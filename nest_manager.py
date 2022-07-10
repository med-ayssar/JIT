from jit.wrapper.module_wrapper import ModuleWrapper


class NestManager():
    """ The main class for starting the JIT Wrapper around the NEST module.
    """

    def __init__(self, moduleName: str):
        """Initialize function.

            Parameters
            ----------
            moduleName: the name of the module to wrapp.
        """
        self.jit = ModuleWrapper(moduleName, "nest")

    def add_module(self, module_name: str):
        """ Append new submodules to main wrapped module.

            Parameters
            ----------
            moduleName: the name of the submodule to append.
        """
        suffix = ".".join(module_name.split(".")[1:])
        self.jit.__dict__[suffix] = ModuleWrapper(f"jit.{suffix}", module_name)

    def get_wrapper(self) -> ModuleWrapper:
        """ Return the wrapper of the targeted module.

            Returns
            --------
            ModuleWrapper:
                Object representing the wrapped targeted module.
        """
        return self.jit
