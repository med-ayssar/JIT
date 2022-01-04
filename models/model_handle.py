from sys import stderr, stdout
from jit.utils.nest_config import NestConfig as config
import os
import platform
from pynestml.frontend.pynestml_frontend import to_nest, install_nest, init_predefined
from jit.utils.create_report import CreateException, CreateState
from pynestml.exceptions.generated_code_build_exception import GeneratedCodeBuildException
from pynestml.utils.model_parser import ModelParser
from pynestml.utils.logger import LoggingLevel, Logger


class ModelHandle():
    def __init__(self, name, model_path, is_lib=False, code=None):
        self.neuron = name
        self.moduleName = f"{self.neuron}module"
        self.path = model_path
        self.is_lib = is_lib
        self.target = os.path.join("/tmp", "nestml", "generated", self.neuron)
        self.stdoutPath = os.path.join(self.target, "output.txt")
        self.stderrPath = os.path.join(self.target, "error.txt")
        self.build_path = os.path.join(os.getcwd(), "build", self.neuron)
        self.lib_path = os.path.join(self.build_path, "lib", "nest")
        self.isValid = False
        self.code = code

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
            to_nest(input_path=self.path, target_path=self.target, module_name=self.moduleName)
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

    def getModelDeclaredVariables(self):
        init_predefined()
        Logger.init_logger(LoggingLevel.INFO)
        astNeuron = ModelParser.parse_neuron(self.code)
        declaredVariables = {}
        declaredVariables.update(self.__extractVariables(astNeuron.get_state_blocks))
        declaredVariables.update(self.__extractVariables(astNeuron.get_parameter_blocks))
        return declaredVariables

    def __extractVariables(self, modelBlockFunc):
        blocks = modelBlockFunc()
        if not isinstance(blocks, list):
            blocks = [blocks]
        variables = {}
        for stateBlock in blocks:
            for dec in stateBlock.get_declarations():
                for variable in dec.get_variables():
                    expression = dec.get_expression()
                    if expression.__class__.__name__ == "ASTSimpleExpression":
                        variables[variable.get_name()] = expression.get_numeric_literal()
                    elif hasattr(expression, "unary_operator") and expression.unary_operator.is_unary_minus:
                        literal = - expression.expression.get_numeric_literal()
                        variables[variable.get_name()] = literal
                    else:
                        raise RuntimeError("ModelHandle doesn't know how to handle this case")

        return variables
