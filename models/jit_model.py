import copy
from os import name
from sys import modules
from jit.models.model_manager import ModelManager


class JitModel:
    def __init__(self, name, number, variables, variations=None):
        self.name = name
        self.count = number
        self.paramsAndState = {}
        if bool(variables["State"]):
            self.paramsAndState["State"] = variables["State"]
        if bool(variables["Parameter"]):
            self.paramsAndState["Parameter"] = variables["Parameter"]
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

    def get(self, *params, **kwargs):
        getRes = {}
        states = list(self.paramsAndState["State"].keys())
        params = list(self.paramsAndState["Parameter"].keys())
        allDeclerations = params
        allDeclerations.extend(states)
        if len(params) == 0:
            params = allDeclerations

        for key in params:
            res = self.getTuple(key)
            getRes[key] = res
        return getRes

    def getTuple(self, key):
        arr = []
        for i in range(self.count):
            if str(i) in self.varaitions:
                variationForI = self.varaitions[str(i)]
                value = self.getValue(key, variationForI)
                if value is None:
                    value = self.getValue(key, self.paramsAndState)
                    if value is None:
                        raise KeyError(f"{self.__class__.__name__}.paramsAndState doesn't contain the key {key}")
                    arr.append(value)
            else:
                value = self.getValue(key, self.paramsAndState)
                if value is None:
                    raise KeyError(f"{self.__class__.__name__}.paramsAndState doesn't contain the key {key}")
                arr.append(value)
        return tuple(arr)

    def getValue(self, key, stateParamDict):
        if "State" in stateParamDict:
            if key in stateParamDict["State"]:
                return stateParamDict["State"][key]

        if "Parameter" in stateParamDict:
            if key in stateParamDict["Parameter"]:
                return stateParamDict["Parameter"][key]
        return None


class JitNodeCollection:
    def __init__(self, name, first=0, last=1):
        self.name = name
        self.first = first
        self.last = last
        self.step = 1

    def __len__(self):
        return self.last - self.first

    def __iter__(self):
        return JitNodeCollectionIterator(self)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < self.first and key > self.last - 1:
                raise IndexError("index out of range")
            return JitNodeCollection(name=self.name, first=key, last=key + 1)
        elif isinstance(key, slice):
            if key.start is None:
                start = 0
            else:
                start = key.start
                if abs(start) > self.__len__():
                    raise IndexError('slice start value outside of the NodeCollection')
            if key.stop is None:
                stop = self.__len__()
            else:
                stop = key.stop
                if abs(stop) > self.__len__():
                    raise IndexError('slice stop value outside of the JitNodeCollection')
            step = 1 if key.step is None else key.step
            if step < 1:
                raise IndexError('slicing step for JitNodeCollection must be strictly positive')
            slicedElement = JitNodeCollection(name=self.name, first=start, last=stop)
            slicedElement.step = step
            return slicedElement

    def __setitem__(self, key, value):
        raise TypeError("JitNodeCollection object does not support item assignment")

    def toString(self):
        return f"{self.__class__.__name__}(name={self.name}, size={self.last - self.first}, first={self.first})"

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
        jitModel = ModelManager.JitModels[self.name]
        return jitModel.get(*args, **kwargs)


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
