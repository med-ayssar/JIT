from jit.utils.nest_config import NestConfig
from multiprocessing import Manager
import sys
import os
from jit.models.model_indexer import ModelIndexer


class ModelManager():
    """Manage the inner state of the created Objects during the simulation."""

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
        """ Reset and clear all created objects.

        """
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

    # @staticmethod
    # def add_model(model_name, handle):
    #     """ Extend the range of Ids covered by the model

    #         Parameters
    #         ----------
    #         newRange: list[int], range
    #             list of new Ids covered by the model
    #     """
    #     if hasattr(handle, "is_lib") and handle.is_lib:
    #         ModelManager.populated[model_name] = handle.get_nest_instance()

    #     ModelManager.to_populate[model_name] = handle

    @staticmethod
    def add_module_to_install(name, addToPathFunc):
        """ Append the path of the module libaray.

            Parameters
            ----------
            addToPathFunc: str
                library path.
        """
        try:
            ModelManager.Modules[name] = addToPathFunc
        except Exception as exp:
            print(exp)
            sys.exit()

    @staticmethod
    def addNestModule(module):
        """ Add the NEST module.
            Parameters
            ----------
            module: Module
                the NEST module
        """
        ModelManager.Nest = module

    @staticmethod
    def getIds(model):
        """ Retrieve the stored IDs of the model.

            Parameters
            ----------
            model: str
                the model's name.

            Returns
            -------
            list[int]:
                the JIT generated IDs of the model.

        """
        ids = []
        for ncp in ModelManager.NodeCollectionProxy:
            if ncp.jitNodeCollection:
                for node in ncp.jitNodeCollection.nodes:
                    if node.name == model:
                        ids.extend(node.tolist())
        return ids

    @staticmethod
    def setDefaults(models):
        """ Update the defaults of the model from JIT to NEST

            Parameters
            ----------
            model: str
                the model's name.

        """
        for model in models:
            jitModel = ModelManager.JitModels[model]
            if jitModel.hasChanged:
                ModelManager.Nest.SetDefaults(model, jitModel.default)

    @staticmethod
    def addJitModel(modelName, n, jitModel):
        """ Store the ``JitModel`` instance and allocate the IDs space.

            Parameters
            ----------
            modelName: str
                the model's name.
            n: int
                the passed argument to the ``nest.Create`` function.

            JitModel: JitModel
                the JIT representation of the model.

        """
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
        """ Update the allocated IDs of the model.

            Parameters
            ----------
            modelName: str
                the model's name.
            n: int
                the passed argument to the ``nest.Create`` function.

        """
        pair = [ModelManager.Index, ModelManager.Index + n]
        ModelManager.ModelIndexer[modelName].addRange(pair)
        ModelManager.Index += n

    # @staticmethod
    # def createJitNode(modelName):
    #     pair = [ModelManager.Index, ModelManager.Index + n - 1]
    #     ModelManager.ModelIndexer[modelName].addRange(pair)
    #     ModelManager.Index += n

    @staticmethod
    def updateIndex(modelName, n):
        """ Update the allocated IDs of the model.

            Parameters
            ----------
            modelName: str
                the model's name.
            n: int
                the passed argument to the ``nest.Create`` function.

        """
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
        """ Get the original name of the model after creating copies.

            Parameters
            ----------
            models: list[str]
                list of the model names.

            Returns
            -------
            list[str]:
                list of the original names of the models.  
        """
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
        """ Get the ``NodeCollectionProxy`` at certain position.

            Parameters
            ----------
            index: int
                global position of the item in the collection.

            Returns 
            -------
            (NodeCollectionProxy, int):
                the first element represents the NodeCollection instance containing the item in the global position. The second element is the relative position of the item in the retrieved collection.

        """
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
        """Retrieve a ``NodeCollectionProxy`` objects that covers the given IDs.

            Parameters
            ----------
            ids: list[int] 
               list of IDs.

            Returns
            -------
            list[NodeCollectionProxy]:
                map each ID to the NodeCollectionProxy it belongs to.

        """
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
        """ Execute the ``nest.CopyModel`` function.

            Parameters
            ----------
            names: list[str]
                list of models to copy.
        """
        for modelName in names:
            jitModel = ModelManager.JitModels[modelName]
            if len(jitModel.alias) > 0:
                for alias in jitModel.alias:
                    newModel = ModelManager.JitModels[alias]
                    ModelManager.Nest.CopyModel(jitModel.name, newModel.name, newModel.getValues())
