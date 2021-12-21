from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitNodeCollection
from jit.interfaces.jit_interface import JitInterface


class NodeCollectionProxy(JitInterface):
    def __init__(self, jitNodeCollection=None, nestNodeCollection=None):
        self.jitNodeCollection = jitNodeCollection
        self.nestNodeCollection = nestNodeCollection

    def getChildren(self):
        children = []
        if self.jitNodeCollection:
            children.append(self.jitNodeCollection)
        if self.nestNodeCollection:
            children.append(self.nestNodeCollection)
        return children

    def getNumberOfChildren(self):
        count = 0
        if self.jitNodeCollection:
            count += 1
        if self.nestNodeCollection:
            count += 1
        return count

    def getKeys(self):
        keys = set()
        if self.jitNodeCollection:
            keys.update(self.jitNodeCollection.getKeys())
        if self.nestNodeCollection:
            keys.update(self.nestNodeCollection.get().keys())
        return keys

    def getTuples(self, items):
        tuples = []
        if self.jitNodeCollection:
            tuples.extend(self.jitNodeCollection.getTuples(items))
        if self.nestNodeCollection:
            getRes = self.nestNodeCollection.get(items)
            size = len(self.nestNodeCollection)
            names = set(getRes["model"])
            tuples.append((getRes, size, names))
        return tuples

    def getNodeAndRelativePos(self, globalPos):
        blockStart = 0
        if self.jitNodeCollection:
            if globalPos < len(self.jitNodeCollection):
                return self.jitNodeCollection, globalPos
            else:
                blockStart += len(self.jitNodeCollection)
        if self.nestNodeCollection:
            if globalPos < blockStart + len(self.nestNodeCollection):
                return self.nestNodeCollection, globalPos - blockStart
        raise IndexError("globalPos is not in the range")

    def setNodes(self, nodes):
        if len(nodes) == 1:
            nodes = nodes[0]
            if isinstance(nodes, JitNodeCollection):
                self.jitNodeCollection = nodes
            elif nodes.__class__.__name__ == "NodeCollection":
                self.nestNodeCollection = nodes
        else:
            if len(nodes) != 2:
                raise ValueError("NodeCollectionProxy can only have two Collections, NodeCollection or JitNodeCollection")
            jncPos = 0 if isinstance(nodes[0], JitNodeCollection) else 1
            self.jitNodeCollection = nodes[jncPos]
            self.nestNodeCollection = nodes[1 - jncPos]

    def __setattr__(self, name, value):
        if name == "jitNodeCollection":

            if isinstance(value, JitNodeCollection) or value is None:
                self.__dict__["jitNodeCollection"] = value
            else:
                raise ValueError(f"{self.__class__.__name__}.{name} accepts only a JitNodeCollection instance")
        elif name == "nestNodeCollection":
            if value is None or value.__class__.__name__ == "NodeCollection":
                self.__dict__["nestNodeCollection"] = value
            else:
                raise ValueError(f"{self.__class__.__name__}.{name} accepts only a NodeCollection instance")
        else:
            raise KeyError(f"{self.__class__.__name__} doesn't have {name} as attribute")

    def toNodeCollection(self):
        if self.jitNodeCollection:
            nodeCollection = self.jitNodeCollection.createNodeCollection()
            self.nestNodeCollection += nodeCollection
            self.jitNodeCollection = None
        else:
            raise Exception(f"{self.__class__.__name__} has no instance of JitNodeCollection")

    def __setitem__(self, key, value):
        raise TypeError("NodeCollectionProxy object does not support item assignment")

    def __add__(self, other):
        if self.isNodeCollection:
            return self.node.__add__(other)

    def __len__(self):
        count = 0
        if self.jitNodeCollection:
            count += len(self.jitNodeCollection)
        if self.nestNodeCollection:
            count += len(self.nestNodeCollection)
        return count

    def toString(self):
        instanceToString = ""
        if self.jitNodeCollection:
            instanceToString += str(self.jitNodeCollection)
        if self.nestNodeCollection:
            instanceToString += str(self.nestNodeCollection)

        return f"{self.__class__.__name__}<{instanceToString}>"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()
