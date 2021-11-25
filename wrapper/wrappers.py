import asyncio
from jit.wrapper.wrapper import Wrapper
from jit.models.model_query import ModelQuery
import os
import asyncio
from jit.models.model_manager import ModelManager
from threading import Thread, current_thread
from jit.utils.thread_manager import JitThread


class CreateWrapper(Wrapper):

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.property = {"Install": original_module.Install}
        self.func = func
        self.modelHandle = None

    def before(self, *args, **kwargs):
        self.neuron_name = args[0]
        model_query = ModelQuery(self.neuron_name)
        self.modelHandle = model_query.get_model_handle()
        self.property["args"] = args
        self.property["kwargs"] = kwargs
        createThread = JitThread(self.__create_model, ModelManager.Modules)
        ModelManager.Threads.append(createThread)
        module_name = f"{self.neuron_name}module"
        ModelManager.add_module_to_install(module_name, self.modelHandle)

        # start thread
        createThread.start()
        return args, kwargs

    def __create_model(self, sharedDict):
        self.modelHandle.build()
        params = {"args": self.property["args"],
                  "kwargs": self.property["kwargs"], "name": self.neuron_name}
        self.modelHandle.add_params("Create", params)
        self.modelHandle.isValid = True
        module_name = f"{self.neuron_name}module"
        ModelManager.add_module_to_install(module_name, self.modelHandle)

    def after(self, *args):
        ModelManager.add_model(self.neuron_name, self.modelHandle.get_neuron())
        return ModelManager.to_populate[self.neuron_name]

    def main_func(self, *args, **kwargs):
        # ignore the real nest function
        return args, kwargs

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
        self.property = {"Install": original_module.Install}
        self.property["Create"] = original_module.Create

    def before(self, *args, **kwargs):
        for thread in ModelManager.Threads:
            thread.join()

        current_dict = ModelManager.Modules.get()
        for module, handle in current_dict.items():
            handle.add_module_to_path()
            create_args = handle.params["Create"]["args"]
            create_kwargs = handle.params["Create"]["kwargs"]
            self.property["Install"](module)
            nest_create_return = self.property["Create"](
                *create_args, **create_kwargs)
            ModelManager.populate(
                handle.params["Create"]["name"], nest_create_return)

        ModelManager.Modules.close()

        return args, kwargs

    def main_func(self, *args, **kwargs):
        # ignore the real nest function
        return args, kwargs

    def after(self, *args):
        return super().after(*args)

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
