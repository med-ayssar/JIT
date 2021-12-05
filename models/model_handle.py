from sys import stderr, stdout
from jit.utils.nest_config import NestConfig as config
import os
import platform
from pynestml.frontend.pynestml_frontend import to_nest, install_nest
from jit.utils.create_report import CreateException, CreateState
from pynestml.exceptions.generated_code_build_exception import GeneratedCodeBuildException


class ModelHandle():
    def __init__(self, name, model_path, is_lib=False, code=None):
        self.neuron = name
        self.module_name = f"{self.neuron}module"
        self.path = model_path
        self.is_lib = is_lib
        self.target = os.path.join("/tmp", "nestml", "generated", self.neuron)
        self.stdoutPath = os.path.join(self.target, "output.txt")
        self.stderrPath = os.path.join(self.target, "error.txt")
        self.build_path = os.path.join(os.getcwd(), "build", self.neuron)
        self.code = code
        self.lib_path = os.path.join(self.build_path, "lib", "nest")
        self.params = {}
        self.isValid = False

    def add_module_to_path(self):
        system = platform.system()
        lib_key = ""
        if system == "Linux":
            lib_key = "LD_LIBRARY_PATH"
        else:
            lib_key = "DYLD_LIBRARY_PATH"

        if lib_key in os.environ:
            os.environ[lib_key] += os.pathsep + self.lib_path
        else:
            os.environ[lib_key] = self.lib_path

    def _generate_code(self):
        try:
            to_nest(input_path=self.path, target_path=self.target, module_name=self.module_name)
        except Exception as exp:
            state = CreateState()
            state.setGenerationState(False)
            msg = str(exp)
            raise CreateException(state, msg)

    def _build(self):
        try:
            # pre-condition of install_nest function
            if not os.path.exists(self.build_path):
                os.makedirs(self.build_path)
            stdout = open(self.stdoutPath, "w")
            stderr = open(self.stderrPath, "w")
            install_nest(self.target, config.nest_prefix, self.build_path, stderr=stderr, stdout=stdout)

            stdout.close()
            stderr.close()

        except GeneratedCodeBuildException as exp:
            stdout.close()
            stderr.close()

            state = CreateState()
            state.setBuiltState(False)
            msg = str(exp)
            raise CreateException(state, msg)

    def build(self):
        if not self.is_lib:
            self._generate_code()
            self._build()
        else:
            self.add_module_to_path()

    def get_nest_instance(self):
        pass

    def get_neuron(self):
        return ["todo: implement proxy"]

    def add_params(self, funcName, args):
        self.params[funcName] = args
