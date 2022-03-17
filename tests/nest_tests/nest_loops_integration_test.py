import os
import unittest
import numpy as np

from jit import nest


class NestLoopsIntegrationTest(unittest.TestCase):
    """
    Tests the code generation and working of for and while loops from NESTML to NEST
    """

    def test_for_and_while_loop(self):

        nest.ResetKernel()

        nrn = nest.Create("for_loop")
        mm = nest.Create("multimeter")
        mm.set({"record_from": ["V_m"]})

        nest.Connect(mm, nrn)

        nest.Simulate(5.0)

        v_m = mm.get("events")["V_m"]
        np.testing.assert_almost_equal(v_m[-1], 16.6)

        nest.ResetKernel()
        nrn = nest.Create("while_loop")

        mm = nest.Create("multimeter")
        mm.set({"record_from": ["y"]})

        nest.Connect(mm, nrn)

        nest.Simulate(5.0)
        y = mm.get("events")["y"]
        np.testing.assert_almost_equal(y[-1], 5.011)
