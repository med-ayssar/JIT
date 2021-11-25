from multiprocessing import Process


class JitThread():
    def __init__(self, funcToRun, sharedMemoryObj):
        self.process = Process(target=runThread, daemon=True,
                               args=(funcToRun, sharedMemoryObj))

    def join(self):
        self.process.join()

    def start(self):
        self.process.start()


def runThread(func, sharedObj):
    func(sharedObj)
