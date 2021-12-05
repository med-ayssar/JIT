from multiprocessing import Process
from jit.models.model_manager import ModelManager
from jit.utils.create_report import CreateException


class JitThread():
    def __init__(self, modelName, funcToRun, sharedMemoryObj):
        self.process = Process(target=self.run, name=modelName, daemon=False, args=(funcToRun, sharedMemoryObj))
        self.modelName = modelName

    def join(self):
        self.process.join()

    def start(self):
        self.process.start()

    def run(self, func, sharedObj):
        try:
            func(sharedObj)
        except CreateException as exp:

            ModelManager.ThreadsState[self.modelName] = exp.state.toDict()
