import sys
from importlib import import_module
from inspect import getmembers, isfunction, ismethod, ismodule
from wrapper.nest_wrapper import NestWrapper
from wrapper.wrappers import to_wrap

class ModuleWrapper():
    def __init__(self, parent, module_to_add):

        self.__dict__["module"] = parent
        self.__dict__["wrapped_module_name"] = module_to_add
        try:
            self.__dict__[module_to_add] = import_module(module_to_add)
        except:
            exit(sys.exc_info())
        
        added_module = self.__dict__[module_to_add]

        nest_functions = getmembers(added_module, isfunction)
        nest_methods = getmembers(added_module, ismethod)
        nest_module = getmembers(added_module, ismodule)
        # insert nest functions
        self.__wrapp_calls(nest_functions)
        # insert nest methodes
        self.__wrapp_calls(nest_methods, True)
        # insert module
        for module in nest_module:
            m = parent + f".{module[0]}"
            sys.modules[m] = module[1]

    def __wrapp_calls(self, iterator, isMethod=False):
        for item in iterator:
            func_wrapper = None
            prefix = self.__dict__["wrapped_module_name"]
            func_name = f"{prefix}.{item[0]}"
            if func_name in to_wrap:
                func_wrapper = to_wrap[func_name](item[1], isMethod).wrapped_func
            else:
                func_wrapper = NestWrapper(item[1], isMethod).wrapped_func
            #func_wrapper =  NestWrapper(item[1], isMethod).wrapped_nest_func
            self.__dict__[item[0]] = func_wrapper
            #setattr(self, item[0], wrapped_nest_func)

    
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

        
