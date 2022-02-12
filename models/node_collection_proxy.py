from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitNodeCollection
from jit.interfaces.jit_interface import JitInterface


class NodeCollectionProxy(JitInterface):
    def __init__(self, jitNodeCollection=None, nestNodeCollection=None, virtualIds=None):
        self.jitNodeCollection = jitNodeCollection
        self.nestNodeCollection = nestNodeCollection
        if virtualIds is None:
            virtualIds = []
        self.virtualIds = virtualIds
        self.synapseName = None

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
            names = "Unknown"
            try:
                names = getRes["model"]
            except:
                pass
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
        elif name == "virtualIds":
            self.__dict__["virtualIds"] = value
        elif name =="synapseName":
            self.__dict__["synapseName"] = value
        else:
            raise KeyError(f"{self.__class__.__name__} doesn't have {name} as attribute")

    def getNestIds(self):
        return self.jitNodeCollection.getNestIds()

    def toNodeCollection(self):
        if self.jitNodeCollection:
            nodeCollection = self.jitNodeCollection.createNodeCollection()
            if self.nestNodeCollection is None:
                self.nestNodeCollection = nodeCollection
            else:
                self.nestNodeCollection += nodeCollection
            self.jitNodeCollection = None
        else:
            raise Exception(f"{self.__class__.__name__} has no instance of JitNodeCollection")

    def __setitem__(self, key, value):
        raise TypeError("NodeCollectionProxy object does not support item assignment")

    def __add__(self, other):
        nestNodeCollection = self.nestNodeCollection + other.nestNodeCollection if self.nestNodeCollection else None
        jitNodeCollection = self.jitNodeCollection + other.jitNodeCollection if self.jitNodeCollection else None
        return NodeCollectionProxy(jitNodeCollection=jitNodeCollection, nestNodeCollection=nestNodeCollection)

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

    def __eq__(self, other):
        return self.tolist() == other.tolist()

    def __hash__(self):
        jitHash = 0
        if self.jitNodeCollection:
            jitHash = hash(self.jitNodeCollection)
        nestHash = 0
        if self.nestNodeCollection:
            nestHash = hash(self.nestNodeCollection)
        return jitHash ^ nestHash

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif self.nestNodeCollection:
            return getattr(self.nestNodeCollection, key)
        elif self.jitNodeCollection:
            return getattr(self.jitNodeCollection, key)
        else:
            raise KeyError(f"NodeCollectionProxy doesn't have {key} as attribute")

    def tolist(self):
        ids = []
        for idsRange in self.virtualIds:
            if isinstance(idsRange, range):
                ids.extend(idsRange)
            else:
                ids.append(idsRange)
        return ids

    def __getitem__(self, key):
        newInstance = super().__getitem__(key)
        if hasattr(key, "__iter__"):
            for item in key:
                newInstance.virtualIds.append(self.__getSubIds(item))
        elif isinstance(key, slice):
            items = list(range(key.stop)[key])
            for item in items:
                newInstance.virtualIds.append(self.__getSubIds(item))
        else:
            newInstance.virtualIds.append(self.__getSubIds(key))
        return newInstance

    def __getSubIds(self, key):
        blockStartsAt = 0
        blockEndsAt = -1
        for ids in self.virtualIds:
            blockStartsAt = blockEndsAt + 1
            blockEndsAt = blockStartsAt + len(ids) - 1
            if key >= blockStartsAt and key <= blockEndsAt:
                relativePos = key - blockStartsAt
                return range(ids[relativePos], ids[relativePos] + 1)

        raise IndexError("list out of range")

    def hasJitNodeCollection(self):
        return self.jitNodeCollection is not None

    def set(self, params=None, **kwargs):
        if self.nestNodeCollection and self.jitNodeCollection is None:
            return self.nestNodeCollection.set(params, **kwargs)
        return super().set(params, **kwargs)