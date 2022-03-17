
from jit import nest
import os
import unittest

try:
    import matplotlib
    import matplotlib.pyplot as plt
    TEST_PLOTS = True
except BaseException:
    TEST_PLOTS = False


class NestMultiSynapseTest(unittest.TestCase):

    def test_multisynapse(self):
       
        nest.set_verbosity("M_ALL")
        nest.ResetKernel()

        # network construction

        neuron = nest.Create("iaf_psc_exp_multisynapse_neuron")

        sg = nest.Create("spike_generator", params={"spike_times": [20., 80.]})
        nest.Connect(sg, neuron, syn_spec={"receptor_type": 1, "weight": 1000., "delay": 0.1})

        sg2 = nest.Create("spike_generator", params={"spike_times": [40., 60.]})
        nest.Connect(sg2, neuron, syn_spec={"receptor_type": 2, "weight": 1000., "delay": 0.1})

        sg3 = nest.Create("spike_generator", params={"spike_times": [30., 70.]})
        nest.Connect(sg3, neuron, syn_spec={"receptor_type": 3, "weight": 500., "delay": 0.1})

        mm = nest.Create("multimeter", params={"record_from": [
                         "I_kernel1__X__spikes1", "I_kernel2__X__spikes2", "I_kernel3__X__spikes3"], "interval": 0.1})
        nest.Connect(mm, neuron)

        vm_1 = nest.Create("voltmeter")
        nest.Connect(vm_1, neuron)

        # simulate

        nest.Simulate(125.)

        # analysis
        V_m_timevec = nest.GetStatus(vm_1)[0]["events"]["times"]
        V_m = nest.GetStatus(vm_1)[0]["events"]["V_m"]
        mm = nest.GetStatus(mm)[0]["events"]
        MAX_ABS_ERROR = 1E-6
        print("Final V_m = " + str(V_m[-1]))
        assert abs(V_m[-1] - -72.89041451202348) < MAX_ABS_ERROR

        if TEST_PLOTS:

            fig, ax = plt.subplots(nrows=4)

            ax[0].plot(V_m_timevec, V_m, label="V_m")
            ax[0].set_ylabel("voltage")

            ax[1].plot(mm["times"], mm["I_kernel1__X__spikes1"], label="I_kernel1")
            ax[1].set_ylabel("current")

            ax[2].plot(mm["times"], mm["I_kernel2__X__spikes2"], label="I_kernel2")
            ax[2].set_ylabel("current")

            ax[3].plot(mm["times"], mm["I_kernel3__X__spikes3"], label="I_kernel3")
            ax[3].set_ylabel("current")

            for _ax in ax:
                _ax.legend(loc="upper right")
                _ax.set_xlim(0., 125.)
                _ax.grid(True)

            for _ax in ax[:-1]:
                _ax.set_xticklabels([])

            ax[-1].set_xlabel("time")

            plt.show()
