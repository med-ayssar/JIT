from multiprocessing import Process
from jit.models.model_manager import ModelManager
from jit.utils.create_report import CreateException


class JitThread():
    def __init__(self, names, funcToRun,):
        self.process = Process(target=self.run, name="|".join(names), daemon=False, args=(funcToRun,))
        self.names = names

    def join(self):
        self.process.join()

    def terminate(self):
        self.process.terminate()

    def start(self):
        self.process.start()

    def run(self, func):
        error_occured = False
        try:
            func()
        except CreateException as exp:
            # store error
            ModelManager.ThreadsState[self.names[0]] = exp.state.toDict()
            print(str(exp))
            error_occured = True
        state = "failed" if error_occured else "finished"
        names = "|".join(self.names)
        print(f"Process<{names}> has {state}, run nest.Simulate() to finish with main process")
