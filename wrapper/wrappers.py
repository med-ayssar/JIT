from jit.helpers.connect_helper import ConnectHelper
from jit.helpers.nodeCollection_helper import NodeCollectionHelper
from jit.wrapper.wrapper import Wrapper
import sys
from loguru import logger
from jit.helpers.create_helper import CreateHelper
from jit.helpers.simulate_helper import SimulateHelper
from jit.helpers.model_helper import CopyModel, Models
from jit.models.model_manager import ModelManager


class CreateWrapper(Wrapper):

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.createHelper = None
        self.nodeCollectionProxy = None

    def before(self, modelName, n=1, params=None, positions=None):
        self.createHelper = CreateHelper(modelName)
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
    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.connectionHelper = ConnectHelper()

    def before(self, pre, post, conn_spec=None, syn_spec=None, return_synapsecollection=False):
        # reset the SimulateHelper
        self.connectionHelper.reset()
        sourceModelName = set(pre.get()["models"]) if pre.hasJitNodeCollection() else set()
        targetModelName = set(post.get()["models"]) if post.hasJitNodeCollection() else set()
        models = sourceModelName.union(targetModelName)
        # wait for all threads to finish
        rootModels = ModelManager.getRootOf(models)
        self.connectionHelper.waitForThreads(rootModels)
        # install all new modules
        self.connectionHelper.installModules(rootModels)
        # convert all JitNodeCollections to NodeCollections
        self.connectionHelper.convertToNodeCollection(pre)
        self.connectionHelper.convertToNodeCollection(post)

        # print report summary
        self.connectionHelper.showReport()
        # check if we must abort before running the simulate
        if self.connectionHelper.mustAbort():
            sys.exit()
        return (pre.nestNodeCollection, post.nestNodeCollection), {"conn_spec": conn_spec, "syn_spec": syn_spec, "return_synapsecollection": return_synapsecollection}

    @staticmethod
    def getName():
        return "nest.Connect"


class SimulateWrapper(Wrapper):
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
        self.simulateHelper.broadcastChanges()
        # print report summary
        self.simulateHelper.showReport()
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
    def __init__(self, clz, original_module, isMethode=False, disable=False):
        super().__init__(clz, original_module, isMethode, disable)
        self.nodeCollection = clz
        setattr(clz, "__hash__", lambda nc: hash(nc._datum))

    def main_func(self, data=None):
        return NodeCollectionHelper().createNodeCollectionProxy(data)

    def after(self, nodeCollectionProxy):
        return nodeCollectionProxy

    @ staticmethod
    def getName():
        return "nest.NodeCollection"


class CopyModelWrapper(Wrapper):
    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, True, disable)

    def main_func(self, existing, new, params=None):
        CopyModel(old=existing, new=new, newDefault=params).copyModel()

    @ staticmethod
    def getName():
        return "nest.CopyModel"


class GetStatusWrapper(Wrapper):
    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, nodes, keys=None, output=""):
        res = []
        for node in nodes:
            if node.jitNodeCollection:
                if keys is None:
                    res.append(node.jitNodeCollection.get())
                else:
                    res.append(node.jitNodeCollection.get(keys))

            if node.nestNodeCollection:
                res.extend(ModelManager.Nest.GetStatus(node.nestNodeCollection, keys))
        return res

    @ staticmethod
    def getName():
        return "nest.GetStatus"


class SetStatusWrapper(Wrapper):
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


class SetDefaultsWrapper(Wrapper):
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
            setFunc(params)

    @ staticmethod
    def getName():
        return "nest.SetDefaults"


class GetDefaultsWrapper(Wrapper):
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
    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, False, disable)

    def main_func(self, mtype='all', sel=None):
       return Models(mtype, sel)

    @ staticmethod
    def getName():
        return "nest.Models"



def installWrappers():
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
