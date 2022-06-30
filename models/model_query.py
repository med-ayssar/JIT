import os
from statistics import mode
from jit.models.model_handle import ModelHandle
from jit.utils.nest_config import NestConfig
from loguru import logger
import warnings


class ModelQuery():
    """Search for the model in the file system either in a NESTML format or in a library and return its handle.
    """

    def __init__(self, model_name, mtype="neuron", onlyNeuron=True):
        """Initialize function.

            Parameters
            ----------
            model_name: str
                the name of the model to load,
            mtype: str
                the type of the model. Either neuron or synapse.
            onlyNeuron: bool
                indicate if the model_name is the prefix of the existing models. (must check this!)
        """
        self.nestml_folders = NestConfig.get_nestml_path()
        self.libs = NestConfig.get_module_lib_path()
        self.neuron = model_name
        self.type = mtype
        self.ChangedName = False
        self.onlyNeuron = onlyNeuron

    def find_model_in_nestml(self):
        """Search for the model in the provided NESTML files.

            Returns
            -------
            ModelHandle:
                the handle of the NESTML file
        """
        path, code = get_neuron(self.neuron, self.nestml_folders, "neuron")
        if path is None:
            # try maybe it was synpase
            path, code = get_neuron(self.neuron, self.nestml_folders, "synapse")

        if path is not None:
            return ModelHandle(self.neuron, path, False)
        return None

    def find_model_in_lib(self):
        """Search for the model in the provided libraries.

            Returns
            -------
            ModelHandle:
                the handle of the library.
        """
        paths = NestConfig.get_module_lib_path()
        build_path = os.path.join(NestConfig.build_path)
        paths.append(build_path)
        for p in paths:
            if os.path.isdir(p):
                for libName in os.listdir(p):
                    if libName.endswith(".so"):
                        lib = os.path.join(p, libName)
                        neurons = get_neurons_in_lib(lib)
                        if self.hasModel(self.neuron, neurons):
                            expectedModuleName = f"{self.neuron}module.so"
                            if expectedModuleName != libName:
                                handle = ModelHandle(self.neuron, p, True)
                                handle.moduleName = libName[:-3]
                                return handle
                            return ModelHandle(self.neuron, p, True)
        return None

    def hasModel(self, modelName, foundModels):
        """ Check of the model is in the list of foud models.

            Parameters
            ----------
            modelName: str
                the required model.

            foundModels: list[str]
                the list of found models.

            Returns
            -------
            bool:
                True, if the model in the list of found models.
        """
        for foundModel in foundModels:
            if self.onlyNeuron:
                if foundModel == modelName:
                    return True
                return False
            else:
                if foundModel.find(modelName) == 0:
                    if modelName != foundModel:
                        self.neuron = foundModel
                        self.ChangedName = True
                    return True
        return False

    def getModelHandle(self):
        """Search for the model in the file system.

            Returns
            -------
            ModelHandle:
                the handle of the model. Either a NESTML handle or a library handle.
        """
        handle = self.find_model_in_lib()
        if handle is None:
            handle = self.find_model_in_nestml()
            if handle is None:
                raise Exception(
                    f"The module {self.neuron} can\'t be found. \n Please check the provided nestml folder paths")
            return handle
        return handle

###################################################################################
# Helps functions for retrieving  neuron location
###################################################################################


def get_neurons_code(path_to_nestml, mtype):
    """Retrieve the model source code from the NESTML file.

            Parameters
            ----------
            path_to_nestml: str
                the location of the model in the file system.

            mtype: str
                the type of the model. Either neuron or synapse.


            Returns
            -------
            ModelHandle:
                the handle of the model. Either a NESTML handle or a library handle.
    """
    if not os.path.isfile(path_to_nestml):
        raise FileNotFoundError(f"{path_to_nestml} doesn\'t exist")
    else:
        import re
        lines = []
        with open(path_to_nestml, 'r') as nestml:
            lines = nestml.readlines()

        # extract neurons name in the nestml file
        pattern = r'{}'.format(f'{mtype}\s+\w+:')
        expression = re.compile(pattern)
        found_models = list(filter(expression.match, lines))
        models_location = [lines.index(x) for x in found_models]
        neurons = {}
        combine_mutli_whitespaces = re.compile(r"\s+")
        for i in range(len(found_models)):
            if i != len(found_models) - 1:
                start = models_location[i]
                end = models_location[i+1]
            else:
                start = models_location[i]
                end = len(lines)

            name = combine_mutli_whitespaces.sub(" ", found_models[i]).split()[
                1].replace(":", "")
            code = "".join(lines[start:end]).strip()
            neurons[name] = code

        #found_models = re.findall(pattern, models)

        #found_models = [combine_mutli_whitespaces.sub(" ", m) for m in found_models]
        #found_models = [m.split()[1].replace(":", "") for m in found_models]
        # extract the nestml code for the model

        return neurons


@logger.catch
def get_neuron(modelName, nestmls_path, mtype="neuron"):
    """ Retrieve the source code file of the model.

            Parameters
            ----------
            modelName: str
                the name of the model.
            nestmls_path: list[str]
                list of paths where to find the model in the file system.
            mtype: str
                the type of the model. Either neuron or synapse.
            Returns
            -------
            (str, str):
                The first element is the pair is the path of the NESTML model. The second element is the source code of the model.
    """
    for path in nestmls_path:
        for file in os.listdir(path):
            nestml_file = os.path.join(path, file)
            found = get_neurons_code(nestml_file, mtype)
            if modelName in found:
                return (nestml_file, found[modelName])
    return (None, None)


@logger.catch
def get_neurons_in_lib(lib_path):
    """ Retrieve the compiled models in the library.

            Parameters
            ----------
            lib_path: str
                the path of the library in the file system.

            Returns
            -------
            list[str]:
               list of found neurons in the library.
    """
    found = set()
    import subprocess
    proc1 = subprocess.Popen(['nm', '--demangle', lib_path], stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(['grep', '-o', '[A-Za-z,_][A-Za-z,_]*::Parameters_'],
                             stdin=proc1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc2.communicate()
    if len(err) == 0 and len(out) > 0:
        neurons_name = out.decode("ascii").split("\n")
        neurons_name = [x.split("::")[0] for x in neurons_name if len(x) > 1]
        found.update(set(neurons_name))

    proc1 = subprocess.Popen(['nm', '--demangle', lib_path], stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(['grep', '-o', 'nest::[A-Za-z,_][A-Za-z,_]*<nest::TargetIdentifierIndex>'],
                             stdin=proc1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc3 = subprocess.Popen(['sort', '-u'], stdin=proc2.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc3.communicate()
    if len(err) == 0 and len(out) > 0:
        synapses = out.decode("ascii").split("\n")
        synapses = [x.split("nest::")[1].split("<")[0] for x in synapses if len(x) > 1]
        found.update(synapses)

    return found
