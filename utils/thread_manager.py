from multiprocessing import Process
from jit.models.model_manager import ModelManager
from jit.utils.create_report import CreateException


class JitThread():
    def __init__(self, modelName, funcToRun, options):
        self.process = Process(target=self.run, name=modelName, daemon=False, args=(funcToRun, options))
        self.modelName = modelName

    def join(self):
        self.process.join()
    def terminate(self):
        self.process.terminate()

    def start(self):
        self.process.start()

    def run(self, func, options):
        error_occured = False
        try:
            func(options)
        except CreateException as exp:
            # store error
            ModelManager.ThreadsState[self.modelName] = exp.state.toDict()
            error_occured = True
        state = "failed" if error_occured else "finished"
        print(f"Process<{self.modelName}> has {state}, run nest.Simulate() to finish with main process")
