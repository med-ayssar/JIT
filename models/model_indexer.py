class ModelIndexer:
    def __init__(self, name):
        self.name = name
        self.ranges = []

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
