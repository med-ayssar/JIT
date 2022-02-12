from urllib.parse import _NetlocResultMixinStr
from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager
from jit.models.model_handle import ModelHandle
import copy


class ConnectHelper:
    def __init__(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False

    def waitForThreads(self, threadsName):
        toRemove = []
        for thread in ModelManager.Threads:
            if any(name in threadsName for name in thread.names):
                thread.join()
                toRemove.append(thread)
                if thread.names[0] in ModelManager.ThreadsState:
                    state = ModelManager.ThreadsState[thread.names[0]]
                    if state["hasError"]:
                        values = [thread.names[0]]
                        values.extend(state.values())
                        self.report.append(values)
                        self.reportErrors[thread.names[0]] = {
                            "phase": state["stage"],
                            "Failure Message": state["msg"]
                        }

                self.error_occured = True
        # clean threads pool
        for thread in toRemove:
            thread.terminate()
            ModelManager.Threads.remove(thread)

    def installModules(self, modules):

        for model in modules:
            module = f"{model}module"
            addLibToPath = ModelManager.Modules.get(model, None)
            if addLibToPath:
                try:

                    addLibToPath()
                    ModelManager.Nest.Install(module)

                except Exception as exp:
                    self.reportErrors[module] = {
                        "phase": "Install",
                        "Failure Message": str(exp)
                    }
                    self.error_occured = True
        ModelManager.setDefaults(modules)
        ModelManager.copyModels(modules)

    def convertPostNeuron(self, ncp, synapseModel):
        modelName = ncp.get()["models"]
        modelName = modelName[0] if isinstance(modelName, (tuple, list)) else modelName
        if modelName in ModelManager.ExternalModels:

            synapseToUpdate = []
            synapse = ModelManager.JitModels[synapseModel]
            synapseToUpdate.append(synapse)
            synapseModel = synapse.root if synapse.root else synapseModel
            valuesFromSynapse = copy.deepcopy(synapse.default)

            neuron = ModelManager.JitModels[modelName]
            valuesFromNeuron = neuron.default

            kwargs = neuron.createParams["kwargs"]
            args = neuron.createParams["args"]

            newSynapseName = f"{synapseModel}__with_{modelName}"
            ModelManager.JitModels[newSynapseName] = ModelManager.JitModels[synapseModel]
            newGeneratedSynapse = ModelManager.JitModels[newSynapseName]
            newGeneratedSynapse.name = newSynapseName
            synapseToUpdate.append(newGeneratedSynapse)

            if synapse.root:
                synapse = synapse.root
            else:
                synapse = synapse.name

            if neuron.root:
                neuron = neuron.root
            else:
                neuron = neuron.name

            neuronAst = ModelManager.ParsedModels[neuron]
            # for pynestmlfrontent
            nestmlPath = neuronAst.file_path
            synapseAst = ModelManager.ParsedModels[synapse]

            codeGenerationOpt = ModelHandle.getCodeGenerationOptions(neuronAst, synapseAst)
            codeGenerator = ModelHandle.getCodeGenerator(codeGenerationOpt)
            neurons, synapse = codeGenerator.transform([neuronAst], [synapseAst])

            neuron = neurons[1]
            kwargs["model"] = neuron.get_name()
            modelHandle = ModelHandle(neuron.get_name(), nestmlPath)
            modelHandle.initNestmlFrontEnd(codeGenerationOpt)
            modelHandle.neurons = [neuron]
            modelHandle.synapses = synapse
            modelHandle.codeGenerator = codeGenerator
            modelHandle.build()
            moduleName = f"{neuron.get_name()}module"
            ModelManager.Nest.Install(moduleName)

            newNodeCollection = ModelManager.Nest.Create(*args, **kwargs)
            newNodeCollection.set(**valuesFromNeuron)
            commonKeys = self.__getCommonItemsKeys(newNodeCollection, synapseAst.get_name())

            self.__updateNodeCollectionWithSynapseItems(newNodeCollection, valuesFromSynapse, commonKeys)

            self.__setSynapsesKeys(synapseToUpdate, commonKeys)
            return newNodeCollection, newSynapseName

    def __setSynapsesKeys(self, synapses, keys):

        for ncKey, synapseKey in keys.items():
            for synapse in synapses:
                synapse.setStates(synapseKey)

    def __getCommonItemsKeys(self, nc, synapseName):
        nodeCollectionKeys = nc.get().keys()
        keys = {}
        for key in nodeCollectionKeys:
            if synapseName in key:
                toReplace = f"__for_{synapseName}"
                synapseKey = key.replace(toReplace, "")
                keys[key] = synapseKey
        return keys

    def __updateNodeCollectionWithSynapseItems(self, nc, synapseItems, keys):
        toSet = {}
        for ncKey, synapseKey in keys.items():
            toSet[ncKey] = synapseItems[synapseKey]

        nc.set(**toSet)

    def convertToNodeCollection(self, node):
        if node.jitNodeCollection is not None:
            initialNodes = ModelManager.getNodeCollectionProxies(node.tolist())
            for initialNode in initialNodes:
                if initialNode.jitNodeCollection:
                    initialNode.jitNodeCollection.isNotInitial = False
                    initialNode.toNodeCollection()
            ids = node.getNestIds()
            nodeCollection = ModelManager.Nest.NodeCollection(ids)
            if node.nestNodeCollection is None:
                node.nestNodeCollection = nodeCollection
            else:
                node.nestNodeCollection += nodeCollection
            node.jitNodeCollection = None

    def showReport(self):
        if len(self.reportErrors) > 0:
            errorSummary = "While processing the modules, the follwing errors have occured:\n" + str(self.reportErrors)
            print(errorSummary)
        # print Create summary
        print(self.report)

    def mustAbort(self):
        return self.errorOccured

    def reset(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False
