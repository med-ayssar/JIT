from modulefinder import Module
import sys
from importlib import import_module
from inspect import getmembers, isclass, isfunction, ismethod, ismodule
from jit.wrapper.wrappers import to_wrap


class ModuleWrapper:
    """Manages the Wrapping workflow for the targeted NEST objects (i.e., functions and classes).
    """

    def __init__(self, parent: str, module_to_add: str):
        """Initialize function.

            Parameters
            ----------
            parent: the root module name.
            module_to_add: name of the submodule to add to the parent module.
        """
        self.__dict__["module"] = parent
        self.__dict__["wrapped_module_name"] = module_to_add
        try:
            self.__dict__[module_to_add] = import_module(module_to_add)
        except ModuleNotFoundError:
            exit(sys.exc_info())
        added_module = self.__dict__[module_to_add]

        nest_functions = getmembers(added_module, isfunction)
        nest_methods = getmembers(added_module, ismethod)
        nest_module = getmembers(added_module, ismodule)
        nest_classes = getmembers(added_module, isclass)
        # insert nest functions
        self.__wrapp_calls(nest_functions)
        # insert nest methodes
        self.__wrapp_calls(nest_methods, True)
        # insert nest classes
        self.__wrapp_module_Classes(nest_classes)
        # insert module
        for module in nest_module:
            m = parent + f".{module[0]}"
            sys.modules[m] = module[1]

    def __wrapp_calls(self, iterator, isMethod: bool = False):
        """ Wrap function and methods from the targeted module.

            Parameters
            ----------
            iterator: list of callables.
            isMethod: indicate if the callables are either functions or methods.
        """
        for item in iterator:
            func_wrapper = None
            prefix = self.__dict__["wrapped_module_name"]
            func_name = f"{prefix}.{item[0]}"
            if func_name in to_wrap:
                func_wrapper = to_wrap[func_name](
                    item[1], self.get_original(), isMethod).wrapped_func
            else:
                func_wrapper = item[1]
            self.__dict__[item[0]] = func_wrapper

    def __wrapp_module_Classes(self, iterator):
        """ Wrap classes from the target module.

            Parameters
            ----------
            iterator: list of classes.
        """
        for item in iterator:
            class_wrapper = None
            prefix = self.__dict__["wrapped_module_name"]
            class_path = f"{prefix}.{item[0]}"
            if class_path in to_wrap:
                class_wrapper = to_wrap[class_path](
                    item[1], self.get_original(), False).wrapped_func
            else:
                class_wrapper = item[1]
            self.__dict__[item[0]] = class_wrapper
            #setattr(self, item[0], class_wrapper)

    def __getattr__(self, k):
        module_to_add = self.__dict__["wrapped_module_name"]
        suffix = ".".join(module_to_add.split(".")[1:])
        if k == suffix:
            return self
        if k in self.__dict__:
            return self.__dict__[k]
        else:
            try:
                added_module = self.__dict__[module_to_add]
                return getattr(added_module, k)
            except KeyError:
                raise AttributeError(k)

    def __setattr__(self, k, v):
        module_to_add = self.__dict__["wrapped_module_name"]
        added_module = self.__dict__[module_to_add]
        setattr(added_module, k, v)

    def get_original(self) -> Module:
        """ Return the targeted module

        Returns
        --------
        Module
            The original NEST module
        """
        module = self.__dict__["wrapped_module_name"]
        added_module = self.__dict__[module]
        return added_module
