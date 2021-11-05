from utils.nest_config import NestConfig
import os
class ModelQuery():
    def __init__(self, neuron_name, config):
        self.nestml = config.get_nestml_path()
        self.libs = config.get_module_lib_path()
        self.neuron = neuron_name
        

    def find_model_in_nestml(self):
        path_to_nestml = get_neuron_nestml_path(self.neuron, self.nestml)
        if path_to_nestml is not None:
            return (self.name, path_to_nestml)
        return None

    def find_model_in_lib(self):
        # check .so section file
        return None

    def get_model_handle(self):
        handle = self.find_model_in_lib()
        if handle is None:
            handle = self.find_model_in_nestml()
            if handle is None:
                raise Exception(f"The module {self.neuron} can\'t be found. \n Please check the provided nestml folder paths")
            return handle
        return handle


####################################################################################
# Helps functions for retrieving  neuron location

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

        found_models = [combine_mutli_whitespaces.sub(" ", m) for m in found_models]
        found_models = [m.split()[1] for m in found_models]

        return found_models
    
def get_neuron_nestml_path(neuron_name, nestmls_path):
    for path in nestmls_path:
        found = get_neurons_name(path)
        if neuron_name in found:
            return path
    
    return None

        