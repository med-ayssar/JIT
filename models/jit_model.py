import copy
from email.policy import default
from jit.interfaces.jit_interface import JitInterface
from jit.models.model_manager import ModelManager
from collections import defaultdict
import numpy as np
import copy


class JitModel:
    def __init__(self, name, modelChecker=None, astModel=None, mtype="neuron"):
        self.name = name
        self.modelchecker = modelChecker
        self.default = self.extractDefaults()
        self.createParams = {}
        self.attributes = {}
        self.alias = []
        self.hasChanged = False
        self.root = None
        self.type = mtype
        self.astModel = astModel
        self.stateKeys = ["synapse_model"] if mtype == "synapse" else []
        self.isExternal = True

    def setStates(self, keys):
        if isinstance(keys, list):
            self.stateKeys.extend(keys)
        elif isinstance(keys, str):
            self.stateKeys.append(keys)
        else:
            raise TypeError("keys must either list or str")

    def isFromNestml(self):
        return self.modelchecker != None

    def getValues(self):
        import copy
        values = copy.deepcopy(self.default)
        for state in self.stateKeys:
            values.pop(state, None)
        return values

    def addNestIds(self, x, y):
        indexer = ModelManager.ModelIndexer[self.name]
        indexer.addNestIds(x=x, y=y)

    def setDefaults(self, dicOfParams):
        keysToChange = dicOfParams.keys()
        modelsIds = ModelManager.getIds(self.name)
        for key in keysToChange:
            ignoredModels = set()
            if key in self.attributes:
                attribute = self.attributes[key]
                ignoredModels = attribute.modelIds
            modelsToUpdate = list(set(modelsIds).difference(ignoredModels))
            self.set(modelsToUpdate, {key: self.default[key]})

        self.default.update(dicOfParams)
        self.hasChanged = True

    def create(self):
        if ModelManager.Nest:
            if self.name not in ModelManager.Nest.Models():
                ModelManager.Nest.Install(self.libName)
            self.toNodeCollection()
            return True
        return False

    def setCreateParams(self, *args, **kwargs):
        self.createParams["args"] = args
        self.createParams["kwargs"] = kwargs

    def createNodeCollection(self, params):
        if ModelManager.Nest:
            if bool(self.createParams):
                args = self.createParams["args"]
                kwargs = self.createParams["kwargs"]
                kwargs.update(params)
                params = kwargs.pop('params', None)
                nodeCollection = ModelManager.Nest.Create(*args, **kwargs)
                nodeCollection.set(params)
                return nodeCollection
            else:
                raise Exception(
                    f"The create parameters in {self.__class__.__name__ } must be set before calling nest.Create function")
        else:
            raise Exception(
                f"The create parameters in {self.__class__.__name__ }.nest is NoneType")

    def get(self, ids, items, onlyChanged=False):
        res = {}
        keys = self.default.keys()
        # select only valid items
        items = list(filter(lambda x: x in keys, items))
        for k in items:
            valuesOfK = []
            for i in ids:
                if k in self.attributes:
                    attribute = self.attributes[k]
                    if i in attribute:
                        value = attribute.getValueOfId(i)
                        valuesOfK.append(value)
                    else:
                        if not onlyChanged:
                            valuesOfK.append(self.default[k])
                else:
                    if not onlyChanged:
                        valuesOfK.append(self.default[k])
            if len(valuesOfK) == 0:
                pass
            elif len(valuesOfK) == 1:
                res[k] = valuesOfK[0]
            else:
                res[k] = valuesOfK
        return res

    def set(self, ids, collection):
        for k, v in collection.items():
            if isinstance(v, (tuple, list)):
                if len(v) != len(ids) and len(v) > 0 and isinstance(v[0], (list, tuple)):
                    raise TypeError(f"Expecting {len(ids)} values in {k}, but got {len(v)}")
                if k in self.attributes:
                    self.attributes[k].update(ids, v)
                else:
                    newAttribute = JitAtribute(attributeName=k, ids=ids, values=v)
                    self.attributes[k] = newAttribute
            else:
                values = [v] * len(ids)
                if k in self.attributes:
                    self.attributes[k].update(ids, values)
                else:
                    newAttribute = JitAtribute(attributeName=k, ids=ids, values=values)
                    self.attributes[k] = newAttribute

    def getKeys(self):
        return list(self.default.keys())

    def extractDefaults(self):
        if self.modelchecker:
            modelVariables = self.modelchecker.declaredVarialbes
            defaults = {}
            for var in modelVariables:
                funcName = f"get_{var}"
                value = getattr(self.modelchecker, funcName)()
                if value.__class__.__name__ == "string":
                    value = str(value)
                if "vector" in value.__class__.__name__:
                    value = [v for v in value]
                defaults[var] = value
            return defaults
        return {}

    def toString(self):
        return f"{self.__class__.__name__}(name={self.name})"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()


class JitNode:
    def __init__(self, name="None", first=0, last=0):
        self.name = name
        self.first = first
        self.last = last
        self.isDefault = True

    def __len__(self):
        return self.last - self.first

    def hasChanged(self):
        return not self.isDefault

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
        return hash(f"{self.name}{self.first}{self.last}")

    def __getitem__(self, key):
        if isinstance(key, int):
            if key >= self.__len__():
                raise IndexError("globalPos out of range")
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
                    raise IndexError('Bool globalPos array must be the same length as JitNode')
                npKey = np.array(key, dtype=np.bool)
                npKey = np.argwhere(npKey == True)
            # Checking that elements are not instances of bool too, because bool inherits from int
            elif all(isinstance(x, int) and not isinstance(x, bool) for x in key):
                npKey = np.array(key, dtype=np.uint64)
                if len(np.unique(npKey)) != len(npKey):
                    raise ValueError('All node IDs in a JitNode have to be unique')
            else:
                raise TypeError('Indices must be integers or bools')
            # TODO convert all int to np.uint64
            return self.__getNodesAt(key)

    def __getNodesAt(self, items):
        if all(globalPos < self.__len__() for globalPos in items):
            groups = self.__groupByDistance(items)
            nodes = list()
            for group in groups:
                first = self.first + group[0]
                last = first + group[1] - group[0]
                newNode = JitNode(name=self.name, first=first, last=last)
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

    def get(self, keys, onlyChanged=False):
        modelsToSelect = range(self.first, self.last)
        jitModel = ModelManager.JitModels[self.name]
        dictOfItems = jitModel.get(ids=modelsToSelect, items=keys, onlyChanged=onlyChanged)
        return dictOfItems

    def getPosition(self):
        jitModel = ModelManager.JitModels[self.name]
        return jitModel.position

    def set(self, collection, ids=None):
        if ids is None:
            ids = range(self.first, self.last)
        jitModel = ModelManager.JitModels[self.name]
        jitModel.set(ids=ids, collection=collection)
        self.isDefault = False

    def getKeys(self):
        jitModel = ModelManager.JitModels[self.name]
        return jitModel.getKeys()

    def tolist(self):
        return list(range(self.first, self.last))

    def addNestIds(self, ids):
        if len(self) == (ids[1] - ids[0] + 1):
            jitModel = ModelManager.JitModels[self.name]
            jitModel.addNestIds(x=[self.first, self.last], y=ids)

    def getNestIds(self):
        indexer = ModelManager.ModelIndexer[self.name]
        return indexer.getNestIdsAt([self.first, self.last])

    def createNodeCollection(self, params):
        jitModel = ModelManager.JitModels[self.name]
        return jitModel.createNodeCollection(params)


class JitNodeCollection(JitInterface):
    def __init__(self, nodes=None, isNotInitial=True):
        if nodes is None:
            self.nodes = list()
        elif isinstance(nodes, (list, tuple)):
            if len(nodes) > 0:
                if isinstance(nodes[0], int):
                    pass
                elif isinstance(nodes[0], JitNode):
                    self.nodes = nodes
                else:
                    raise TypeError(f"{self.__class__.__name__} accepts only list of int or JitNode")
            else:
                self.nodes = nodes
        elif isinstance(nodes, JitNode):
            self.nodes = [nodes]
        else:
            raise TypeError(f"{self.__class__.__name__} accepts only list of int or JitNode")

        self.isNotInitial = isNotInitial
        self.spatial = None
        self.changed = False

    def __len__(self):
        if self.nodes:
            return sum([len(node) for node in self.nodes])
        return 0

    def setNodes(self, nodes):
        if isinstance(nodes, list):
            self.nodes = nodes
        elif isinstance(nodes, JitNode):
            self.nodes = [nodes]
        else:
            raise TypeError(f"{self.__class__.__name__} accepts only list or single of a JitNode instancess")

    def getNodeAndRelativePos(self, globalPos):
        blockStartsAt = 0
        blockEndsAt = -1
        for node in self.nodes:
            blockStartsAt = blockEndsAt + 1
            blockEndsAt = blockStartsAt + len(node) - 1
            if globalPos >= blockStartsAt and globalPos <= blockEndsAt:
                relativeglobalPos = globalPos - blockStartsAt
                return node, relativeglobalPos
        raise IndexError("list out of range")

    def __setitem__(self, key, value):
        raise TypeError("JitNodeCollection object does not support item assignment")

    def toString(self):
        classNameLength = len(self.__class__.__name__) + len("NodeCollectionProxy") + 2
        spaces = " " * classNameLength
        instanceToString = f"{self.__class__.__name__}("
        if len(self.nodes) > 0:
            for globalPos, node in enumerate(self.nodes):
                newLineOrClose = ")" if globalPos == len(self.nodes) - 1 else "\n"
                padding = spaces if globalPos > 0 else ""
                instanceToString += f"{padding}{str(node)}{newLineOrClose}"
        else:
            instanceToString += "Empty)"
        return instanceToString

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def __add__(self, other):
        mynodes = copy.deepcopy(self.nodes)
        otherNodes = copy.deepcopy(copy.nodes)
        mynodes.extend(otherNodes)
        return JitNodeCollection(nodes=mynodes)

    def getNestIds(self):
        ids = []
        for node in self.nodes:
            ids.extend(node.getNestIds())
        return ids

    def createNodeCollection(self):
        # This  JitCollection must contain the original created models before indexing or slicing
        if not self.isNotInitial:
            jitNode = self.nodes[0]
            keys = self.getKeys()
            params = jitNode.get(keys=keys, onlyChanged=True)
            nodeCollection = jitNode.createNodeCollection({"params": params})
            ids = nodeCollection.tolist()
            idsInterval = [ids[0], ids[-1]]
            jitNode.addNestIds(idsInterval)
            self.isNotInitial = True
            return nodeCollection
        raise Exception("Only initial JitNodeCollection can be converted to NodeCollection")

    def setCreateParams(self, *args, **kwargs):
        pass

    def hasChanged(self):
        return self.hasChanged

    def getChildren(self):
        return self.nodes

    def getNumberOfChildren(self):
        return len(self.nodes)

    def getKeys(self):
        res = list()
        for node in self.nodes:
            res.extend(node.getKeys())
        return set(res)

    def getTuples(self, items):
        return [(node.get(items), len(node), node.name) for node in self.nodes]

    def tolist(self):
        allIds = []
        for node in self.nodes:
            allIds.extend(node.tolist())
        return allIds

    def setSpatial(self, positions):
        self.spatial = vars(positions)


class JitAtribute:
    def __init__(self, attributeName, ids, values):
        self.values = []
        self.attributeName = attributeName
        if len(ids) != len(values) and len(ids) != 1:
            raise ValueError(f"ids:{len(ids)} != values: {len(values)}: both ids and values must be of the same size")

        if isinstance(ids, range):
            self.modelIds = list(ids)
        elif isinstance(ids, (list, set)):
            self.modelIds = ids
        else:
            raise TypeError(
                f"{self.__class__.__name__} accepts only range or list types for ids, but ids have type of{ids.__class__.__name__}")
        if (len(ids)) < len(values) and len(ids) == 1:
            self.values.append(values)
        else:
            self.values.extend(values)

    def __contains__(self, other):
        if isinstance(other, str):
            return self.attributeName == other
        if isinstance(other, int):
            return other in self.modelIds
        return False

    def getValueOfId(self, modeId):
        if modeId in self:
            index = self.modelIds.index(modeId)
            value = self.values[index]
            if value.__class__.__name__ == "Parameter":
                value = value.GetValue()
                self.values[index] = value
            return value
        raise ValueError(f"the model id {modeId} is not in {str(self)}")

    def toString(self):
        return f"{self.__class__.__name__}(attribute={self.attributeName})"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def update(self, ids, values):
        if len(ids) != len(values):
            raise ValueError(f"ids:{len(ids)} != values: {len(values)}: both ids and values must be of the same size")

        for pos, localId in enumerate(ids):
            if localId in self:
                index = self.modelIds.index(localId)
                self.values[index] = values[pos]
            else:
                self.modelIds.append(localId)
                self.values.append(values[pos])
