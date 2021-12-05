from tabulate import tabulate


class CreateReport():
    def __init__(self, tablefmt="grid"):
        self.headers = ["Model", "Generated", "Build", "Installed"]
        self.data = []
        self.tableFormat = tablefmt

    def __str__(self):

        table = tabulate(self.data, self.headers, tablefmt=self.tableFormat)
        output = "\n\nModels creation summary:\n" + str(table)
        return output

    def append(self, arr):
        if len(arr) > 1:
            self.data.append(arr[:len(self.headers)])
        else:
            values = arr[:]
            values.extend(["Ok"]*3)
            self.data.append(values)


class CreateState():
    def __init__(self):
        self._generated = "ok"
        self._build = "ok"
        self._installed = "ok"
        self.hasError = False
        self.msg = None
        self.stage = None

    def setGenerationState(self, state):
        if state == True:
            self._generated = "ok"
        else:
            self.stage = "Code Generation"
            self._generated = "Failed"
            self._build = "Abort"
            self._installed = "Abort"
            self.hasError = True

    def setBuiltState(self, state):
        if state == True:
            self._build = "Ok"
        else:
            self.stage = "Build"
            self._build = "Failed"
            self._installed = "Abort"
            self.hasError = True

    def toDict(self):
        return {
            "Code Generation": self._generated,
            "Build": self._build,
            "Install": self._installed,
            "hasError": self.hasError,
            "stage": self.stage,
            "msg": self.msg
        }

    def __str__(self):
        dic = self.toDict()
        return str(dic)

    def setFailureMsg(self, msg):
        self.msg = msg


class CreateException(Exception):
    def __init__(self, state, msg):
        self.state = state
        self.message = msg
        self.state.setFailureMsg(msg)
        super().__init__(msg)
