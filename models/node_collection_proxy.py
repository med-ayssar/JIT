from jit.models.model_manager import ModelManager
from typing import Any

from jit.models.jit_model import JitNodeCollection


class NodeCollectionProxy():
    def __init__(self, name, libName, node=None):

        properties = {
            # holds the model name to communicate with the ModelManager
            "name": name,
            "libName": libName,
            "node": node,
            # check whether the JitModel instance contains isNodeCollectionalready a nodeCollection instance
            "isNodeCollection": False,
            "createParams": {}
        }

        for k, v in properties.items():
            self.__dict__[k] = v

    def setNodeCollection(self, nodeCollection):
        self.node = nodeCollection
        self.isNodeCollection = True

    def setNodeCollectionProxy(self, proxy):
        self.node = proxy

    def setCreateParams(self, *args, **kwargs):
        if self.isNodeCollection:
            self.createParams["args"] = args
            self.createParams["kwargs"] = kwargs
        else:
            if self.node:
                self.node.setCreateParams(*args, **kwargs)

    def toNodeCollection(self):
        if isinstance(self.node, JitNodeCollection):
            self.__dict__["node"] = self.node.createNodeCollection(self.libName)
            self.setAsNodeCollection()
        else:
            self.__dict__["node"] = self.__create()
            self.setAsNodeCollection()

    def __create(self):
        if bool(self.createParams):
            args = self.createParams["args"]
            kwargs = self.createParams["kwargs"]
            if self.name not in ModelManager.Nest.Models():
                ModelManager.Nest.Install(self.libName)
            nodeCollection = ModelManager.Nest.Create(*args, **kwargs)
            return nodeCollection
        else:
            raise Exception(
                f"The create parameters in {self.__class__.__name__ } must be set before calling nest.Create function")

    def setAsNodeCollection(self):
        self.__dict__["isNodeCollection"] = True

    def __getattr__(self, name):
        if self.isNodeCollection:
            return getattr(self.node, name)
        return self.node[name]

    def __setattr__(self, name, value):
        if self.isNodeCollection:
            setattr(self.node, name, value)
        else:
            self.node[name] = value

    def set(self, params=None, **kwargs):
        if self.isNodeCollection:
            self.node.set(params, **kwargs)

    def get(self, *params, **kwargs):
        return self.node.get(*params, **kwargs)


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
