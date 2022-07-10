from logging import root
from jit.helpers.connect_helper import ConnectHelper
from jit.helpers.nodeCollection_helper import NodeCollectionHelper
from jit.wrapper.wrapper import Wrapper
import sys
from loguru import logger
from jit.helpers.create_helper import CreateHelper
from jit.helpers.simulate_helper import SimulateHelper
from jit.helpers.model_helper import CopyModel, models, printNodes
from jit.models.model_manager import ModelManager
from jit.utils.utils import swapConnections
from jit.models.node_collection_proxy import NodeCollectionProxy


class CreateWrapper(Wrapper):
    """Wrapper for the NEST Create function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.createHelper = None
        self.nodeCollectionProxy = None

    def before(self, modelName, n=1, params=None, positions=None):
        self.createHelper = CreateHelper()
        self.nodeCollectionProxy = self.createHelper.Create(modelName, n, params, positions)
        return (), {}

    def after(self, *args):
        return self.nodeCollectionProxy

    def main_func(self, *args, **kwargs):
        pass

    @staticmethod
    def getName():
        return "nest.Create"


class ConnectWrapper(Wrapper):
    """Wrapper for the NEST Connect function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.connectionHelper = ConnectHelper()

    def before(self, pre, post, conn_spec=None, syn_spec=None, return_synapsecollection=False):
        # reset the SimulateHelper
        self.connectionHelper.reset()
        models = set()
        postNodes = None
        if type(syn_spec) == str:
            synapseName = syn_spec
        else:
            synapseName = syn_spec.get("synapse_model", "static_synapse") if syn_spec else "static_synapse"
        if synapseName and synapseName in ModelManager.ExternalModels:
            postNodes, synapseName = self.connectionHelper.convertPostNeuron(post, synapseName)
            if synapseName:
                models.add(synapseName)

        sourceModelName = set(pre.get()["models"]) if pre.hasJitNodeCollection() else set()
        targetModelName = set(post.get()["models"]) if post.hasJitNodeCollection() else set()
        neuronModels_ = sourceModelName.union(targetModelName)
        models = neuronModels_.union(models)

        # wait for all threads to finish
        rootModels = ModelManager.getRootOf(models)
        self.connectionHelper.waitForThreads(rootModels)

        # install all new modules
        if len(rootModels) > 0:
            self.connectionHelper.installModules(rootModels)
        # convert all JitNodeCollections to NodeCollections
        self.connectionHelper.convertToNodeCollection(pre)
        if postNodes:
            if post.nestNodeCollection is not None:
                swapConnections(post.nestNodeCollection, postNodes)
            post.nestNodeCollection = postNodes
            post.jitNodeCollection = None

        else:
            self.connectionHelper.convertToNodeCollection(post)

        # print report summary
        # self.connectionHelper.showReport()
        # check if we must abort before running the simulate
        if self.connectionHelper.mustAbort():
            sys.exit()
        return (pre.nestNodeCollection, post.nestNodeCollection), {"conn_spec": conn_spec, "syn_spec": syn_spec, "return_synapsecollection": return_synapsecollection}

    @staticmethod
    def getName():
        return "nest.Connect"


class SimulateWrapper(Wrapper):
    """Wrapper for the NEST Simulate function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.simulateHelper = SimulateHelper()

    def before(self, *args, **kwargs):
        # reset the SimulateHelper
        self.simulateHelper.reset()
        # wait for all threads to finish
        self.simulateHelper.waitForThreads()
        # install all new modules
        self.simulateHelper.installModules()
        # convert all JitNodeCollections to NodeCollections
        self.simulateHelper.convertToNodeCollection()
        # broadcast converted JitNodeCollections to their subsets
        # self.simulateHelper.broadcastChanges()
        # print report summary
        # self.simulateHelper.showReport()
        # check if we must abort before running the simulate
        if self.simulateHelper.mustAbort():
            sys.exit()

        return args, kwargs

    def after(self, *args):
        self.simulateHelper.deleteJitModels()

    @ staticmethod
    def getName():
        return "nest.Simulate"


class DisableNestFunc(Wrapper):
    """Wrapper for disabling any NEST function."""

    def __init__(self, *args, **kwargs):
        args = args + (True,)
        super().__init__(*args, **kwargs)

    @ staticmethod
    def getName():
        # just an example how to disable nest functions
        return ["nest.Install"]

    @ staticmethod
    def wrapps_one():
        return False


class NodeCollectionWrapper(Wrapper):
    """Wrapper for the NEST NodeCollection class."""

    def __init__(self, clz, original_module, isMethode=False, disable=False):
        super().__init__(clz, original_module, isMethode, disable)
        self.nodeCollection = clz
        setattr(clz, "__hash__", lambda nc: hash(nc._datum))
        setattr(clz, "__deepcopy__", lambda self, memo: self)

    def main_func(self, data=None):
        return NodeCollectionHelper().createNodeCollectionProxy(data)

    def after(self, nodeCollectionProxy):
        return nodeCollectionProxy

    @ staticmethod
    def getName():
        return "nest.NodeCollection"


class CopyModelWrapper(Wrapper):
    """Wrapper for the NEST CopyModel function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, True, disable)

    def main_func(self, existing, new, params=None):
        CopyModel(old=existing, new=new, newDefault=params).copyModel()

    @ staticmethod
    def getName():
        return "nest.CopyModel"


class GetStatusWrapper(Wrapper):
    """Wrapper for the NEST GetStatus function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, nodes, keys=None, output=""):
        res = []
        if isinstance(nodes, NodeCollectionProxy):
            for node in nodes:
                if node.jitNodeCollection:
                    if keys is None:
                        res.append(node.jitNodeCollection.get())
                    else:
                        res.append(node.jitNodeCollection.get(keys))

                if node.nestNodeCollection:
                    res.extend(ModelManager.Nest.GetStatus(node.nestNodeCollection, keys))
            return res
        else:
            # synapsecollection
            return ModelManager.Nest.GetStatus(nodes, keys)

    @ staticmethod
    def getName():
        return "nest.GetStatus"


class SetStatusWrapper(Wrapper):
    """Wrapper for the NEST SetStatus function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, nodes, params, val=None):
        if isinstance(params, str):
            nodes.set({params: val})
        else:
            nodes.set(params)

    @ staticmethod
    def getName():
        return "nest.SetStatus"


class ResetKernelWrapper(Wrapper):
    """Wrapper for the NEST ResetKernel function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, True, disable)

    def main_func(*args, **kwargs):
        ModelManager.resetManager()
        ModelManager.Nest.ResetKernel()

    @ staticmethod
    def getName():
        return "nest.ResetKernel"


class SetDefaultsWrapper(Wrapper):
    """Wrapper for the NEST SetDefaults function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, model, params, val=None):
        setFunc = None
        if model in ModelManager.JitModels:
            setFunc = ModelManager.JitModels[model].setDefaults
        else:
            setFunc = ModelManager.Nest.SetDefaults
        if isinstance(params, str):
            setFunc({params: val})
        else:
            setFunc(model, params)

    @ staticmethod
    def getName():
        return "nest.SetDefaults"


class GetDefaultsWrapper(Wrapper):
    """Wrapper for the NEST GetDefaults function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, modelName, keys=None, output=""):
        if modelName in ModelManager.JitModels:
            defautls = ModelManager.JitModels[modelName].default
            if keys is None:
                return defautls
            else:
                res = {}
                for k, v in defautls.items():
                    if k in keys:
                        res[k] = v
                return res
        elif modelName in ModelManager.Nest.Models():
            return ModelManager.Nest.GetDefaults(modelName, keys, output)

    @ staticmethod
    def getName():
        return "nest.GetDefaults"


class ModelsWrapper(Wrapper):
    """Wrapper for the NEST Models function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, mtype='all', sel=None):
        return models(mtype, sel)

    @ staticmethod
    def getName():
        return "nest.Models"


class PrintNodesWrapper(Wrapper):
    r"""Wrapper for the NEST PrintNode function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, True, disable)

    def main_func(self, mtype='all', sel=None):
        return printNodes()

    @ staticmethod
    def getName():
        return "nest.PrintNodes"


class GetConnectionsWrapper(Wrapper):
    """Wrapper for the NEST GetConnections function."""

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def before(self, source=None, target=None, synapse_model=None, synapse_label=None):
        if source:
            source = source.nestNodeCollection
        if target:
            target = target.nestNodeCollection
        return (source, target, synapse_model, synapse_label), {}

    @staticmethod
    def getName():
        return "nest.GetConnections"


def installWrappers():
    """Create a dictionary of the implemented wrapper classes"""

    sub_classes = Wrapper.__subclasses__()
    to_wrap = {}
    for sub_clz in sub_classes:
        if sub_clz.wrapps_one():
            to_wrap[sub_clz.getName()] = sub_clz
        else:
            for name in sub_clz.getName():
                to_wrap[name] = sub_clz
    return to_wrap


to_wrap = installWrappers()
