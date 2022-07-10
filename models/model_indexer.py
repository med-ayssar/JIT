import numpy as np


class ModelIndexer:
    """Match the partial instances IDs with the complete real instances IDs from NEST."""

    def __init__(self, name):
        """Initialize function.

            Parameters
            ----------
            name: str
                the name of the model.
        """
        self.name = name
        self.ranges = []
        self.intervalMap = {}

    def addRange(self, newRange):
        """ Extend the range of Ids covered by the model

            Parameters
            ----------
            newRange: list[int], range 
                list of new Ids covered by the model
        """
        self.ranges.append(newRange)

    def flatten(self):
        """ Merge all Paritions of the ids of the model in one list.

            Returns
            --------
            list[int]:
                list of the Ids covered by the model.
        """
        res = []
        for pair in self.ranges:
            res.extend(pair)
        return res

    def toString(self):
        """ Represent the Indexer in a string fromat.

            Returns
            -------
            str:
                string version of the class
        """
        allIndices = self.flatten()
        return f"{self.name} can be found at these positions in ModelManager: {allIndices}"

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def addNestIds(self, x, y):
        """ Bind the partial model's Ids with the NEST generated Ids

            Parameters
            ----------
            x: list[int]
                Jit generated Ids
            y: NEST generated Ids
        """
        if x in self.ranges:
            self.intervalMap[tuple(x)] = y

    def getNestIdsAt(self, x):
        """ retrieve the NEST Ids from the certain the JIT Ids

            Parameters
            ----------
            x: list[int]
                Jit generated Ids

        """
        for interval in self.ranges:
            if x[0] >= interval[0] and x[1] <= interval[1]:
                nestIdsInterval = self.intervalMap[tuple(interval)]
                start = nestIdsInterval[0] + (x[0] - interval[0])
                end = start + x[1] - x[0]
                ids = list(range(start, end))
                return ids
