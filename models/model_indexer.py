import numpy as np
class ModelIndexer:
    def __init__(self, name):
        self.name = name
        self.ranges = []
        self.intervalMap = {}

    def addRange(self, newRange):
        self.ranges.append(newRange)

    def flatten(self):
        res = []
        for pair in self.ranges:
            res.extend(pair)
        return res

    def toString(self):
        allIndices = self.flatten()
        return f"{self.name} can be found at these positions in ModelManager: {allIndices}"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def addNestIds(self, x, y):
        if x in self.ranges:
            self.intervalMap[tuple(x)] = y

    def getNestIdsAt(self, x):
        for interval in self.ranges:
            if x[0]>= interval[0] and x[1]<= interval[1]:
                nestIdsInterval = self.intervalMap[tuple(interval)]
                start = nestIdsInterval[0] + (x[0] - interval[0])
                end = start + x[1] - x[0]
                ids = list(range(start, end))
                return ids
                

