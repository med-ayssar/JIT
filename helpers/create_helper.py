from sys import modules
from jit.models.model_query import ModelQuery
from jit.models.node_collection_proxy import NodeCollectionProxy
from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitModel, JitNode, JitNodeCollection
from jit.utils.thread_manager import JitThread


class CreateHelper:
    def __init__(self, modelName):
        # prepare the NodeCollectionProxy instance
        self.nodeCollectionProxy = NodeCollectionProxy()

    def Create(self, modelName, n=1, params=None, positions=None, options=None):
        if modelName in ModelManager.JitModels:
            self.handleJitModel(modelName, n, params, positions)
        # if the model is already installed
        elif modelName in ModelManager.Nest.Models():
            self.handleBuiltIn(modelName, n, params, positions)
        # else if the model is an external lib, but not yet installed
        else:
            model_query = ModelQuery(modelName)
            # create the model handle (nestml or lib)
            self.modelHandle = model_query.getModelHandle()
            if self.modelHandle.is_lib:
                self.handleExternalLib(modelName, n, params, positions)
            # else if the model is only available as nestml object
            else:
                self.handleNestml(modelName, n, params, positions)
        return self.nodeCollectionProxy

    def handleBuiltIn(self, modelName, n=1, params=None, positions=None):
        # create the real instance of NodeCollection
        nodeCollection = ModelManager.Nest.Create(modelName, n, params, positions)
        # make the NodeCollection hashable, will be removed later
        setattr(nodeCollection.__class__, "__hash__", lambda nc: hash(nc._datum))
        # store the nodeCollection in the nodeCollectionProxy
        self.nodeCollectionProxy.nestNodeCollection = nodeCollection
        # set Ids range
        first, last = ModelManager.updateIndex(modelName, len(nodeCollection))
        self.nodeCollectionProxy.virtualIds.append(range(first, last))

        ModelManager.NodeCollectionProxy.append(self.nodeCollectionProxy)

    def handleExternalLib(self, modelName, n=1, params=None, positions=None):
        # add module to path
        self.modelHandle.add_module_to_path()
        # install the module
        ModelManager.Nest.Install(self.modelHandle.moduleName)
        # create the instances of the module
        nodeCollection = ModelManager.Nest.Create(modelName, n, params, positions)
        # store the nodeCollection in the nodeCollectionProxy
        self.nodeCollectionProxy.nestNodeCollection = nodeCollection
        # set Ids range
        first, last = ModelManager.updateIndex(modelName, n)
        self.nodeCollectionProxy.virtualIds.append(range(first, last + 1))

        ModelManager.NodeCollectionProxy.append(self.nodeCollectionProxy)

    def handleNestml(self, modelName, n=1, params=None, positions=None):

        ModelManager.ExternalModels.append(modelName)
        self.modelHandle.processModels(None)
        model = self.modelHandle.getModels()[0]
        
        givenKeys = set(params.keys())
        expectedKeys = set(model.declaredVarialbes)
        result = givenKeys.difference(expectedKeys)
        if len(result) > 0:
            wrongKeys = ",".join(result)
            raise KeyError (f"{modelName} doesn't have {wrongKeys} as paramaters or states")


        self.registerModels([model])

        self.handleJitModel(modelName, n, params, positions)

        
        ModelManager.add_module_to_install(self.modelHandle.neuron, self.modelHandle.add_module_to_path)

        createThread = JitThread([model.name], self.modelHandle.build)
        ModelManager.Threads.append(createThread)
        # start thread
        createThread.start()

    def handleJitModel(self, modelName, n=1, params=None, positions=None):
        jitModel = ModelManager.JitModels[modelName]
        n, dic = self.getParams(modelName, n, params, positions)
        jitModel.setCreateParams(**dic)
        first, last = ModelManager.updateIndex(modelName, n)
        initialJitNode = JitNode(name=modelName, first=first, last=last)
        jitNodeCollection = JitNodeCollection(initialJitNode, isNotInitial=False)
        if positions:
            jitNodeCollection.setSpatial(positions)
        self.nodeCollectionProxy.jitNodeCollection = jitNodeCollection
        self.nodeCollectionProxy.set(**params)
        # set Ids range
        self.nodeCollectionProxy.virtualIds.append(range(first, last))
        ModelManager.NodeCollectionProxy.append(self.nodeCollectionProxy)

    def getParams(self, model, n, params, positions):
        positionsXorN = n if positions is None else positions
        key = "n" if positions is None else "positions"
        import numpy

        size = n if positions is None else numpy.prod(positions.shape)
        return size, {"model": model, "params": params, key: positionsXorN}

  
   

    def registerModels(self, models):
        for model in models:
            name = model.name
            modelChecker = model
            mtype = model.type
            astModel = self.modelHandle.neurons[0] if mtype == "neuron" else self.modelHandle.synapse[0]
            jitModel = JitModel(name=name, modelChecker=modelChecker, astModel=astModel, mtype=mtype)
            ModelManager.JitModels[name] = jitModel
