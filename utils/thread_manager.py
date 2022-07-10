from multiprocessing import Process
from jit.models.model_manager import ModelManager
from jit.utils.create_report import CreateException


class JitThread():
    """ Starts the code generation in the background"""

    def __init__(self, names, funcToRun):
        """Initialize function.
            Parameters
            ----------
            names: list[str]
                list of neurons names.
            funcToRun: Object
                callback function to run.
        """
        self.process = Process(target=self.run, name="|".join(names), daemon=False, args=(funcToRun,))
        self.names = names

    def join(self):
        """ Explicit wait for the thread."""
        self.process.join()

    def terminate(self):
        """Terminate the running thread."""
        self.process.terminate()

    def start(self):
        """Start the thread in the background."""
        self.process.start()

    def run(self, func):
        """Execute the main function.

            Parameters
            ----------
            func: Object
                main function to call.

        """
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
