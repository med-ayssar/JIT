import functools
class Wrapper:
    def __init__(self, func, isMethode=False, disable=False):
        self._isMethode = isMethode
        self._disabled = disable
        setattr(self, "wrapped_func", self.__wrapper(func))


    def before(self, *args, **kwargs):
        return args, kwargs

    def after(self, *res):
        if not self._isMethode:
            return res[0]

    @staticmethod
    def wrapps_one():
        return True

    def __wrapper(self, func):
        @functools.wraps(func)
        def call_func(*args, **kwargs):
            if not self._disabled:
                args, kwargs = self.before(*args, **kwargs)
                if self._isMethode:
                    func(*args, **kwargs)
                    self.after()
                else:
                    res = func(*args, **kwargs)
                    return self.after(res)
        return call_func



            


        
        