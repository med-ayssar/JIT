from sys import stderr, stdout

from jit.utils.nest_config import NestConfig as config
import os
import platform
from jit.models.model_manager import ModelManager
from pynestml.frontend.pynestml_frontend import generate_code, configure_front_end, get_parsed_models, code_generator_from_target_name, builder_from_target_name
from jit.utils.create_report import CreateException, CreateState
from pynestml.exceptions.generated_code_build_exception import GeneratedCodeBuildException
from jit.utils.jit_model_parser import JitModelParser
from pynestml.frontend.frontend_configuration import FrontendConfiguration


class ModelHandle():
    """Handles the source of the Model. The class may either trigger the code generation pipeline to register the NESTML models, or simply register the existing library containing the model.
    """

    def __init__(self, name, model_path=None, is_lib=False):
        """Initialize function.

            Parameters
            ----------
            name: str
                the name of the model to load
            model_path: str
                the path where to find the model in the file system
            is_lib: bool
                indicate if the path of the model points to a NESTML file or a library.
        """
        self.neuron = name
        self.moduleName = f"{self.neuron}module"

        self.is_lib = is_lib
        self.target = os.path.join("/tmp", "nestml", "generated", self.neuron)
        self.path = os.path.join(self.target, f"{self.neuron}.nestml") if model_path is None else model_path
        self.stdoutPath = os.path.join(self.target, "output.txt")
        self.stderrPath = os.path.join(self.target, "error.txt")
        self.build_path = os.path.join(os.getcwd(), "build")
        self.lib_path = os.path.join(self.build_path)
        self.isExternal = True if "nest/lib" not in model_path else False
        self.options = None

    def add_module_to_path(self):
        """ Add the library path to the SLI environment.
        """
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
        """ Trigger the code generation pipeline for creating the C++ code
        """
        try:
            hasErrors = generate_code(codeGenerator=self.codeGenerator, neurons=self.neurons, synapses=self.synapses)
            if hasErrors:
                raise Exception("Error(s) occurred while generating code")
        except Exception as exp:
            state = CreateState()
            state.setGenerationState(False)
            msg = str(exp)
            raise CreateException(state, msg)

    def _build(self):
        """ Trigger the build of the created C++ code. 
        """
        try:
            # pre-condition of install_nest function
            if not os.path.exists(self.build_path):
                os.makedirs(self.build_path)

            if not os.path.exists(self.target):
                os.makedirs(self.target)

            stdout = open(self.stdoutPath, "w")
            stderr = open(self.stderrPath, "w")
            builder = builder_from_target_name(FrontendConfiguration.get_target_platform(), options=self.options)
            builder.build(stderr=stderr, stdout=stdout)

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
        """ Trigger the complete code generation pipeline.
        """
        if not self.is_lib:
            self._generate_code()
            self._build()
        else:
            self.add_module_to_path()

    def add_params(self, funcName, args):
        """ Cache the provided parameters for the targeted NEST function

            Parameters
            ---------
            funcName: str
                the name of the targeted NEST function
            args: Tuple
                the provided paramters to the NEST function
        """
        self.params[funcName] = args

    def processModels(self, options=None):
        """Parse the NESTML model

            Parameters
            ---------
            options: dict
                the code generation options
        """
        self.setupFrontEnd(options)

        neuronsAst, synapsesAst, errors_occurred = get_parsed_models()
        if errors_occurred:
            raise Exception("Error(s) occurred while process_nestml_filesing the model")
        models = neuronsAst + synapsesAst
        for model in models:
            name = model.get_name()
            ModelManager.ParsedModels[name] = model

        codeGenerator = code_generator_from_target_name(FrontendConfiguration.get_target_platform(),
                                                        options=FrontendConfiguration.get_codegen_opts())
        neurons = [n.clone() for n in neuronsAst]
        synapses = [s.clone() for s in synapsesAst]
        neurons, synapses = codeGenerator.transform(neurons, synapses)

        self.options = options
        self.codeGenerator = codeGenerator
        self.neurons = neurons
        self.synapses = synapses

    def setupFrontEnd(self, options):
        """Prepare the code generation options.

            Parameters
            ---------
            options: dict
                the code generation options
        """
        # pre-condition of install_nest function
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)

        configure_front_end(input_path=self.path, target_path=self.target,  install_path=self.build_path,
                            module_name=self.moduleName, codegen_opts=options, target_platform="NEST")
        self.options = options

    def getModels(self, mtype="neuron"):
        """Generate the partial version of the NESTML model.
            Parameters
            ---------
            mytpye: str
                the type of the model. Either neuron or synapse.

            Returns
            -------
            Model:
                the partial version of the NESTML model.

        """
        models = []
        for model in self.neurons + self.synapses:
            modelInstnace = JitModelParser(model, self.codeGenerator)
            models.append(modelInstnace.getPyInstance())
        return models

    @staticmethod
    def getCodeGenerator(options):
        """Create an instance of the CodeGenerator

            Parameters
            ---------
            options: dict
                the code generation options
        """
        return code_generator_from_target_name(FrontendConfiguration.get_target_platform(),
                                               options=options)

    @staticmethod
    def getCodeGenerationOptions(neuron, synapse):
        """Prepare the code generation options.

            Parameters
            ---------
            neuron: str
                the neuron name
            synapse: str
                the synapse name
        """
        codegenOpts = {
            "neuron_parent_class": "StructuralPlasticityNode",
            "neuron_parent_class_include": "structural_plasticity_node.h",
            "neuron_synapse_pairs": [{"neuron": neuron.get_name(),
                                      "synapse": synapse.get_name(),
                                      "post_ports": ["post_spikes"]}],

        }
        return codegenOpts
