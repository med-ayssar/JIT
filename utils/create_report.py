from tabulate import tabulate


class CreateReport():
    """Create report for installing new models"""

    def __init__(self, tablefmt="grid"):
        """Initialize function.
            Parameters
            ----------
            tablefmt: str
                table format style.
        """
        self.headers = ["Model", "Generated", "Build", "Installed"]
        self.data = []
        self.tableFormat = tablefmt

    def __str__(self):

        table = tabulate(self.data, self.headers, tablefmt=self.tableFormat)
        output = "\n\nModels creation summary:\n" + str(table)
        return output

    def append(self, arr):
        """ Append new states to the report.

            Parameters
            ----------
            arr: list[CreateState]
                list of new states.
        """
        if len(arr) > 1:
            self.data.append(arr[:len(self.headers)])
        else:
            values = arr[:]
            values.extend(["Ok"]*3)
            self.data.append(values)


class CreateState():
    """Create new state for the report"""

    def __init__(self):
        """Initialize function.

        """
        self._generated = "ok"
        self._build = "ok"
        self._installed = "ok"
        self.hasError = False
        self.msg = None
        self.stage = None

    def setGenerationState(self, state):
        """ Set the report state for the code generation phase
            Parameters
            ----------
            state: bool
                If False, then state indicates a failing phase.
        """
        if state == True:
            self._generated = "ok"
        else:
            self.stage = "Code Generation"
            self._generated = "Failed"
            self._build = "Abort"
            self._installed = "Abort"
            self.hasError = True

    def setBuiltState(self, state):
        """ Set the report state for the building phase.
            Parameters
            ----------
            state: bool
                If False, then state indicates a failing phase.
        """
        if state == True:
            self._build = "Ok"
        else:
            self.stage = "Build"
            self._build = "Failed"
            self._installed = "Abort"
            self.hasError = True

    def toDict(self):
        """ Convert the State instance to a dictionary object.

            Returns
            -------
            dict: 
                State class in dictionary object.

        """
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
    """ Defines an exception of the CreateWrapper when using threads."""

    def __init__(self, state, msg):
        """Initialize function.
            Parameters
            ----------
            state: bool
                True, if no failure has occurred before.
            msg:
                exception message.
        """
        self.state = state
        self.message = msg
        self.state.setFailureMsg(msg)
        super().__init__(msg)
