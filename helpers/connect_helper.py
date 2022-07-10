from jit.utils.create_report import CreateReport
from jit.models.model_manager import ModelManager
from jit.models.model_handle import ModelHandle

from jit.helpers.model_helper import CopyModel
from jit.utils.utils import handle
import copy


class ConnectHelper:
    """Managing the logic behind the ``ConnectWrapper``"""
    def __init__(self):
        """Initialize function.

        """
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccurred = False

    def waitForThreads(self, threadsName):
        """ Explicit call to wait for the thread to finish.

            Parameters
            ----------
            threadsName: str
                name of the thread
        """
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

                self.errorOccurred = True
        # clean threads pool
        for thread in toRemove:
            thread.terminate()
            ModelManager.Threads.remove(thread)

    def installModules(self, modules):
        """ Install the built libraries after the completion of the threads.

            Parameters
            ----------
            modules: list[str]
                list of modules names.

        """
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
        """ Convert a neuron instance to new instance from another model that supports the given synapse type.

            Parameters
            ----------
            ncp: NodeCollection
                a homogenous collection of nodes.
            
            synapseModel: str
                synapse model's name.
            
            Returns
            -------
            NodeCollection:
                a new node collection of instances that support the synapse model.
        """
        return handle(ncp, synapseModel)

    def convertToNodeCollection(self, node):
        """ Convert a `JitNodeCollection` object to `NodeCollection`.

            Parameters
            ----------
            node: JitNodeCollection
                a homogenous collection of nodes.
            
            
            
            Returns
            -------
            NodeCollection:
                The real representation of the model in NEST kernel.
        """
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
        """ Print a report of the installed new models.
        """
        if len(self.reportErrors) > 0:
            errorSummary = "While processing the modules, the following errors have occurred:\n" + str(self.reportErrors)
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
        """ Reset the state of the report printer
        """
        self.report = CreateReport()
        self.reportErrors = {}
        self.errorOccurred = False
