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
from jit.models.node_collection_proxy import NodeCollectionProxy
from jit.models.jit_model import JitModel, JitNodeCollection, JitNode
from jit.models.model_handle import ModelHandle



class CreateWrapper(Wrapper):

    def __init__(self, func, original_module, isMethode=False, disable=False):
        super().__init__(func, original_module, isMethode, disable)
        self.nest = original_module
        self.modelHandle = None
        self.nodeCollectionProxy = None
        self.builtIn = False

    def before(self, *args, **kwargs):
        self.neuronName = args[0]
        self.modelCount = next(iter(args[1:2]), 1)
        self.__setup()

        if self.neuronName in self.nest.Models():
            self.nodeCollectionProxy.setAsNodeCollection()
            self.nodeCollectionProxy.setCreateParams(*args, **kwargs)
            self.__handleBuiltIn()
            return args, kwargs

        if not self.modelHandle.is_lib:
            self.__handleNestml(*args, **kwargs)
        else:
            self.nodeCollectionProxy.setAsNodeCollection()
            self.nodeCollectionProxy.setCreateParams(*args, **kwargs)
            self.__create_model(ModelManager.Modules)
        return args, kwargs

    def __setup(self):
        model_query = ModelQuery(self.neuronName)

        self.modelHandle = model_query.get_model_handle()
        self.moduleName = self.modelHandle.moduleName

        self.nodeCollectionProxy = NodeCollectionProxy(self.neuronName, self.moduleName)
        ModelManager.NodeCollectionProxys[self.moduleName] = self.nodeCollectionProxy

    def __handleNestml(self, *args, **kwargs):
        modelDeclatedVars = self.modelHandle.getModelDeclaredVariables()
        jitModel = JitModel(name=self.neuronName, number=self.modelCount, variables=modelDeclatedVars)
        jitModel.addNestModule(self.nest)
        jitModel.setCreateParams(*args, **kwargs)

        first, last = ModelManager.addJitModel(self.neuronName, self.modelCount, jitModel)
        initialJitNode = JitNode(name=self.neuronName, first=first, last=last)

        self.nodeCollectionProxy.addJitNodeCollection(JitNodeCollection(initialJitNode))
        ModelManager.add_module_to_install(self.moduleName, self.modelHandle)

        createThread = JitThread(self.neuronName, self.__create_model, ModelManager.Modules)
        ModelManager.Threads.append(createThread)

        # start thread
        createThread.start()

    def __handleBuiltIn(self):
        self.modelHandle = ModelHandle(self.neuronName, "", True)
        ModelManager.NodeCollectionProxys[self.neuronName] = self.nodeCollectionProxy
        ModelManager.add_module_to_install(self.neuronName, self.modelHandle)

        self.builtIn = True

    def __create_model(self, sharedDict):
        self.modelHandle.build()
        self.modelHandle.isValid = True
        module_name = f"{self.neuronName}module"
        ModelManager.add_module_to_install(module_name, self.modelHandle)

    def after(self, *args):
        if self.builtIn or self.modelHandle.is_lib:
            self.nodeCollectionProxy.toNodeCollection()
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
        self.property = {"Install": original_module.Install}
        self.property["Create"] = original_module.Create
        self.property["Models"] = original_module.Models
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

                    if handle.neuron not in self.property["Models"]():
                        ModelManager.NodeCollectionProxys[module].toNodeCollection()
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
