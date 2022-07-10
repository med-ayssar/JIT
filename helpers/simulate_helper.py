from types import MethodDescriptorType
from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager
import gc

from jit.models.node_collection_proxy import NodeCollectionProxy


class SimulateHelper:
    """Managing the logic behind the ``SimulateWrapper``"""

    def __init__(self):
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccurred = False

    def waitForThreads(self):
        """ Explicit call to wait for all running threads to finish.
        """
        for thread in ModelManager.Threads:
            thread.join()
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

    def installModules(self):
        """ Install the built libraries after the completion of all threads.

        """
        for model, addLibToPath in ModelManager.Modules.items():
            module = f"{model}module"
            try:
                addLibToPath()
                jitModel = ModelManager.JitModels[model]
                ModelManager.Nest.Install(module)

                if len(jitModel.alias) > 0:
                    for alias in jitModel.alias:
                        newModel = ModelManager.JitModels[alias]
                        ModelManager.Nest.CopyModel(jitModel.name, newModel.name, newModel.default)
            except Exception as exp:
                self.reportErrors[module] = {
                    "phase": "Install",
                    "Failure Message": str(exp)
                }
                self.errorOccurred = True
        ModelManager.Modules.clear()
        models = list(ModelManager.JitModels.keys())
        ModelManager.setDefaults(models)

    def convertToNodeCollection(self):
        """ Convert all `JitNodeCollection` object to `NodeCollection`.
        """
        for ncp in ModelManager.NodeCollectionProxy:
            if ncp.jitNodeCollection:
                ncp.toNodeCollection()
      

    def broadcastChanges(self):
        """ Convert a all slices of a `JitNodeCollection` object to `NodeCollection`.
        """
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
        """ Print a report of the installed new models.
        """
        if len(self.reportErrors) > 0:
            errorSummary = "While processing the models, the following errors have occurred:\n" + str(self.reportErrors)
            print(errorSummary)
        # print Create summary
        print(self.report)

    def mustAbort(self):
        """ Checks if errors occurred during the connect call.

        Returns
        -------
        bool:
            True, if an error has occurred.

        """
        return self.errorOccurred

    def reset(self):
        """ Reset the state of the report printer.
        """
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccurred = False

    def deleteJitModels(self):
        """ delete all stored JitModels.
        """
        ModelManager.JitModels.clear()
