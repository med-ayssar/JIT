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
        toSet[ncKey] = synapseItems[synapseKey]

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
                   "Ca"]

    dicKeys = dic.keys()
    for key in list(dicKeys):
        if key in keyToDelete or key not in toKeep:
            dic.pop(key, None)
    return dic


def handleNestmlNestml(postNeuron, synapseName):
    from jit.models.model_manager import ModelManager
    from jit.models.model_handle import ModelHandle

    postNeuronValues = postNeuron.get()
    neuronName = postNeuronValues["models"]
    neuronName = neuronName[0] if isinstance(neuronName, (tuple, list)) else neuronName
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

    newNeuronName = f"{rootNeuron}__with_{rootSynapse}"
    newSynapseName = f"{rootSynapse}__with_{rootNeuron}"

    # nust clone instead
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
    setSynapsesKeys(synapsesToUpdate ,synapseStates)

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


def handleNestmlBuiltin(neuronName, synapseName):
    pass


def handleBuiltinNestml(neuronName, synapseName):
    raise Exception(f"Cannot have a builtin neuron {neuronName} with external synapse model {synapseName}")


def handleBuiltinBuiltin(neuronName, synapseName):
    pass
