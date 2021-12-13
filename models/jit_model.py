import copy
from multiprocessing.managers import Namespace
from os import name
from sys import modules

from numpy.core.fromnumeric import var
from jit.models.model_manager import ModelManager
from collections import defaultdict
import numpy as np


class JitModel:
    def __init__(self, name, number, variables, variations=None):
        self.name = name
        self.count = number
        self.default = variables
        self.varaitions = {}
        self.nest = None
        self.createParams = {}

    def __len__(self):
        return self.count

    def addNestModule(self, module):
        self.nest = module

    def create(self):
        if self.nest:
            if self.name not in self.nest.Models():
                self.nest.Install(self.libName)
            self.toNodeCollection()
            return True
        return False

    def setCreateParams(self, *args, **kwargs):
        self.createParams["args"] = args
        self.createParams["kwargs"] = kwargs

    def createNodeCollection(self, moduleName):
        if self.nest:
            if bool(self.createParams):
                args = self.createParams["args"]
                kwargs = self.createParams["kwargs"]
                self.nest.Install(moduleName)
                nodeCollection = self.nest.Create(*args, **kwargs)
                return nodeCollection
            else:
                raise Exception(
                    f"The create parameters in {self.__class__.__name__ } must be set before calling nest.Create function")
        else:
            raise Exception(
                f"The create parameters in {self.__class__.__name__ }.nest is NoneType")

    def get(self, ids, items):
        res = {}
        keys = self.default.keys()
        # select only valid items
        items = list(filter(lambda x: x in keys, items))
        for k in items:
            valuesOfK = []
            for i in ids:
                if i in self.varaitions and k in self.varaitions[i]:
                    valuesOfK.append(self.varaitions[i][k])
                else:
                    valuesOfK.append(self.default[k])
            res[k] = valuesOfK
        return res

    def getKeys(self):
        return list(self.default.keys())

    def toString(self):
        return f"{self.__class__.__name__}(name={self.name})"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()


class JitNode():
    def __init__(self, name="None", first=0, last=0):
        self.name = name
        self.first = first
        self.last = last

    def __len__(self):
        return self.last - self.first

    def toString(self):
        return f"model={self.name}, size={self.last - self.first}, first={self.first}"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def __contains__(self, obj):
        if isinstance(obj, int):
            if obj < self.first and obj >= self.last:
                return False
            return True
        raise NotImplemented("Todo handle other cases in JitNode.__contains__")

    def __eq__(self, other):
        if other is not None:
            if other.name == self.name and self.first == other.first and self.last == other.last:
                return True
        return False

    def __hash__(self):
        return hash(self.name)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key >= self.__len__():
                raise IndexError("index out of range")
            return self.__getNodesAt([key])
        elif isinstance(key, slice):
            if key.start is None:
                start = 0
            else:
                start = key.start
                if abs(start) > self.__len__():
                    raise IndexError('slice start value outside of the JitNode')
            if key.stop is None:
                stop = self.__len__()
            else:
                stop = key.stop
                if abs(stop) > self.__len__():
                    raise IndexError('slice stop value outside of the JitNode')
            step = 1 if key.step is None else key.step
            if step < 1:
                raise IndexError('slicing step for JitNode must be strictly positive')
            nodesRange = list(range(start, stop, step))
            slicedElement = self.__getNodesAt(nodesRange)
            return slicedElement
        elif isinstance(key, (list, tuple)):
            if len(key) == 0:
                return JitNode()
            # Must check if elements are bool first, because bool inherits from int
            if all(isinstance(x, bool) for x in key):
                if len(key) != len(self):
                    raise IndexError('Bool index array must be the same length as JitNode')
                npKey = np.array(key, dtype=np.bool)
                npKey = np.argwhere(npKey == True)
            # Checking that elements are not instances of bool too, because bool inherits from int
            elif all(isinstance(x, int) and not isinstance(x, bool) for x in key):
                npKey = np.array(key, dtype=np.uint64)
                if len(np.unique(npKey)) != len(npKey):
                    raise ValueError('All node IDs in a JitNode have to be unique')
            else:
                raise TypeError('Indices must be integers or bools')
            return self.__getNodesAt(npKey)

    def __getNodesAt(self, items):
        if all(index < self.__len__() for index in items):
            groups = self.__groupByDistance(items)
            nodes = list()
            for group in groups:
                newNode = JitNode(name=self.name, first=group[0], last=group[1])
                nodes.append(newNode)
            return nodes

    def __groupByDistance(self, items):
        res = []
        if len(items) == 1:
            return [(items[0], items[0] + 1)]
        else:
            first = items[0]
            last = first
            for i in range(1, len(items)):
                if items[i] - last == 1:
                    last = items[i]
                else:
                    res.append((first, last + 1))
                    first = items[i]
                    last = items[i]
            res.append((first, last + 1))
        return res

    def get(self, keys):
        modelsToSelect = range(self.first, self.last)
        jitModel = ModelManager.JitModels[self.name]
        dictOfItems = jitModel.get(ids=modelsToSelect, items=keys)
        return dictOfItems

    def getKeys(self):
        jitModel = ModelManager.JitModels[self.name]
        return jitModel.getKeys()


class JitNodeCollection:
    def __init__(self, nodes):
        if isinstance(nodes, (list, tuple)):
            if len(nodes) > 0:
                if isinstance(nodes[0], int):
                    pass
                elif isinstance(nodes[0], JitNode):
                    self.nodes = nodes
                else:
                    raise TypeError(f"{self.__class__.__name__} accepts only list of int or JitNode")
        elif isinstance(nodes, JitNode):
            self.nodes = [nodes]
        else:
            raise TypeError(f"{self.__class__.__name__} accepts only list of int or JitNode")

    def __len__(self):
        return sum([len(node) for node in self.nodes])

    def __iter__(self):
        return JitNodeCollectionIterator(self)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0 and key > self.__len__():
                raise IndexError("index out of range")
            return JitNodeCollection(self.__indexing(key))
        elif isinstance(key, slice):
            if key.start is None:
                start = 0
            else:
                start = key.start
                if abs(start) > self.__len__():
                    raise IndexError('slice start value outside of the JitNodeCollection')
            if key.stop is None:
                stop = self.__len__()
            else:
                stop = key.stop
                if abs(stop) > self.__len__():
                    raise IndexError('slice stop value outside of the JitNodeCollection')
            step = 1 if key.step is None else key.step
            if step < 1:
                raise IndexError('slicing step for JitNodeCollection must be strictly positive')
            ranges = list(range(start, stop, step))
            newNodes = self.__slicing(ranges)
            slicedElement = JitNodeCollection(newNodes)
            return slicedElement
        elif isinstance(key, (list, tuple)):
            newNodes = newNodes = self.__slicing(key)
            return JitNodeCollection(newNodes)
        else:
            raise Exception("Only list, tuple and int are accepted")

    def __indexing(self, index):
        blockStartsAt = 0
        blockEndsAt = -1
        for node in self.nodes:
            blockStartsAt = blockEndsAt + 1
            blockEndsAt = blockStartsAt + len(node) - 1
            if index >= blockStartsAt and index <= blockEndsAt:
                relativeIndex = index - blockStartsAt
                return node[relativeIndex]
        raise IndexError("list out of range")

    def __slicing(self, items):
        dictOfModelNames = {}
        # map index to model name
        for i in items:
            node, relativeIndex = self.resolveModelAt(i)
            dictOfModelNames[i] = (node, relativeIndex)

        # group dict by model name
        groups = defaultdict()
        for key, value in sorted(dictOfModelNames.items()):
            if value[0] in groups:
                groups[value[0]].append(value[1])
            else:
                groups[value[0]] = [value[1]]

        # execute each split on each node
        nodes = list()
        for key, value in groups.items():
            newNodes = key[value]
            nodes.extend(newNodes)
        return nodes

    def resolveModelAt(self, index):
        blockStartsAt = 0
        blockEndsAt = -1
        for node in self.nodes:
            blockStartsAt = blockEndsAt + 1
            blockEndsAt = blockStartsAt + len(node) - 1
            if index >= blockStartsAt and index <= blockEndsAt:
                relativeIndex = index - blockStartsAt
                return node, relativeIndex
        raise IndexError("list out of range")

    def __setitem__(self, key, value):
        raise TypeError("JitNodeCollection object does not support item assignment")

    def toString(self):
        classNameLength = len(self.__class__.__name__) + 1
        spaces = " " * classNameLength
        instanceToString = f"{self.__class__.__name__}("
        for index, node in enumerate(self.nodes):
            newLineOrClose = ")" if index == len(self.nodes) - 1 else "\n"
            padding = spaces if index > 0 else ""
            instanceToString += f"{padding}{str(node)}{newLineOrClose}"
        return instanceToString

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def createNodeCollection(self, moduleName):
        jitModel = ModelManager.JitModels[self.name]
        nodeCollection = jitModel.createNodeCollection(moduleName)
        return nodeCollection

    def setCreateParams(self, *args, **kwargs):
        jitModel = ModelManager.JitModels[self.name]
        jitModel.setCreateParams(*args, **kwargs)

    def get(self, *args, **kwargs):
        # TODO implement return style using(kwargs)
        # get all Keys from all nodes
        allKeys = set()
        for node in self.nodes:
            allKeys.update(node.getKeys())
        if len(args) == 0:
            args = allKeys
        
        tuples  = [(node.get(args), len(node), node.name) for node in self.nodes]
        toMerge = {}
        for item in args:
            subRes = []
            for subDict in tuples:
                if item in subDict[0]:
                    subRes.extend(subDict[0][item])
                else:
                    notFound = [None] * subDict[1]
                    subRes.extend(notFound)
            toMerge[item] = subRes
        models =  []
        for subDict in tuples:
            models.extend([subDict[2]] * subDict[1])
        
        toMerge["models"] = models

        return toMerge


        


class JitNodeCollectionIterator:
    def __init__(self, jnc):
        self.jnc = jnc
        self._count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._count > len(self.jnc) - 1:
            raise StopIteration

        nestElement = JitNodeCollection(self.jnc.name, first=self._count, last=self._count + 1)
        self._count += 1
        return nestElement
