from jit.models.node_collection_proxy import NodeCollectionProxy
from jit.models.model_manager import ModelManager
from jit.models.jit_model import JitNodeCollection


class NodeCollectionHelper():
    """Managing the logic behind the ``NodeCollectionWrapper``"""

    def __init__(self):
        """Initialize function.

        """
        pass
        # no-op

    def createNodeCollectionProxy(self, data=None):
        """ Create new instance of the `NodeCollectionProxy`.

            Parameters
            ----------
            data: list[int]
                list of ids
            
            Returns
            -------
            NodeCollectionProxy:
                a wrapper around the NodeCollection

        """
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
        """ Partition the items according to their distance to each other.

            Parameters
            ----------
            items: list[int]
                list of ids
            
            Returns
            -------
            list[list[int]]:
                a partition of the original item list.

        """
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
