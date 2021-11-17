from jit.utils.nest_config import NestConfig
import asyncio
import threading


class ModelManager():
    to_populate = {}
    populated = {}
    Event_loop = asyncio.get_event_loop()
    Lock = threading.Lock()
    Threads = []
    Modules = {}

    @staticmethod
    def add_model(model_name, handle):
        with ModelManager.Lock:
            if hasattr(handle, "is_lib") and handle.is_lib:
                ModelManager.populated[model_name] = handle.get_nest_instance()

        ModelManager.to_populate[model_name] = handle

    @staticmethod
    def populate(name, nodeCollectionInstance):
        with ModelManager.Lock:
            ModelManager.populated[name] = nodeCollectionInstance
            ModelManager.to_populate.pop(name, None)

    @staticmethod
    def add_module_to_install(name, params):
        with ModelManager.Lock:
            ModelManager.Modules[name] = params
