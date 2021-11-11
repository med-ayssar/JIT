from jit.wrapper.module_wrapper import ModuleWrapper


class NestManager():
    def __init__(self, moduleName):
        self.jit = ModuleWrapper(moduleName, "nest")

    def add_module(self, module_name):
        suffix = ".".join(module_name.split(".")[1:])
        self.jit.__dict__[suffix] = ModuleWrapper(f"jit.{suffix}", module_name)

    def get_wrapper(self):
        return self.jit
