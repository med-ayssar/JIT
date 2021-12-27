from jit.models.node_collection_proxy import NodeCollectionProxy
from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitNodeCollection


class NodeCollectionHelper():
    def __init__(self):
        pass
        # no-op

    def createNodeCollectionProxy(self, data=None):
        nodeCollectionProxy = NodeCollectionProxy()
        if data is None:
            return nodeCollectionProxy
        if isinstance(data, NodeCollectionProxy):
            return data
        else:
            proxies = ModelManager.getNodeCollectionProxies(data)
            jitNodes = []
            nestIds = []
            for proxy in proxies:
                if proxy.jitNodeCollection:
                    jitNodes.extend(proxy.jitNodeCollection.nodes)
                if proxy.nestNodeCollection:
                    nestIds.extend(proxy.nestNodeCollection.tolist())
            jitNodeCollection = JitNodeCollection(jitNodes) if len(jitNodes) > 0 else None
            nestNodeCollection = ModelManager.Nest.NodeCollection(nestIds) if len(nestIds) > 0 else None
            proxy =  NodeCollectionProxy(jitNodeCollection, nestNodeCollection)
            proxy.virtualIds.extend(self.__groupByDistance(data))
            return proxy

    def __groupByDistance(self, items):
        res = []
        if len(items) == 1:
            return [range(items[0], items[0] + 1)]
        else:
            first = items[0]
            last = first
            for i in range(1, len(items)):
                if items[i] - last == 1:
                    last = items[i]
                else:
                    res.append(range(first, last + 1))
                    first = items[i]
                    last = items[i]
            res.append(range(first, last + 1))
        return res
