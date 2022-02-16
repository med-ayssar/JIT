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
                   "frozen",
                   "model",
                   "element_type",
                   "local",
                   "Ca"]
    
    dicKeys  = dic.keys()
    for key in list(dicKeys):
        if key in keyToDelete or  key not in toKeep:
            dic.pop(key, None)
    return dic
