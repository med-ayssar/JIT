import os
from jit.models.model_handle import ModelHandle
from jit.utils.nest_config import NestConfig
from loguru import logger


class ModelQuery():
    def __init__(self, neuron_name):
        self.nestml_folders = NestConfig.get_nestml_path()
        self.libs = NestConfig.get_module_lib_path()
        self.neuron = neuron_name

    def find_model_in_nestml(self):
        path_to_nestml = get_neuron_nestml_path(
            self.neuron, self.nestml_folders)
        if path_to_nestml is not None:
            return  ModelHandle(self.neuron, path_to_nestml, False)
        return None

    def find_model_in_lib(self):
        paths = NestConfig.get_module_lib_path()
        for p in paths:
            for file in os.listdir(p):
                if file.endswith(".so"):
                    lib = os.path.join(p, file)
                    neurons = get_neurons_in_lib(lib)
                    if self.neuron in neurons:
                        return ModelHandle(self.neuron, lib, True)
        return None

    def get_model_handle(self):
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


def get_neurons_name(path_to_nestml):
    if not os.path.isfile(path_to_nestml):
        raise FileNotFoundError(f"{path_to_nestml} doesn\'t exist")
    else:
        import re
        models = ""
        with open(path_to_nestml, 'r') as nestml:
            models = nestml.read()

        pattern = r'neuron\s+\w+:'
        found_models = re.findall(pattern, models)
        combine_mutli_whitespaces = re.compile(r"\s+")

        found_models = [combine_mutli_whitespaces.sub(
            " ", m) for m in found_models]
        found_models = [m.split()[1].replace(":", "") for m in found_models]
        return found_models


@logger.catch
def get_neuron_nestml_path(neuron_name, nestmls_path):
    for path in nestmls_path:
        for file in os.listdir(path):
            nestml_file = os.path.join(path, file)
            found = get_neurons_name(nestml_file)
            if neuron_name in found:
                return path
    return None


@logger.catch
def get_neurons_in_lib(lib_path):
    import subprocess
    proc1 = subprocess.Popen(
        ['nm', '--demangle', lib_path], stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(['grep', '-o', 'nest::[a-z,_]*::Parameters_'],
                             stdin=proc1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc2.communicate()
    if len(err) == 0 and len(out) > 0:
        neurons_name = out.decode("ascii").split("\n")
        neurons_name = [x.split("::")[1] for x in neurons_name if len(x) > 1]
        return set(neurons_name)
    else:
        return []
