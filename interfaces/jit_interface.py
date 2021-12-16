class JitMeta(type):
    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass):
        #functions = ["getChildren", "getNumberOfChildren"]
        return (hasattr(subclass, 'getChildren') and
                callable(subclass.getChildren) and
                hasattr(subclass, 'getNumberOfChildren') and
                callable(subclass.getNumberOfChildren))


class JitInterface(metaclass=JitMeta):

    def getChildren(self):
        pass

    def getNumberOfChildren(self):
        pass

    def getKeys(self):
        pass

    def getTuples(self, items):
        pass

    def getNodeAndRelativePos(self, golbalPos):
        pass

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
                for i in range(len(self.nodes)):
                    listOfDict[i][k] = v
        return listOfDict

    def get(self, *args, **kwargs):
        allKeys = self.getKeys()
        if len(args) == 0:
            args = allKeys

        tuples = self.getTuples(args)
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
        models = []
        for subDict in tuples:
            if isinstance(subDict[2], (tuple, list)):
                models.extend(subDict[2])
            else:
                models.extend([subDict[2]] * subDict[1])

        toMerge["models"] = models

        return toMerge


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
        nextElement = self.node.__class__(node[relativeglobalPos])
        self._count += 1
        return nextElement
