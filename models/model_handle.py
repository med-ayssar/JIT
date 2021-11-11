from jit.utils.nest_config import NestConfig as config
import os
import platform
from pynestml.frontend.pynestml_frontend import to_nest, install_nest


class ModelHandle():
    def __init__(self, name, model_path, is_lib=False):
        self.neuron = name
        self.path = model_path
        self.is_lib = is_lib
        self.target = os.path.join(os.getcwd(), "generated", self.neuron)
        self.build = os.path.join(os.getcwd(), "build", self.neuron)

    def _add_model(self, path):
        system = platform.system()
        lib_key = ""
        if system == "Linux":
            lib_key = "LD_LIBRARY_PATH"
        else:
            lib_key = "DYLD_LIBRARY_PATH"

        if lib_key in os.environ:
            os.environ[lib_key] += os.pathsep + path
        else:
            os.environ[lib_key] = path

    def _generate_code(self):
        module_name = f"{self.neuron}module"
        to_nest(input_path=self.path, target_path=self.target,
                module_name=module_name)

    def _build(self):
        # pre-condition of install_nest function
        if not os.path.exists(self.build):
             os.makedirs(self.build)
        install_nest(self.target, config.nest_prefix, self.build)

    def install(self):
        if self.is_lib:
            self._add_model(self.path)
        else:
            self._generate_code()
            self._build()
            lib_path = os.path.join(self.build, "lib", "nest")
            self._add_model(lib_path)
