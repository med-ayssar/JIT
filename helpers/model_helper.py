from nbformat import current_nbformat_minor
from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitModel, JitNode
from jit.utils.thread_manager import JitThread
from jit.models.model_query import ModelQuery
from jit.utils.utils import getCommonItemsKeys
import copy


class CopyModel:
    Pending = []

    def __init__(self, old, new, newDefault):
        self.oldModelName = old
        self.newModelName = new
        self.newDefault = newDefault

    def copyModel(self):
        if self.oldModelName in ModelManager.JitModels:
            self.handleJitModel()
        elif self.oldModelName in ModelManager.Nest.Models():
            self.handleBuiltIn()
        else:
            # initiate search for the model
            model_query = ModelQuery(self.oldModelName, onlyNeuron=False)
            ModelManager.ExternalModels.append(self.oldModelName)
            ModelManager.ExternalModels.append(self.newModelName)

            # create the model handle (nestml or lib)
            self.modelHandle = model_query.getModelHandle()

            if self.modelHandle.is_lib:
                self.handleExternLib()
            else:
                self.handleNestml()

    def handleBuiltIn(self):
        neuron, synapse = self.__getNeuronSynapsePair()
        if synapse is None:
            ModelManager.Nest.CopyModel(
                self.modelHandle.neuron, self.newModelName, self.newDefault)
        else:
            neuronName = f"{neuron}__with_{synapse}"
            keys = set(ModelManager.Nest.GetDefaults(neuronName).keys())
            commonKeys = getCommonItemsKeys(keys, synapse)

            neuronDict = {}
            for neuronKey, synapseKey in commonKeys.items():
                value = self.newDefault.pop(synapseKey, None)
                if value:
                    neuronDict[neuronKey] = value

            CopyModel.Pending.append([ModelManager.Nest.CopyModel, self.modelHandle.neuron,
                                     self.newModelName, self.newDefault])

            # ModelManager.Nest.CopyModel(
            #    self.modelHandle.neuron, self.newModelName, self.newDefault)

            ModelManager.Nest.SetDefaults(neuronName, neuronDict)

    def __getNeuronSynapsePair(self):
        currentModuleName = self.modelHandle.moduleName
        currentModuleName = currentModuleName.replace("module", "")
        if currentModuleName.find("__with_") > -1:
            neuronSynapse = currentModuleName.split("__with_")
            assert len(neuronSynapse) == 2, "The library file name doesn't contain the expected neuron_synapse name!"
            return neuronSynapse

        else:
            return currentModuleName, None

    def handleJitModel(self):
        oldModel = ModelManager.JitModels[self.oldModelName]
        newModel = JitModel(name=self.newModelName, modelChecker=oldModel.modelchecker,
                            astModel=oldModel.astModel, mtype=oldModel.type)

        newModel.root = self.oldModelName
        oldModel.alias.append(self.newModelName)
        if self.newDefault:
            newModel.default.update(self.newDefault)
        ModelManager.JitModels[self.newModelName] = newModel

    def handleExternLib(self):
        # add module to path
        self.modelHandle.add_module_to_path()
        # install the module
        try:
            ModelManager.Nest.Install(self.modelHandle.moduleName)
        except:
            # in case already loaded
            pass

        defaults = ModelManager.Nest.GetDefaults(self.modelHandle.neuron)
        mtype = "synapse" if "num_connections" in defaults else "neuron"
        jitModel = JitModel(name=self.oldModelName, mtype=mtype)
        jitModel.default = defaults
        ModelManager.JitModels[self.oldModelName] = jitModel
        self.handleJitModel()
        # rest like handleBuitIn
        self.handleBuiltIn()

    def handleNestml(self):
        # extract structural information from the model

        self.modelHandle.processModels(None)
        models = self.modelHandle.getModels()
        self.registerModels(models)
        self.handleJitModel()
        if models[0].type == "neuron":
            ModelManager.add_module_to_install(self.modelHandle.neuron, self.modelHandle.add_module_to_path)

            createThread = JitThread([self.oldModelName], self.modelHandle.build)
            ModelManager.Threads.append(createThread)
            # start thread
            createThread.start()

    def registerModels(self, models):
        for model in models:
            name = model.name
            modelChecker = model
            mtype = model.type
            astModel = self.modelHandle.neurons[0] if mtype == "neuron" else self.modelHandle.synapses[0]
            jitModel = JitModel(name=name, modelChecker=modelChecker, astModel=astModel, mtype=mtype)
            ModelManager.JitModels[name] = jitModel


def models(mtype, sel=None):
    jitModels = list(ModelManager.JitModels.keys())
    nestModels = ModelManager.Nest.Models(mtype, sel)
    return jitModels + list(nestModels)


def printNodes():
    toPrint = []
    for ncp in ModelManager.NodeCollectionProxy:
        if ncp.jitNodeCollection:
            name = ncp.jitNodeCollection.nodes[0].name
            ids = ncp.tolist()
            first = ids[0]
            last = ids[-1]
            __insert(toPrint, name, first, last)

        else:
            name = ncp.get("model")
            name = name["model"][0] if isinstance(name, dict) else name
            ids = ncp.tolist()
            first = ids[0]
            last = ids[-1]
            __insert(toPrint, name, first, last)

    toPrint = list(
        map(
            lambda item: f"{item[1]} ... {item[2]}\t{item[0]}"
            if item[2] - item[1] > 1
            else f"{item[1]}\t{item[0]}",
            toPrint,
        )
    )

    toPrint = "\n".join(toPrint)
    print(toPrint)


def __insert(arr, name, first, last):
    if len(arr) > 0:
        lastSeenElement = arr[-1]
        if lastSeenElement[0] == name:
            arr[-1][2] = last
        else:
            arr.append([name, first, last])
    else:
        arr.append([name, first, last])
