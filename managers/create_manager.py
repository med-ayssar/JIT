from jit.models.model_query import ModelQuery
from jit.models.node_collection_proxy import NodeCollectionProxy
from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitModel, JitNode, JitNodeCollection
from jit.utils.thread_manager import JitThread


class CreateManager:
    def __init__(self, modelName):
        # initiate search for the model
        model_query = ModelQuery(modelName)
        # create the model handle (nestml or lib)
        self.modelHandle = model_query.get_model_handle()
        # prepare the NodeCollectionProxy instance
        self.nodeCollectionProxy = NodeCollectionProxy()
        # register the NodeCollectionProxy instance
        ModelManager.NodeCollectionProxys[modelName] = self.nodeCollectionProxy

    def Create(self, modelName, n=1, params=None, posistions=None):
        # if the model is already installed
        if modelName in ModelManager.Nest.Models():
            self.handleBuiltIn(modelName, n, params, posistions)
        # else if the model is an external lib, but not yet installed
        elif self.modelHandle.is_lib:
            self.handleExternalLib(modelName, n, params, posistions)
        # else if the model is only available as nestml object
        else:
            self.handleNestml(modelName, n, params, posistions)
        return self.nodeCollectionProxy

    def handleBuiltIn(self, modelName, n=1, params=None, posistions=None):
        # create the real instance of NodeCollection
        nodeCollection = self.nest.Create(modelName, n, params, posistions)
        # make the NodeCollection hashable, will be removed later
        setattr(nodeCollection.__class__, "__hash__", lambda nc: hash(nc._datum))
        # store the nodeCollection in the nodeCollectionProxy
        self.nodeCollectionProxy.nestNodeCollection = nodeCollection
        # register the nodeCollectionProxy in the ModelManage stack
        ModelManager.NodeCollectionProxys[self.neuronName] = self.nodeCollectionProxy

    def handleExternalLib(self, modelName, n=1, params=None, posistions=None):
        # add module to path
        self.modelHandle.build()
        # install the module
        ModelManager.Nest.Install(self.modelHandle.moduleName)
        # create the instances of the module
        nodeCollection = ModelManager.Nest.Create(modelName, n, params, posistions)
        # store the nodeCollection in the nodeCollectionProxy
        self.nodeCollectionProxy.nestNodeCollection = nodeCollection
        # register the nodeCollectionProxy in the ModelManage stack
        ModelManager.NodeCollectionProxys[self.neuronName] = self.nodeCollectionProxy

    def handleNestml(self, modelName, n=1, params=None, posistions=None):
        # extract structural information from the model
        modelDeclatedVars = self.modelHandle.getModelDeclaredVariables()
        # create the JitModel holding the model strucutre
        jitModel = JitModel(name=self.neuronName, number=n, variables=modelDeclatedVars)
        # store the additional parameters in the Jitmodel instance
        jitModel.setCreateParams(n=1, params=params, posistions=posistions)
        # create the first JitNode referring to the JitModel instance
        first, last = ModelManager.addJitModel(self.neuronName, self.modelCount, jitModel)
        initialJitNode = JitNode(name=self.neuronName, first=first, last=last)

        # store the JitNodeCollection in the Proxy
        self.nodeCollectionProxy.jitNodeCollection = JitNodeCollection(initialJitNode)
        ModelManager.add_module_to_install(self.modelHandle.moduleName, self.modelHandle)

        # define local function
        def createModel(instance):
            instance.modelHandle.build()
            ModelManager.add_module_to_install(instance.modelHandle.modelName, instance.modelHandle)

        createThread = JitThread(modelName, createModel, self)
        ModelManager.Threads.append(createThread)
        # start thread
        createThread.start()
