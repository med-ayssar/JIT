
from pynestml.codegeneration.nest_cpp_printer import NestCppPrinter
from jinja2 import Environment, BaseLoader, FileSystemLoader
import os
import re
import sys
from jit.utils.symbols import SymbolConverter
from jit.models.model_manager import ModelManager


class JitModelParser:
    modelTemplate = os.path.join(os.path.dirname(__file__), 'templates')

    def __init__(self, node, codeGenerator):
        self.name = node.get_name()
        self.stateBlocks = node.get_state_blocks()
        self.paramBlocks = node.get_parameter_blocks()
        self.type = "neuron" if node.__class__.__name__ == "ASTNeuron" else "synapse"
        self.hasParam = len(self.paramBlocks.declarations) > 0 if self.paramBlocks else False
        self.hasState = len(self.stateBlocks.declarations) > 0 if self.stateBlocks else False
        self.printer = NestCppPrinter(node, codeGenerator)
        self.symbolsConverter = SymbolConverter()
        self.data = {"name": self.name, "hasParam": self.hasParam, "hasState": self.hasState}
        self.setCallables()
        self.setStructs()
        self.setConstructorBody()
        self.setGetterAndSetter()
        self.setPrivateFields()

    def getCppCode(self):
        loader = FileSystemLoader(self.__class__.modelTemplate)
        env = Environment(loader=loader)
        template = env.get_template("model.jinja2")
        return template.render(self.data)

    def setGetterAndSetter(self):
        self.data["getterAndSetter"] = self.printer.print_getter_setter(["State", "Parameters"])

    def setCallables(self):
        callables = []
        functions = self.printer.print_functions()
        callables.extend(functions.values())
        self.data["callables"] = callables

    def setStructs(self):
        if self.hasState:
            stateStruct = self.printer.print_state_struct()
            stateStruct = re.sub("State_\(\);", "State_(){};", stateStruct)
            self.data["state"] = stateStruct

        if self.hasParam:
            paramStruct = self.printer.print_parameters_struct()
            paramStruct = re.sub("Parameters_\(\);", "Parameters_(){};", paramStruct)
            self.data["parameters"] = paramStruct

    def setConstructorBody(self):
        decs = self.printer.print_default_constructorBody()
        newCode, declarations, args = self.symbolsConverter.convertSymbols(decs)
        self.data["args"] = ",".join(args)
        if len(declarations) > 0:
            declarations = ", ".join(declarations)
            self.data["ConstructorParams"] = declarations
        else:
            self.self.data["ConstructorParams"] = ""
        self.data["body"] = newCode

    def setPrivateFields(self):
        if self.hasState:
            stateInstance = self.printer.print_struct_instance("State")
            self.data["stateInstance"] = stateInstance

        if self.hasParam:
            paramInstance = self.printer.print_struct_instance("Parameters")
            self.data["paramInstance"] = paramInstance

    def toCPP(self, toFile=True, outputPath=None):
        cppCode = self.getCppCode()
        import os
        path = os.path.join(os.getcwd(), "toDelete", "code.cpp")
        if toFile:
            if outputPath is None:
                import os
                outputPath = os.path.join(os.getcwd(), f"{self.name}.cpp")

            with open(outputPath, "w+") as cpp:
                cpp.write(cppCode)
            return
        else:
            return cppCode

    def __extractVariables(self, blocks):
        variables = []
        if blocks:
            if not isinstance(blocks, list):
                blocks = [blocks]
            for stateBlock in blocks:
                for dec in stateBlock.get_declarations():
                    decVars = [var.get_name() for var in dec.get_variables()]
                    variables.extend(decVars)
        return variables

    def getVariables(self):
        stateVars = self.__extractVariables(self.stateBlocks)
        paramVars = self.__extractVariables(self.paramBlocks)
        return stateVars + paramVars

    def getPyInstance(self):
        cppCode = self.getCppCode()

        import cppyy
        cppyy.cppdef(cppCode)
        className = self.name.upper()
        clz = getattr(cppyy.gbl, className)
        constructorArgs = self.getValues(self.symbolsConverter.getArgsHandler())
        instance = clz(*constructorArgs)
        setattr(instance, "declaredVarialbes", self.getVariables())
        setattr(instance, "name", self.name)
        setattr(instance, "type", self.type)
        return instance

    def getValues(self, argsHandler):
        values = []
        for arg in argsHandler:
            if arg[0] == "resolution":
                values.append(ModelManager.Nest.resolution)
            elif arg[0] == "random.uniform":
                offset = arg[1][0]
                scale = arg[1][1]
                uniform = ModelManager.Nest.random.uniform()
                value = offset + scale * uniform
                values.append(value.GetValue())
            else:
                mean = arg[1][0]
                std = arg[1][1]
                value = ModelManager.Nest.random.normal(mean, std)
                values.append(value.GetValue())
        return values
