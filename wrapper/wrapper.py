import functools


class Wrapper:
    """Interface defining the core functionalities to wrap the targeted NEST objects"""

    def __init__(self, func, original_module, isMethode: bool = False, disable: bool = False):
        """Initialize function.

            Parameters
            ----------
            func: target NEST object.
            original_module: NEST module.
            isMethode: indicate if the targeted NEST is function or method.
            disable: to skip the execution of the targeted NEST function/method.

        """
        self._isMethod = isMethode
        self._disabled = disable
        setattr(self, "wrapped_func", self.__wrapper(func))
        self.func = func

    def before(self, *args, **kwargs):
        """ Preprocessing of the input parameters of the targeted NEST function.

            Parameters
            ----------
            args: arguments  tuple as definined in te targeted NEST function.
            kwargs: Keyword arguments as definined in te targeted NEST function.

            Returns
            -------
            args:
                modified arguments.
            kwargs:
                modified Keyword arguments.

        """

        return args, kwargs

    def after(self, *res):
        """ Postprocessing of the output of the targeted NEST function.

            Parameters
            ----------
            res: the output tuple of the NEST function.

        """
        if not self._isMethod:
            return res[0]

    def main_func(self, *args, **kwargs):
        """Execute the targeted NEST function.

            Parameters
            ----------
            args: Parameters that are defined in the targeted NEST function.
            kwargs: keyworded variables that are defined in the targeted NEST function.
        """
        return self.func(*args, **kwargs)

    @staticmethod
    def wrapps_one():
        """Indiciate if the wrapper wraps one or many targeted functions.

            Returns
            -------
            bool
                True, if the wrapper wraps exactly one targeted function.

        """
        return True

    @ staticmethod
    def getName():
        """Indiciate the name of the NEST targeted function.
            If the return of :meth:`wrapps_one` is true, the the function should return only a string, otherwise a list of strings.

            Returns
            -------
            (str, list[str])
                the name of the NEST targeted function.

        """
        return "function_not_selected"

    def __wrapper(self, func):
        """Wrap the NEST targeted function.

            Parameters
            ----------
            func: the targeted NEST function


            Returns
            -------
            Wrapper
                the Wrapper object of the NEST function

        """
        @functools.wraps(func)
        def call_func(*args, **kwargs):
            if not self._disabled:
                args, kwargs = self.before(*args, **kwargs)
                if self._isMethod:
                    self.main_func(*args, **kwargs)
                    self.after()
                else:
                    res = self.main_func(*args, **kwargs)
                    return self.after(res)
        return call_func
