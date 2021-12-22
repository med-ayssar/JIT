from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager


class SimulateHelper:
    def __init__(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False

    def waitForThreads(self):
        for thread in ModelManager.Threads:
            thread.join()
            if thread.modelName in ModelManager.ThreadsState:
                state = ModelManager.ThreadsState[thread.modelName]
                if state["hasError"]:
                    values = [thread.modelName]
                    values.extend(state.values())
                    self.report.append(values)
                    self.reportErrors[thread.modelName] = {
                        "phase": state["stage"],
                        "Failure Message": state["msg"]
                    }

                self.error_occured = True

    def installModules(self):
        for module in ModelManager.Modules:
            try:
                ModelManager.Nest.Install(module)
            except Exception as exp:
                self.reportErrors[module] = {
                    "phase": "Install",
                    "Failure Message": str(exp)
                }
                self.error_occured = True

    def convertToNodeCollection(self):
        for ncp in ModelManager.NodeCollectionProxy:
            ncp.toNodeCollection()
