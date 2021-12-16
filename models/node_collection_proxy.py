from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitNodeCollection


class NodeCollectionProxy():
    def __init__(self, name, libName, node=None):
        self.jitNodeCollection = None
        self.nestNodeCollection = None
        self.createParams = {}



    def toNodeCollection(self):
        if self.jitNodeCollection:
            nodeCollection = self.node.createNodeCollection(self.libName)
            self.nestNodeCollection+= nodeCollection
            self.jitNodeCollection = None
        else:
            raise Exception(f"{self.__class__.__name__} has no instance of JitNodeCollection")

    def set(self, params=None, **kwargs):
        if kwargs and params:
            raise TypeError("must either provide params or kwargs, but not both.")
        elif kwargs:
            pass

        else:
            if isinstance(params, dict):
               pass
            elif isinstance(params, list):
                if len(params) == 0:
                    return
                types = set([type(item) for item in params])
                if len(types) != 1 and types.pop().__class__.__name__ != "dict":
                    raise TypeError("params can only contain a dictionary or list of dictionaries")
                if len(params) != len(self):
                    raise ValueError(
                        f"params is a list of dict and has {len(params)} items, but expected are {len(self)}")
                

    def get(self, *params, **kwargs):
        nodeCollectionOutput = self.nestNodeCollection.get(*params, **kwargs)
        if self.jitNodeCollection is None:
            return nodeCollectionOutput
        else:
            jitNodeCollectionOutput = self.jitNodeCollection.get(*params, **kwargs)
            return {"JitNodeCollection": jitNodeCollectionOutput, "NestNodeCollection" : nodeCollectionOutput}
                    


    def __iter__(self):
        return self.node.__iter__()

    def __getitem__(self, key):
        node = self.node[key]
        return NodeCollectionProxy(name=self.name, libName=self.libName, node=node)

    def __setitem__(self, key, value):
        raise TypeError("NodeCollectionProxy object does not support item assignment")

    def __add__(self, other):
        if self.isNodeCollection:
            return self.node.__add__(other)

    def addModelDeclaredVariables(self, variables):
        if not self.isNodeCollection:
            self.node = variables

    def __len__(self):
        return len(self.node)

    def addJitNodeCollection(self, jitNodeCollection):
        if isinstance(jitNodeCollection, JitNodeCollection):
            self.__dict__["node"] = jitNodeCollection
        else:
            raise TypeError(f"the passed arugement must be of type JitNodeCollection")

    def toString(self):
        return f"{self.__class__.__name__}<{str(self.node)}>"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()


class NodeCollectionProxyIterator:
    def __init__(self, ncp):
        self.ncp = ncp
        self._count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._count > len(self.ncp) - 1:
            raise StopIteration
        node = self.ncp.node[self._count]
        nextElement = NodeCollectionProxy(name=self.ncp.name, libName=self.ncp.libName, node=node)
        self._count += 1
        return nextElement
