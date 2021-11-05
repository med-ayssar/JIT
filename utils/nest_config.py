import os


class NestConfig():
    default_install = None
    target_path = None
    nestml_path = None
    libs_path = None

    @staticmethod
    def reset(nest_install_prefix):
        if nest_install_prefix is None:
            raise TypeError("nest_install_prefix mustn\'t be a None")
        else:
            NestConfig.default_install = nest_install_prefix
        NestConfig.target_path = os.path.join(os.getcwd(), "build")
        NestConfig.nestml_path = [os.path.join(os.getcwd(), "nestml")]
        NestConfig.libs_path = [nest_install_prefix]

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
    def set_target_path(self, path):
        NestConfig.target_path = path
