from jit.utils.nest_config import NestConfig
from multiprocessing import Manager
import sys
import os
from jit.models.model_indexer import ModelIndexer


class ModelManager():
    _Manager = Manager()
    Threads = []
    ThreadsState = _Manager.dict()
    Modules = dict()
    NodeCollectionProxy = []
    JitModels = {}
    ExternalModels = []
    ModelIndexer = {}
    ParsedModels = {}
    Index = 0
    Nest = None

    @staticmethod
    def resetManager():
        ModelManager.ExternalModels = []
        ModelManager.ModelIndexer = {}
        ModelManager.ParsedModels = {}
        ModelManager.NodeCollectionProxy = []
        ModelManager.Index = 0
        libs = ModelManager.JitModels.keys()
        libs = [f"{lib}module.so" for lib in libs]
        workingDir = os.path.join(os.getcwd(), "build")
        for lib in libs:
            path = os.path.join(workingDir, lib)
            if os.path.exists(path):
                os.remove(path)
        ModelManager.JitModels = {}

    @staticmethod
    def add_model(model_name, handle):
        if hasattr(handle, "is_lib") and handle.is_lib:
            ModelManager.populated[model_name] = handle.get_nest_instance()

        ModelManager.to_populate[model_name] = handle

    @staticmethod
    def add_module_to_install(name, addToPathFunc):
        try:
            ModelManager.Modules[name] = addToPathFunc
        except Exception as exp:
            print(exp)
            sys.exit()

    @staticmethod
    def addNestModule(module):
        ModelManager.Nest = module

    @staticmethod
    def getIds(model):
        ids = []
        for ncp in ModelManager.NodeCollectionProxy:
            if ncp.jitNodeCollection:
                for node in ncp.jitNodeCollection.nodes:
                    if node.name == model:
                        ids.extend(node.tolist())
        return ids

    @staticmethod
    def setDefaults(models):
        for model in models:
            jitModel = ModelManager.JitModels[model]
            if jitModel.hasChanged:
                ModelManager.Nest.SetDefaults(model, jitModel.default)

    @staticmethod
    def addJitModel(modelName, n, jitModel):
        ModelManager.JitModels[modelName] = jitModel
        pair = [ModelManager.Index, ModelManager.Index + n]
        ModelManager.Index += n
        if modelName in ModelManager.ModelIndexer:
            ModelManager.ModelIndexer[modelName].addRange(pair)
        else:
            modelIndexer = ModelIndexer(modelName)
            modelIndexer.addRange(pair)
            ModelManager.ModelIndexer[modelName] = modelIndexer
        return pair

    @staticmethod
    def updateJitmodel(modelName, n):
        pair = [ModelManager.Index, ModelManager.Index + n]
        ModelManager.ModelIndexer[modelName].addRange(pair)
        ModelManager.Index += n

    @staticmethod
    def createJitNode(modelName):
        pair = [ModelManager.Index, ModelManager.Index + n - 1]
        ModelManager.ModelIndexer[modelName].addRange(pair)
        ModelManager.Index += n

    @staticmethod
    def updateIndex(modelName, n):
        pair = [ModelManager.Index, ModelManager.Index + n]
        ModelManager.Index += n
        if modelName in ModelManager.ModelIndexer:
            ModelManager.ModelIndexer[modelName].addRange(pair)
        else:
            modelIndexer = ModelIndexer(modelName)
            modelIndexer.addRange(pair)
            ModelManager.ModelIndexer[modelName] = modelIndexer
        return pair

    @staticmethod
    def getRootOf(models):
        roots = set()
        for model in models:
            jitModel = ModelManager.JitModels.get(model, None)
            if jitModel:
                if jitModel.root:
                    roots.add(jitModel.root)
                else:
                    roots.add(jitModel.name)
        return roots

    @staticmethod
    def getNodeCollectionProxyAt(index):
        blockStartsAt = 0
        blockEndsAt = -1
        for node in ModelManager.NodeCollectionProxy:
            blockStartsAt = blockEndsAt + 1
            blockEndsAt = blockStartsAt + len(node) - 1
            if index >= blockStartsAt and index <= blockEndsAt:
                relativeglobalPos = index - blockStartsAt
                return node, relativeglobalPos
        raise IndexError("list out of range")

    @staticmethod
    def getNodeCollectionProxies(ids):
        dictOfModelNames = {}
        # map globalPos to model name
        for i in ids:
            node, relativeglobalPos = ModelManager.getNodeCollectionProxyAt(i)
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

    @staticmethod
    def copyModels(names):
        for modelName in names:
            jitModel = ModelManager.JitModels[modelName]
            if len(jitModel.alias) > 0:
                for alias in jitModel.alias:
                    newModel = ModelManager.JitModels[alias]
                    ModelManager.Nest.CopyModel(jitModel.name, newModel.name, newModel.getValues())
