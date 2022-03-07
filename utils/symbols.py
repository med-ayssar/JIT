import re

symbolTable = [

    {
        "pattern": "__resolution",
        "replaceWith": "resolution",
        "source": "double resolution",
        "hasArgs": False,
        "nestKey": "resolution",
        "isConstant": True,



    },
    {
        "pattern": "\(\([0-9]+\) \+ \([0-9]+\) \* nest::get_vp_specific_rng\( get_thread\(\) \)->drand\(\)\)",
        "replaceWith": "uniform_value",
        "hasArgs": True,
        "getArgs": lambda string: re.findall('[0-9]+', string),
        "source": "double uniform_value",
        "nestKey": "random.uniform",
        "isConstant": False,
        "args": ["offset", "scale"]
    },
    {
        "pattern": "\(\([0-9]+\) \+ \([0-9]+\) \* normal_dev_\( nest::get_vp_specific_rng\( get_thread\(\) \) \)\)",
        "replaceWith": "normal_value",
        "hasArgs": True,
        "getArgs": lambda string: re.findall('[0-9]+', string),
        "source": "double normal_value",
        "nestKey": "random.nomral",
        "isConstant": False,
        "args": ["mean", "std"]
    }


]


class SymbolConverter:
    def __init__(self):
        self.argsHandler = []
        self.declarations = []
        self.constructorArgs = []

    def convertSymbols(self, cpp_code):
        for symbol in symbolTable:
            pattern = symbol["pattern"]
            matches = re.findall(pattern, cpp_code)
            baseName = symbol["replaceWith"]
            count = 0
            if symbol["isConstant"]:
                self.hasConvertedSymbols = True
                cpp_code = re.sub(pattern,  baseName, cpp_code)
                declaration = symbol["source"]
                self.declarations.append(declaration)
                self.constructorArgs.append("\"resolution-> None\"")
                self.argsHandler.append(("resolution", None))
            else:

                for match in matches:
                    self.hasConvertedSymbols = True
                    newSymbol = f"{baseName}_{count}"
                    cpp_code = re.sub(pattern,  newSymbol, cpp_code, 1)
                    source = symbol["source"]
                    declaration = f"{source}_{count}"
                    self.declarations.append(declaration)
                    if symbol["hasArgs"]:
                        args = symbol["getArgs"](match)
                        self.argsHandler.append((symbol["nestKey"], list(map(lambda x: float(x), args))))
                        symbolArgs = list(zip(symbol["args"], args))
                        symbolArgs = list(map(lambda x: f"{x[0]}={x[1]}", symbolArgs))
                        constructorArg = f"\"{newSymbol}->{symbolArgs}\""
                        self.constructorArgs.append(constructorArg)
                    count += 1
                count = 0
        return cpp_code, self.declarations, self.constructorArgs

    def getArgsHandler(self):
        return self.argsHandler

    
