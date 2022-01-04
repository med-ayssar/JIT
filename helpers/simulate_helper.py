from types import MethodDescriptorType
from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager
import gc

from jit.models.node_collection_proxy import NodeCollectionProxy


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

        for model, addLibToPath in ModelManager.Modules.items():
            module = f"{model}module"
            try:
                addLibToPath()
                ModelManager.Nest.Install(module)
                jitModel = ModelManager.JitModels[model]
                if len(jitModel.alias) > 0:
                    for alias in jitModel.alias:
                        newModel = ModelManager.JitModels[alias]
                        ModelManager.Nest.CopyModel(jitModel.name, newModel.name, newModel.default)
            except Exception as exp:
                self.reportErrors[module] = {
                    "phase": "Install",
                    "Failure Message": str(exp)
                }
                self.error_occured = True

    def convertToNodeCollection(self):
        for ncp in ModelManager.NodeCollectionProxy:
            if ncp.jitNodeCollection:
                ncp.toNodeCollection()
        # clear Array of NodeCollectionProxy<JitNodeCollection>
        #ModelManager.NodeCollectionProxy = []

    def broadcastChanges(self):
        for ncp in gc.get_objects():
            if isinstance(ncp, NodeCollectionProxy):
                if ncp.jitNodeCollection and ncp.jitNodeCollection.isNotInitial:
                    nestIds = ncp.getNestIds()
                    nodeCollection = ModelManager.Nest.NodeCollection(nestIds)
                    if ncp.nestNodeCollection is None:
                        ncp.nestNodeCollection = nodeCollection
                    else:
                        ncp.nestNodeCollection += nodeCollection
                    ncp.jitNodeCollection = None

    def __del__(self):
        print("Simulation Ends")

    def showReport(self):
        if len(self.reportErrors) > 0:
            errorSummary = "While processing the models, the follwing errors have occured:\n" + str(self.reportErrors)
            print(errorSummary)
        # print Create summary
        print(self.report)

    def mustAbort(self):
        return self.errorOccured

    def reset(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False

    def deleteJitModels(self):
        ModelManager.JitModels.clear()