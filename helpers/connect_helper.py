from urllib.parse import _NetlocResultMixinStr
from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager
from jit.models.model_handle import ModelHandle

from jit.helpers.model_helper import CopyModel
from jit.utils.utils import handle
import copy


class ConnectHelper:
    def __init__(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False

    def waitForThreads(self, threadsName):
        toRemove = []
        for thread in ModelManager.Threads:
            if any(name in threadsName for name in thread.names):
                thread.join()
                toRemove.append(thread)
                if thread.names[0] in ModelManager.ThreadsState:
                    state = ModelManager.ThreadsState[thread.names[0]]
                    if state["hasError"]:
                        values = [thread.names[0]]
                        values.extend(state.values())
                        self.report.append(values)
                        self.reportErrors[thread.names[0]] = {
                            "phase": state["stage"],
                            "Failure Message": state["msg"]
                        }

                self.error_occured = True
        # clean threads pool
        for thread in toRemove:
            thread.terminate()
            ModelManager.Threads.remove(thread)

    def installModules(self, modules):

        for model in modules:
            module = f"{model}module"
            addLibToPath = ModelManager.Modules.pop(model, None)
            if addLibToPath:
                try:

                    addLibToPath()
                    ModelManager.Nest.Install(module)

                except Exception as exp:
                    self.reportErrors[module] = {
                        "phase": "Install",
                        "Failure Message": str(exp)
                    }
                    self.error_occured = True
        
        ModelManager.setDefaults(modules)
        ModelManager.copyModels(modules)
        for copyModel, oldName, newName, newParams in CopyModel.Pending:
            if oldName not in modules:
                copyModel(oldName, newName, newParams)
                
        CopyModel.Pending.clear()


    def convertPostNeuron(self, ncp, synapseModel):
        return handle(ncp, synapseModel)

    def convertToNodeCollection(self, node):
        if node.jitNodeCollection is not None:
            initialNodes = ModelManager.getNodeCollectionProxies(node.tolist())
            for initialNode in initialNodes:
                if initialNode.jitNodeCollection:
                    initialNode.jitNodeCollection.isNotInitial = False
                    initialNode.toNodeCollection()
            ids = node.getNestIds()
            nodeCollection = ModelManager.Nest.NodeCollection(ids)
            if node.nestNodeCollection is None:
                node.nestNodeCollection = nodeCollection
            else:
                node.nestNodeCollection += nodeCollection
            node.jitNodeCollection = None

    def showReport(self):
        if len(self.reportErrors) > 0:
            errorSummary = "While processing the modules, the follwing errors have occured:\n" + str(self.reportErrors)
            print(errorSummary)
        # print Create summary
        print(self.report)

    def mustAbort(self):
        return self.errorOccured

    def reset(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False
