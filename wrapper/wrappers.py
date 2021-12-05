import asyncio
from posixpath import expanduser
from jit.wrapper.wrapper import Wrapper
from jit.models.model_query import ModelQuery
import os
import asyncio
from jit.models.model_manager import ModelManager
from jit.utils.thread_manager import JitThread
from jit.utils.create_report import CreateReport
from string import Template
import sys
from loguru import logger


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
        module_name = f"{self.neuron_name}module"
        self.property["args"] = args
        self.property["kwargs"] = kwargs
        if not self.modelHandle.is_lib:
            createThread = JitThread(self.neuron_name, self.__create_model, ModelManager.Modules)
            ModelManager.Threads.append(createThread)
            ModelManager.add_module_to_install(module_name, self.modelHandle)
            # start thread
            createThread.start()
        else:
            self.__create_model(ModelManager.Modules)
        return args, kwargs

    def __create_model(self, sharedDict):
        self.modelHandle.build()
        params = {"args": self.property["args"], "kwargs": self.property["kwargs"], "name": self.neuron_name}
        self.modelHandle.add_params("Create", params)
        self.modelHandle.isValid = True
        module_name = f"{self.neuron_name}module"
        ModelManager.add_module_to_install(module_name, self.modelHandle)

    def after(self, *args):
        if not self.modelHandle.is_lib:
            ModelManager.add_model(self.neuron_name, self.modelHandle.get_neuron())
            return ModelManager.to_populate[self.neuron_name]
        return args[0]

    def main_func(self, *args, **kwargs):
        # ignore the real nest function
        if self.modelHandle.is_lib:
            return self.func(*args, **kwargs)
        return

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
        self.error_occured = False
        self.report = CreateReport()
        self.reportError = {}

    def before(self, *args, **kwargs):

        self.__insepectThreads()
        current_dict = ModelManager.Modules.get()
        for module, handle in current_dict.items():
            try:
                if handle.neuron not in ModelManager.ThreadsState:
                    msg = "skipped" if handle.is_lib else "ok"
                    handle.add_module_to_path()
                    create_args = handle.params["Create"]["args"]
                    create_kwargs = handle.params["Create"]["kwargs"]
                    self.property["Install"](module)
                    nest_create_return = self.property["Create"](*create_args, **create_kwargs)
                    ModelManager.populate(handle.params["Create"]["name"], nest_create_return)
                    self.report.append([handle.neuron, msg, msg, "ok", "None"])
            except Exception as exp:
                self.report.append([handle.neuron, msg, msg, "Failed"])
                self.error_occured = True
                self.reportError[handle.neuron] = {
                    "phase": "Install",
                    "Failure Message": str(exp)
                }

        ModelManager.Modules.close()
        # print errors summary
        if len(self.reportError) > 0:
            errorSummary = "While processing the models, the follwing errors have occured:\n" + str(self.reportError)
            print(errorSummary)
        # print Create summary
        print(self.report)

        if self.error_occured:
            sys.exit()

        return args, kwargs

    # def main_func(self, *args, **kwargs):
    #     # ignore the real nest function
    #     return args, kwargs
    def __insepectThreads(self):
        for thread in ModelManager.Threads:
            thread.join()
            if thread.modelName in ModelManager.ThreadsState:
                state = ModelManager.ThreadsState[thread.modelName]
                if state["hasError"]:
                    values = [thread.modelName]
                    values.extend(state.values())
                    self.report.append(values)
                    self.reportError[thread.modelName] = {
                        "phase": state["stage"],
                        "Failure Message": state["msg"]
                    }

                self.error_occured = True

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
