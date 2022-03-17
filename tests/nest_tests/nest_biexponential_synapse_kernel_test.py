
from jit import nest
import os
import unittest

try:
    import matplotlib
    import matplotlib.pyplot as plt
    TEST_PLOTS = True
except BaseException:
    TEST_PLOTS = False


class NestBiexponentialSynapseTest(unittest.TestCase):

    def test_biexp_synapse(self):

        nest.set_verbosity("M_ALL")

        nest.ResetKernel()

        # network construction
        
        neuron = nest.Create("biexp_postsynaptic_response")

        sg = nest.Create("spike_generator", params={"spike_times": [10., 30.]})
        nest.Connect(sg, neuron, syn_spec={"receptor_type": 1, "weight": 1000., "delay": 0.1})

        sg2 = nest.Create("spike_generator", params={"spike_times": [20., 40.]})
        nest.Connect(sg2, neuron, syn_spec={"receptor_type": 2, "weight": 1000., "delay": 0.1})

        sg3 = nest.Create("spike_generator", params={"spike_times": [25., 45.]})
        nest.Connect(sg3, neuron, syn_spec={"receptor_type": 3, "weight": 1000., "delay": 0.1})

        sg4 = nest.Create("spike_generator", params={"spike_times": [35., 55.]})
        nest.Connect(sg3, neuron, syn_spec={"receptor_type": 4, "weight": 1000., "delay": 0.1})

        i_1 = nest.Create("multimeter", params={"record_from": [
                          "g_gap__X__spikeGap", "g_ex__X__spikeExc", "g_in__X__spikeInh", "g_GABA__X__spikeGABA"], "interval": .1})
        nest.Connect(i_1, neuron)

        vm_1 = nest.Create("voltmeter")
        nest.Connect(vm_1, neuron)

        # simulate

        nest.Simulate(125.)

        # analysis

        vm_1 = nest.GetStatus(vm_1)[0]["events"]
        i_1 = nest.GetStatus(i_1)[0]["events"]
        if TEST_PLOTS:
            self.plot(vm_1, i_1)

        # verification
        final_v_m = vm_1["V_m"][-1]
        print("final V_m = " + str(final_v_m))
        MAX_ABS_ERROR = 1E-6
        assert abs(final_v_m - -64.2913308548727) < MAX_ABS_ERROR

    def plot(self, vm_1, i_1):
        fig, ax = plt.subplots(nrows=5)

        ax[0].plot(vm_1["times"], vm_1["V_m"], label="V_m")
        ax[0].set_ylabel("voltage")

        ax[1].plot(i_1["times"], i_1["g_gap__X__spikeGap"], label="g_gap__X__spikeGap")
        ax[1].set_ylabel("current")

        ax[2].plot(i_1["times"], i_1["g_ex__X__spikeExc"], label="g_ex__X__spikeExc")
        ax[2].set_ylabel("current")

        ax[3].plot(i_1["times"], i_1["g_in__X__spikeInh"], label="g_in__X__spikeInh")
        ax[3].set_ylabel("current")

        ax[4].plot(i_1["times"], i_1["g_GABA__X__spikeGABA"], label="g_GABA__X__spikeGABA")
        ax[4].set_ylabel("current")

        for _ax in ax:
            # _ax.legend()
            _ax.legend(loc="upper right")
            _ax.set_xlim(0., 125.)
            _ax.grid(True)

        for _ax in ax[:-1]:
            _ax.set_xticklabels([])

        ax[-1].set_xlabel("time")

        fig.savefig("/tmp/biexp_synapse_test.png")
