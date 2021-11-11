from jit.wrapper.wrapper import Wrapper
from jit.models.model_query import ModelQuery
import os

class CreateWrapper(Wrapper):

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.property = {"Install": original_module.Install}

    def before(self, *args, **kwargs):
        neuron_name = args[0]
        model_query = ModelQuery(neuron_name)
        model_query.get_model_handle().install()
        print(os.environ["LD_LIBRARY_PATH"])
        self.property["Install"](neuron_name)
       
        return args, kwargs

    def after(self, *args):
        print("Running the after function for nest.Create")
        return super().after(*args)

    @staticmethod
    def get_name():
        return "nest.Create"


class ConnectWrapper(Wrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def before(self, *args, **kwargs):
        return super().before(*args, **kwargs)

    def after(self, *args):
        super().after(*args)

    @staticmethod
    def get_name():
        return "nest.Connect"


class SimulateWrapper(Wrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def before(self, *args, **kwargs):
        return super().before(*args, **kwargs)

    def after(self, *args):
        super().after(*args)

    @staticmethod
    def get_name():
        return "nest.Simulate"


class DisableNestFunc(Wrapper):
    def __init__(self, *args, **kwargs):
        args = args + (True,)
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_name():
        # just an example how to disable nest functions
        return ["nest.Install", "nest.sysinfo"]

    @staticmethod
    def wrapps_one():
        return False


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
