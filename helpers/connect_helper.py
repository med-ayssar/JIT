from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager


class ConnectHelper:
    def __init__(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccured = False

    def waitForThreads(self, threadsName):
        toRemove = []
        for thread in ModelManager.Threads:
            if thread.modelName in threadsName:
                thread.join()
                toRemove.append(thread)
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
        # clean threads pool
        for thread in toRemove:
            thread.terminate()
            ModelManager.Threads.remove(thread)


    def installModules(self, modules):

        for model in modules:
            module = f"{model}module"
            addLibToPath = ModelManager.Modules[model]
            try:
                addLibToPath()
                ModelManager.Nest.Install(module)
                jitModel = ModelManager.JitModels[model]
                del ModelManager.Modules[model]
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
