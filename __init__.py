from jit import nest_manager as manager
from utils.nest_config import NestConfig
import builtins
import copy

# create instance of NestManager
nest_manager = manager.NestManager(__name__)

# get the real nest wrapper
nest = nest_manager.get_wrapper()

# get instance of the nest install settings
config = NestConfig

# resest all paths to default paths
config.reset(nest.ll_api.sli_func("statusdict/prefix ::"))

# keep the original implementation of builtin __import__
old_import = copy.deepcopy(builtins.__import__)

def custom_import(name,*args, **kwargs):
    if "nest." in name:
        nest_manager.add_module(name)
        #suffix = ".".join(name.split(".")[1:])
        #return nest.__dict__[suffix]
        return nest
    else:
        return old_import(name, *args, **kwargs)

builtins.__import__ = custom_import


__all__ = ['nest', 'config']