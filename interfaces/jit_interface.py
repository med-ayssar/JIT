from jit.utils.help import whichFunc
import nest
# class JitMeta(type):
#     def __instancecheck__(cls, instance):
#         return cls.__subclasscheck__(type(instance))

#     def __subclasscheck__(cls, subclass):
#         #functions = ["getChildren", "getNumberOfChildren"]
#         return (hasattr(subclass, 'getChildren') and
#                 callable(subclass.getChildren) and
#                 hasattr(subclass, 'getNumberOfChildren') and
#                 callable(subclass.getNumberOfChildren))


class JitInterface():

    def getChildren(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} inherits from JitInterface and must implemenet {whichFunc()}")

    def getNumberOfChildren(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} inherits from JitInterface and must implemenet {whichFunc()}")

    def getKeys(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} inherits from JitInterface and must implemenet {whichFunc()}")

    def getTuples(self, items):
        raise NotImplementedError(
            f"{self.__class__.__name__} inherits from JitInterface and must implemenet {whichFunc()}")

    def getNodeAndRelativePos(self, golbalPos):
        raise NotImplementedError(
            f"{self.__class__.__name__} inherits from JitInterface and must implemenet {whichFunc()}")

    def setNodes(self, nodes):
        raise NotImplementedError(
            f"{self.__class__.__name__} inherits from JitInterface and must implemenet {whichFunc()}")

    def __iter__(self):
        return JitIterator(self)

    def projectDict(self, dic):
        listOfDict = [dict() for i in range(self.getNumberOfChildren())]
        for k, v in dic.items():
            if isinstance(v, (list, tuple)):
                current = 0
                currentLength = 0
                for index, node in enumerate(self.getChildren()):
                    currentLength += len(node)
                    listOfDict[index][k] = v[current: currentLength]
                    current += len(node)
            else:
                for i in range(self.getNumberOfChildren()):
                    listOfDict[i][k] = v
        return listOfDict

    def get(self, *args, **kwargs):
        allKeys = self.getKeys()
        hasModels = False
        if len(args) == 0:
            args = allKeys
            hasModels = True

        tuples = self.getTuples(args)
        toMerge = {}
        for item in args:
            subRes = []
            for subDict in tuples:
                if item in subDict[0]:
                    value = subDict[0][item]
                    if isinstance(value, (tuple, list)):
                        subRes.extend(value)
                    else:
                        values = [value] * subDict[1]
                        subRes.extend(values)
                    
                else:
                    notFound = [None] * subDict[1]
                    subRes.extend(notFound)
            if len(subRes) > 1 :
                toMerge[item] = subRes
            else:
                toMerge[item] = subRes[0]
        if hasModels:
            models = []
            for subDict in tuples:
                if isinstance(subDict[2], (tuple, list)):
                    models.extend(subDict[2])
                else:
                    models.extend([subDict[2]] * subDict[1])

            toMerge["models"] = models
        if len(toMerge.keys()) == 1:
            values = toMerge[list(toMerge.keys())[0]]
            if len(values) == 1:
                return values[0]
        if len(args) == 1:
            return toMerge[args[0]]
        return toMerge

    def set(self, params=None, **kwargs):
        if kwargs and params:
            raise TypeError("must either provide params or kwargs, but not both.")
        elif kwargs:
            splitCollection = self.projectDict(kwargs)
            for globalPos, node in enumerate(self.getChildren()):
                node.set(splitCollection[globalPos])

        else:
            if isinstance(params, dict):
                collection = splitCollection = self.projectDict(params)
                for globalPos, node in enumerate(self.getChildren()):
                    node.set(collection[globalPos])
            elif isinstance(params, list):
                if len(params) == 0:
                    return
                types = set([type(item) for item in params])
                if len(types) != 1 and types.pop().__class__.__name__ != "dict":
                    raise TypeError("params can only contain a dictionary or list of dictionaries")
                if len(params) != len(self):
                    raise ValueError(
                        f"params is a list of dict and has {len(params)} items, but expected are {len(self)}")

                currentNode = 0
                nodes = self.getChildren()
                partialLength = len(nodes[currentNode])
                for globalPos, dic in enumerate(params):
                    if globalPos < partialLength:
                        self.nodes[currentNode].set(ids=[globalPos], collection=dic)
                    else:
                        currentNode += 1
                        self.nodes[currentNode].set(ids=[globalPos], collection=dic)
                        partialLength += len(nodes[currentNode])

    def nodeAt(self, globalPos):
        blockStartsAt = 0
        blockEndsAt = -1
        for node in self.getChildren():
            blockStartsAt = blockEndsAt + 1
            blockEndsAt = blockStartsAt + len(node) - 1
            if globalPos >= blockStartsAt and globalPos <= blockEndsAt:
                relativeglobalPos = globalPos - blockStartsAt
                return node[relativeglobalPos]
        raise IndexError("list out of range")

    def nodesAt(self, items):
        dictOfModelNames = {}
        # map globalPos to model name
        for i in items:
            node, relativeglobalPos = self.getNodeAndRelativePos(i)
            dictOfModelNames[i] = (node, relativeglobalPos)

        # group dict by model name
        groups = dict()
        for key, value in sorted(dictOfModelNames.items()):
            if value[0] in groups:
                groups[value[0]].append(value[1])
            else:
                groups[value[0]] = [value[1]]

        # execute each split on each node
        nodes = list()
        for key, value in groups.items():
            newNodes = key[value]
            if isinstance(newNodes, list):
                nodes.extend(newNodes)
            else:
                nodes.append(newNodes)
        return nodes

    def __getitem__(self, key):
        if isinstance(key, int):
            if abs(key) >= self.__len__():
                raise IndexError("globalPos out of range")
            actualKey = key if key >= 0 else self.__len__() - abs(key)
            newInstance = self.__class__()
            newInstance.setNodes(self.nodeAt(actualKey))
            return newInstance
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
                if key.stop < 0 and abs(key.stop) < self.__len__():
                    stop = self.__len__() - abs(key.stop)
                else:
                    stop = key.stop
                    if abs(stop) >= self.__len__():
                        raise IndexError("slice stop value outside of the JitNodeCollection")
            step = 1 if key.step is None else key.step
            if step < 1:
                raise IndexError('slicing step for JitNodeCollection must be strictly positive')
            ranges = list(range(start, stop, step))
            newNodes = self.nodesAt(ranges)
            newInstance = self.__class__()
            newInstance.setNodes(newNodes)
            return newInstance
        elif isinstance(key, (list, tuple)):
            newNodes = newNodes = self.nodesAt(key)
            newInstance = self.__class__()
            newInstance.setNodes(newNodes)
            return newInstance
        else:
            raise Exception("Only list, tuple and int are accepted")


class JitIterator:
    def __init__(self, node):
        self.node = node
        self._count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._count > len(self.node) - 1:
            raise StopIteration

        node, relativeglobalPos = self.node.getNodeAndRelativePos(self._count)
        nextElement = self.node.__class__()
        nextElement.setNodes(node[relativeglobalPos])
        self._count += 1
        return nextElement
