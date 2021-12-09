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
        error_occured = False
        try:
            func(sharedObj)
        except CreateException as exp:
            # store error
            ModelManager.ThreadsState[self.modelName] = exp.state.toDict()
            error_occured = True
        state = "failed" if error_occured else "finished" 
        print(f"Process<{self.modelName}> {state}, run nest.Simulate() to finish with main process")
