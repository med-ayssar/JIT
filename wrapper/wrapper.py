import functools


class Wrapper:
    def __init__(self, func, original_module, isMethode=False, disable=False):
        self._isMethod = isMethode
        self._disabled = disable
        setattr(self, "wrapped_func", self.__wrapper(func))
        self.func = func

    def before(self, *args, **kwargs):
        return args, kwargs

    def after(self, *res):
        if not self._isMethod:
            return res[0]

    def main_func(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @staticmethod
    def wrapps_one():
        return True

    def __wrapper(self, func):
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
