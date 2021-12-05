import os


class NestConfig():
    nest_prefix = None
    build_path = None
    nestml_path = None
    libs_path = None
    ModelManagerCapacity = 3

    @staticmethod
    def reset(nest_install_prefix):
        if nest_install_prefix is None:
            raise TypeError("nest_install_prefix can\'t be a None")

        NestConfig.nest_prefix = nest_install_prefix
        NestConfig.build_path = os.path.join(os.getcwd(), "build")
        NestConfig.nestml_path = [os.path.join(os.getcwd(), "nestml")]
        NestConfig.libs_path = [os.path.join(
            nest_install_prefix, "lib", "nest")]

    @staticmethod
    def add_module_lib_path(path):
        NestConfig.libs_path.append(path)

    @staticmethod
    def add_nestml_path(path):
        NestConfig.nestml_path.append(path)

    @staticmethod
    def get_module_lib_path():
        return NestConfig.libs_path

    @staticmethod
    def get_nestml_path():
        return NestConfig.nestml_path

    @staticmethod
    def set_build_path(self, path):
        NestConfig.build_path = path
