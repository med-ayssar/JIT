import os


class NestConfig():
    """Configure the paths where to find the custom external models"""
    nest_prefix = None
    build_path = None
    nestml_path = None
    libs_path = None
    ModelManagerCapacity = 3

    @staticmethod
    def reset(nest_install_prefix):
        """Reset the provided paths to the defaults paths.

            Parameters
            ----------
            nest_install_prefix: str
                path to nest

        """
        if nest_install_prefix is None:
            raise TypeError("nest_install_prefix can\'t be a None")

        NestConfig.nest_prefix = nest_install_prefix
        NestConfig.build_path = os.path.join(os.getcwd(), "build")
        NestConfig.nestml_path = [os.path.join(os.getcwd(), "nestml")]
        NestConfig.libs_path = [os.path.join(
            nest_install_prefix, "lib", "nest")]

    @staticmethod
    def add_module_lib_path(path):
        """ Add library to install.

            Parameters
            ----------
            path: str
                path to the library

        """
        NestConfig.libs_path.append(path)

    @staticmethod
    def add_nestml_path(path):
        """ Add folder of NESTML files to install.

            Parameters
            ----------
            path: str
                path to the NESTML folder.

        """
        NestConfig.nestml_path.append(path)

    @staticmethod
    def get_module_lib_path():
        """ Get knows paths of libraries.

               Returns
               -------
               list[str]:
                   list of paths

           """
        return NestConfig.libs_path

    @staticmethod
    def get_nestml_path():
        """ Get knows paths of NESTML folders

            Returns
            -------
            list[str]:
                list of paths

        """
        return NestConfig.nestml_path

    @staticmethod
    def set_build_path(path):
        """ Set path where to store the built library.

            Parameters
            ----------
            str:
                build path.
        """
        NestConfig.build_path = path
