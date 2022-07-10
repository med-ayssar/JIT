from jit import nest
import numpy as np
import os
import unittest



class NestLogarithmicFunctionTest(unittest.TestCase):
    """Sanity test for the predefined logarithmic functions ln() and log10()"""

    def test_logarithmic_function(self):
        MAX_SSE = 1E-12

    
        nest.set_verbosity("M_ALL")

        nest.ResetKernel()
        

        nrn = nest.Create("logarithm_function_test")
        mm = nest.Create("multimeter")

        ln_state_specifier = "ln_state"
        log10_state_specifier = "log10_state"
        mm.set({"record_from": [ln_state_specifier, log10_state_specifier, "x"]})

        nest.Connect(mm, nrn)

        nest.Simulate(100.0)

        timevec = mm.get("events")["x"]
        ln_state_ts = mm.get("events")[ln_state_specifier]
        log10_state_ts = mm.get("events")[log10_state_specifier]
        ref_ln_state_ts = np.log(timevec - 1)
        ref_log10_state_ts = np.log10(timevec - 1)

        assert np.all((ln_state_ts - ref_ln_state_ts)**2 < MAX_SSE)
        assert np.all((log10_state_ts - ref_log10_state_ts)**2 < MAX_SSE)

        # test that expected failure occurs

        nest.ResetKernel()
        nrn = nest.Create("logarithm_function_test_invalid")

        mm = nest.Create("multimeter")

        ln_state_specifier = "ln_state"
        log10_state_specifier = "log10_state"
        mm.set({"record_from": [ln_state_specifier, log10_state_specifier, "x"]})

        nest.Connect(mm, nrn)

        nest.Simulate(100.0)

        timevec = mm.get("events")["x"]
        ln_state_ts = mm.get("events")[ln_state_specifier]
        log10_state_ts = mm.get("events")[log10_state_specifier]
        ref_ln_state_ts = np.log(timevec - 1)
        ref_log10_state_ts = np.log10(timevec - 1)

        assert not np.all((ln_state_ts - ref_ln_state_ts)**2 < MAX_SSE)
        assert not np.all((log10_state_ts - ref_log10_state_ts)**2 < MAX_SSE)
