from jit.models.model_manager import ModelManager
from jit.models.model_query import ModelQuery
import inspect


def whichFunc():
    return inspect.stack()[1][3]


def setSynapsesKeys(synapses, keys):
    for ncKey, synapseKey in keys.items():
        for synapse in synapses:
            synapse.setStates(synapseKey)


def getCommonItemsKeys(nodeCollectionKeys, synapseName):
    keys = {}
    for key in nodeCollectionKeys:
        if synapseName in key:
            toReplace = f"__for_{synapseName}"
            synapseKey = key.replace(toReplace, "")
            keys[key] = synapseKey
    return keys


def updateNodeCollectionWithSynapseItems(nc, synapseItems, keys):
    toSet = {}
    for ncKey, synapseKey in keys.items():
        newValue = synapseItems.get(synapseKey, None)
        if newValue:
            toSet[ncKey] = newValue
    if len(toSet) > 0:
        nc.set(**toSet)


def cleanDictionary(dic, toKeep):
    keyToDelete = ["recordables",
                   "node_uses_wfr",
                   "synaptic_elements",
                   "thread",
                   "vp",
                   "global_id",
                   "thread_local_id",
                   "model",
                   "element_type",
                   "local",
                   "Ca",
                   "model_id",
                   "is_vectorized"]

    dicKeys = dic.keys()
    for key in list(dicKeys):
        if key in keyToDelete or key not in toKeep:
            dic.pop(key, None)
    return dic


def handleNestmlNestml(postNeuron, synapseName):
    from jit.models.model_handle import ModelHandle

    postNeuronValues = postNeuron.get()
    neuronName = postNeuronValues["models"]
    neuronName = getName(postNeuron)

    synapse = ModelManager.JitModels[synapseName]
    neuron = ModelManager.JitModels[neuronName]

    synapsesToUpdate = []
    synapseValues = synapse.default
    synapsesToUpdate.append(synapse)

    rootSynapse = synapse.root if synapse.root else synapseName
    synapseValues["synapse_model"] = rootSynapse

    rootNeuron = neuron.root if neuron.root else neuronName

    kwargs = neuron.createParams["kwargs"]
    args = neuron.createParams["args"]

    synapseAst = ModelManager.ParsedModels[rootSynapse]
    neuronAst = ModelManager.ParsedModels[rootNeuron]

    newNeuronName = f"{rootNeuron}__with_{rootSynapse}" if "with" not in rootNeuron else rootNeuron
    newSynapseName = f"{rootSynapse}__with_{rootNeuron}" if "with" not in rootSynapse else rootSynapse

    # mnust clone instead
    ModelManager.JitModels[newSynapseName] = ModelManager.JitModels[rootSynapse]
    newSynapse = ModelManager.JitModels[newSynapseName]
    newSynapse.name = newSynapseName
    synapsesToUpdate.append(newSynapse)

    modelHandle = ModelHandle(newNeuronName, neuronAst.file_path)
    codeGenerationOpt = ModelHandle.getCodeGenerationOptions(neuronAst, synapseAst)
    modelHandle.setupFrontEnd(codeGenerationOpt)
    codeGenerator = ModelHandle.getCodeGenerator(codeGenerationOpt)

    neurons, synapses = codeGenerator.analyse_transform_neuron_synapse_pairs([neuronAst], [synapseAst])
    codeGenerator.analyse_transform_synapses(synapses)

    neurons = neurons[1:]
    codeGenerator.analyse_transform_neurons(neurons)

    neuron = neurons[0]
    kwargs["model"] = neuron.get_name()

    modelHandle.neurons = neurons
    modelHandle.synapses = synapses
    modelHandle.codeGenerator = codeGenerator
    modelHandle.build()

    moduleName = f"{neuron.get_name()}module"
    ModelManager.Nest.Install(moduleName)

    newNodeCollection = ModelManager.Nest.Create(*args, **kwargs)

    synapseStates = getCommonItemsKeys(newNodeCollection.get().keys(), synapseValues["synapse_model"])
    setSynapsesKeys(synapsesToUpdate, synapseStates)

    updateNodeCollection(newNodeCollection, postNeuronValues, synapseValues)

    return newNodeCollection, newSynapseName


def retrieveSynapseStates(ncp, synapse):
    k1 = set(ncp.get().keys())
    k2 = set(synapse.keys())
    return k1.intersection(k2)


def updateNodeCollection(newNcp, oldNcpDic,  synapseValues):
    newNcpKeys = newNcp.get().keys()
    k1 = set(newNcpKeys)
    k2 = set(oldNcpDic.keys())
    sharedKeys = k1.intersection(k2)
    oldNcpDic = cleanDictionary(oldNcpDic, sharedKeys)
    newNcp.set(**oldNcpDic)
    neuronToSynapse = getCommonItemsKeys(newNcpKeys, synapseValues["synapse_model"])
    updateNodeCollectionWithSynapseItems(newNcp, synapseValues, neuronToSynapse)


def handleNestmlBuiltin(postNeuron, synapseName):
    return None, None


def handleExternalNestml(postNeuron, synapseName):
    neuronName = getName(postNeuron)
    modelQuery = ModelQuery(neuron_name=neuronName)
    nestmlHandle = modelQuery.find_model_in_nestml()
    if nestmlHandle is None:
        raise Exception(
            f"Cannnot find nestml source file for neuron name={neuronName}")

    from jit.models.model_handle import ModelHandle

    postNeuronValues = postNeuron.get()
    nestmlHandle.processModels()
    neuronAst = ModelManager.ParsedModels.pop(neuronName, None)

    synapse = ModelManager.JitModels[synapseName]

    synapsesToUpdate = []
    synapseValues = synapse.default
    synapsesToUpdate.append(synapse)

    rootSynapse = synapse.root if synapse.root else synapseName
    synapseValues["synapse_model"] = rootSynapse

    rootNeuron = neuronAst.get_name()
    newNeuronName = f"{rootNeuron}__with_{rootSynapse}" if "with" not in rootNeuron else rootNeuron

    args, kwargs = postNeuron.getCreationParams()

    synapseAst = ModelManager.ParsedModels[rootSynapse]
    newSynapseName = f"{rootSynapse}__with_{neuronName}"

    # mnust clone instead
    ModelManager.JitModels[newSynapseName] = ModelManager.JitModels[rootSynapse]
    newSynapse = ModelManager.JitModels[newSynapseName]
    newSynapse.name = newSynapseName
    synapsesToUpdate.append(newSynapse)

    modelHandle = ModelHandle(newNeuronName, nestmlHandle.path)
    codeGenerationOpt = ModelHandle.getCodeGenerationOptions(neuronAst, synapseAst)
    modelHandle.setupFrontEnd(codeGenerationOpt)
    codeGenerator = ModelHandle.getCodeGenerator(codeGenerationOpt)

    neurons, synapses = codeGenerator.analyse_transform_neuron_synapse_pairs([neuronAst], [synapseAst])
    codeGenerator.analyse_transform_synapses(synapses)

    neurons = neurons[1:]
    codeGenerator.analyse_transform_neurons(neurons)

    neuron = neurons[0]
    kwargs["model"] = neuron.get_name()

    modelHandle.neurons = neurons
    modelHandle.synapses = synapses
    modelHandle.codeGenerator = codeGenerator
    modelHandle.build()

    moduleName = f"{neuron.get_name()}module"
    ModelManager.Nest.Install(moduleName)

    newNodeCollection = ModelManager.Nest.Create(*args, **kwargs)

    synapseStates = getCommonItemsKeys(newNodeCollection.get().keys(), synapseValues["synapse_model"])
    setSynapsesKeys(synapsesToUpdate, synapseStates)

    updateNodeCollection(newNodeCollection, postNeuronValues, synapseValues)

    return newNodeCollection, newSynapseName


def handleBuiltinNestml(postNeuron, synapseName):
    postNeuronValues = postNeuron.get()
    neuronName = getName(postNeuron)

    synapse = ModelManager.JitModels[synapseName]
    synapsesToUpdate = []
    synapseValues = synapse.default
    synapsesToUpdate.append(synapse)

    rootSynapse = synapse.root if synapse.root else synapseName
    synapseValues["synapse_model"] = rootSynapse

    args, kwargs = postNeuron.getCreationParams()

    newSynapseName = f"{rootSynapse}__with_{neuronName}"
    newNeuronName = f"{neuronName}__with_{rootSynapse}"

    ModelManager.JitModels[newSynapseName] = ModelManager.JitModels[rootSynapse]
    newSynapse = ModelManager.JitModels[newSynapseName]
    newSynapse.name = newSynapseName
    synapsesToUpdate.append(newSynapse)

    kwargs["model"] = newNeuronName
    assert newNeuronName in ModelManager.Nest.Models(), f" The model {newNeuronName} isn't found in nest"
    newNodeCollection = ModelManager.Nest.Create(*args, **kwargs)

    synapseStates = getCommonItemsKeys(newNodeCollection.get().keys(), synapseValues["synapse_model"])
    setSynapsesKeys(synapsesToUpdate, synapseStates)

    updateNodeCollection(newNodeCollection, postNeuronValues, synapseValues)

    return newNodeCollection, newSynapseName


def handleExternalExternal(postNeuron, synapseName):
    postNeuronValues = postNeuron.get()
    neuronName = postNeuronValues["models"]
    neuronName = getName(postNeuron)

    synapse = ModelManager.JitModels[synapseName]
    neuron = ModelManager.JitModels[neuronName]

    synapsesToUpdate = []
    synapseValues = synapse.default
    synapsesToUpdate.append(synapse)

    rootSynapse = synapse.root if synapse.root else synapseName
    synapseValues["synapse_model"] = rootSynapse

    rootNeuron = neuron.root if neuron.root else neuronName

    kwargs = neuron.createParams["kwargs"]
    args = neuron.createParams["args"]

    newNeuronName = f"{rootNeuron}__with_{rootSynapse}"
    newSynapseName = f"{rootSynapse}__with_{rootNeuron}"

    ModelManager.JitModels[newSynapseName] = ModelManager.JitModels[rootSynapse]
    newSynapse = ModelManager.JitModels[newSynapseName]
    newSynapse.name = newSynapseName
    synapsesToUpdate.append(newSynapse)

    kwargs["model"] = newNeuronName
    newNodeCollection = ModelManager.Nest.Create(*args, **kwargs)

    synapseStates = getCommonItemsKeys(newNodeCollection.get().keys(), synapseValues["synapse_model"])
    setSynapsesKeys(synapsesToUpdate, synapseStates)

    updateNodeCollection(newNodeCollection, postNeuronValues, synapseValues)

    return newNodeCollection, newSynapseName


def handleBuiltinBuiltin(postNeuron, synapseName):

    postNeuronValues = postNeuron.get()
    neuronName = getName(postNeuron)
    synapse = ModelManager.JitModels[synapseName]
    synapsesToUpdate = []
    synapseValues = synapse.default
    synapsesToUpdate.append(synapse)

    rootSynapse = synapse.root if synapse.root else synapseName
    synapseValues["synapse_model"] = rootSynapse

    args, kwargs = postNeuron.getCreationParams()

    newNeuronName = f"{neuronName}__with_{rootSynapse}"
    newSynapseName = f"{rootSynapse}__with_{neuronName}"

    ModelManager.JitModels[newSynapseName] = ModelManager.JitModels[rootSynapse]
    newSynapse = ModelManager.JitModels[newSynapseName]
    newSynapse.name = newSynapseName
    synapsesToUpdate.append(newSynapse)

    kwargs["model"] = newNeuronName
    assert newNeuronName in ModelManager.Nest.Models(), f" The model {newNeuronName} isn't found in nest"
    newNodeCollection = ModelManager.Nest.Create(*args, **kwargs)

    synapseStates = getCommonItemsKeys(newNodeCollection.get().keys(), synapseValues["synapse_model"])
    setSynapsesKeys(synapsesToUpdate, synapseStates)

    updateNodeCollection(newNodeCollection, postNeuronValues, synapseValues)

    return newNodeCollection, newSynapseName


def handle(postNeuron, synapseName):
    synapse = ModelManager.JitModels[synapseName]
    rootSynapse = synapse.root if synapse.root else synapseName
    neuronName = getName(postNeuron)

    models = ModelManager.Nest.Models()
    parsedModels = ModelManager.ParsedModels
    newSynapseName = f"{rootSynapse}__with_{neuronName}" if "with" not in rootSynapse else rootSynapse

    if all(x in parsedModels for x in [neuronName, rootSynapse]):
        return handleNestmlNestml(postNeuron, synapseName)

    if neuronName in ModelManager.JitModels and ModelManager.JitModels[neuronName].isFromExternalLib() and synapseName in parsedModels or (neuronName in models and rootSynapse in parsedModels):
        return handleExternalNestml(postNeuron, synapseName)

    if newSynapseName in models:
        return handleBuiltinNestml(postNeuron, synapseName)

    if neuronName in parsedModels and newSynapseName in models:
        return None, None

    if neuronName in parsedModels and synapse.isFromExternalLib():
        return handleBuiltinBuiltin(postNeuron, synapse)


def getName(ncp):
    ncpValues = ncp.get()
    neuronName = ncpValues["models"]
    neuronName = neuronName[0] if isinstance(neuronName, (tuple, list)) else neuronName
    if neuronName == "UnknownNode":
        import re
        pattern = "model=(.*?),"
        neuronName = re.search(pattern, str(ncp)).group(1)
    return neuronName


def swapConnections(oldPostNeuron, newPostNeuron):
    swapSource(oldPostNeuron, newPostNeuron)
    swapTarget(oldPostNeuron, newPostNeuron)


def swapTarget(oldPostNeuron, newPostNeuron):
    connections = ModelManager.Nest.GetConnections(target=oldPostNeuron).get()
    if len(connections) > 0:
        sources = connections["source"]
        sources = [sources] if not isinstance(sources, list) else sources

        targets = connections["target"]
        targets = [targets] if not isinstance(targets, list) else targets

        synapses = connections["synapse_model"]
        synapses = [synapses] if not isinstance(synapses, list) else synapses

        tuples = zip(sources, synapses, targets)
        oldTargetIds = oldPostNeuron.tolist()
        newTargetIds = newPostNeuron.tolist()

        for source, synapse, target in tuples:
            pre = ModelManager.Nest.NodeCollection([source])
            post = ModelManager.Nest.NodeCollection([target])
            ModelManager.Nest.Disconnect(pre, post, syn_spec=synapse)

            pos = oldTargetIds.index(target)
            newId = newTargetIds[pos]
            post = ModelManager.Nest.NodeCollection([newId])
            ModelManager.Nest.Connect(pre, post, syn_spec={"synapse_model": synapse})


def swapSource(oldPostNeuron, newPostNeuron):
    connections = ModelManager.Nest.GetConnections(source=oldPostNeuron).get()
    if len(connections) > 0:
        sources = connections["source"]
        sources = [sources] if not isinstance(sources, list) else sources

        targets = connections["target"]
        targets = [targets] if not isinstance(targets, list) else targets

        synapses = connections["synapse_model"]
        synapses = [synapses] if not isinstance(synapses, list) else synapses

        tuples = zip(sources, synapses, targets)
        oldSourcesIds = oldPostNeuron.tolist()
        newSourcesIds = newPostNeuron.tolist()

        for source, synapse, target in tuples:
            source
            pre = ModelManager.Nest.NodeCollection([source])
            post = ModelManager.Nest.NodeCollection([target])
            ModelManager.Nest.Disconnect(pre, post, syn_spec=synapse)

            pos = oldSourcesIds.index(source)
            newId = newSourcesIds[pos]
            pre = ModelManager.Nest.NodeCollection([newId])
            ModelManager.Nest.Connect(pre, post, syn_spec={"synapse_model": synapse})
