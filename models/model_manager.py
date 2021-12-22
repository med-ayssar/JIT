from jit.utils.nest_config import NestConfig
from multiprocessing import Manager, Queue
import sys

from jit.models.model_indexer import ModelIndexer
from models.jit_model import JitNodeCollection

class ModelManager():
    to_populate = {}
    _Manager = Manager()
    Threads = []
    ThreadsState = _Manager.dict()
    Modules = Queue()
    Modules.put({})
    NodeCollectionProxy = []
    JitModels = {}
    ModelIndexer = {}
    Index = 0
    Nest = None


    @staticmethod
    def add_model(model_name, handle):
        if hasattr(handle, "is_lib") and handle.is_lib:
            ModelManager.populated[model_name] = handle.get_nest_instance()

        ModelManager.to_populate[model_name] = handle

    @staticmethod
    def populate(name, nodeCollectionInstance):
        ModelManager.to_populate[name][0] = nodeCollectionInstance

    @staticmethod
    def add_module_to_install(name, handle):
        try:
            current_dict = ModelManager.Modules.get()
            current_dict[name] = handle
            ModelManager.Modules.put(current_dict)
        except Exception as exp:
            print(exp)
            sys.exit()


    @staticmethod
    def addNestModule(module):
        ModelManager.Nest = module

    @staticmethod
    def addJitModel(modelName, n, jitModel):
        ModelManager.JitModels[modelName] = jitModel
        pair = [ModelManager.Index, ModelManager.Index + n ]
        ModelManager.Index+= n
        if modelName in ModelManager.ModelIndexer:
            ModelManager.ModelIndexer[modelName].addRange(pair)
        else:
            modelIndexer = ModelIndexer(modelName)
            modelIndexer.addRange(pair)
            ModelManager.ModelIndexer[modelName] = modelIndexer
        return pair
    @staticmethod
    def updateJitmodel(modelName, n):
        pair = [ModelManager.Index, ModelManager.Index + n]
        ModelManager.ModelIndexer[modelName].addRange(pair)
        ModelManager.Index+= n

    @staticmethod
    def createJitNode(modelName):
        pair = [ModelManager.Index, ModelManager.Index + n - 1]
        ModelManager.ModelIndexer[modelName].addRange(pair)
        ModelManager.Index+= n

