from jit.helpers.nodeCollection_helper import NodeCollectionHelper
from jit.wrapper.wrapper import Wrapper
import sys
from loguru import logger
from jit.helpers.create_helper import CreateHelper
from jit.helpers.simulate_helper import SimulateHelper


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
    def get_name():
        return "nest.Create"


class ConnectWrapper(Wrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def before(self, *args, **kwargs):
        return super().before(*args, **kwargs)

    def after(self, *args):
        return super().after(*args)

    @staticmethod
    def get_name():
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

    @ staticmethod
    def get_name():
        return "nest.Simulate"


class DisableNestFunc(Wrapper):
    def __init__(self, *args, **kwargs):
        args = args + (True,)
        super().__init__(*args, **kwargs)

    @ staticmethod
    def get_name():
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
    def get_name():
        return "nest.NodeCollection"


def install_wrappers():
    sub_classes = Wrapper.__subclasses__()
    to_wrap = {}
    for sub_clz in sub_classes:
        if sub_clz.wrapps_one():
            to_wrap[sub_clz.get_name()] = sub_clz
        else:
            for name in sub_clz.get_name():
                to_wrap[name] = sub_clz
    return to_wrap


to_wrap = install_wrappers()
