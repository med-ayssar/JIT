import os
import unittest

import numpy as np

try:
    import matplotlib
    import matplotlib.pyplot as plt

    TEST_PLOTS = True
except BaseException:
    TEST_PLOTS = False

from jit import nest
import scipy
import scipy.signal
import scipy.stats


class NestFirFilterTest(unittest.TestCase):
    r"""
    Tests the working of FIR filter model in NEST
    """

    def test_fir_filter(self):

        nestml_model_name = "fir_filter"

        t_sim = 101.
        resolution = 0.1

        nest.set_verbosity("M_ALL")

        nest.ResetKernel()

        # Create a fir_filter node
        neuron = nest.Create(nestml_model_name, params={"N": 256})

        # Create a spike generator
        spikes = [1.0, 1.0, 1.5, 1.5, 1.5, 6.7, 10.0, 10.5, 10.5, 10.5, 10.5, 11.3, 11.3, 11.4, 11.4, 20., 22.5, 30.,
                  40., 42., 42., 42., 50.5, 50.5, 75., 88., 93., 93.]
        sg = nest.Create("spike_generator", params={"spike_times": spikes})
        nest.Connect(sg, neuron, syn_spec=dict(delay=resolution))

        # Get N (order of the filter)
        n = nest.GetStatus(neuron, "N")[0]
        print("N: {}".format(n))

        # Set filter coefficients
        h = self.generate_filter_coefficients(n)
        nest.SetStatus(neuron, {"h": h})
        print("h: ", h)

        # Multimeter
        multimeter = nest.Create("multimeter")
        nest.SetStatus(multimeter, {"interval": resolution})
        multimeter.set({"record_from": ["y"]})  # output of the filter
        nest.Connect(multimeter, neuron)

        # Spike recorder
        sr = nest.Create("spike_recorder")
        nest.Connect(sg, sr)
        nest.Connect(neuron, sr)

        # Simulate
        nest.Simulate(t_sim)

        # Record from multimeter
        events = multimeter.get("events")
        y = events["y"]
        times = events["times"]
        spike_times = nest.GetStatus(sr, keys="events")[0]["times"]

        # Scipy filtering
        spikes, bin_edges = np.histogram(spike_times, np.arange(0, t_sim, resolution))
        output = scipy.signal.lfilter(h, 1, spikes)

        # Plots
        if TEST_PLOTS:
            self.plot_output(spike_times, times, y, title="FIR FILTER (NESTML)",
                             filename="fir_filter_output_nestml.png")
            self.plot_output(spike_times, bin_edges[1:], output, title="FIR FILTER (scipy)",
                             filename="fir_filter_output_scipy.png")

        np.testing.assert_allclose(y, output)

    def generate_filter_coefficients(self, order: int):
        """
        Generate the filter coefficients for the given order
        :param order: order of the filter
        :return: a list with the coefficients for the filter
        """
        Ts = 1E-4
        f_sampling = 1 / Ts
        f_cutoff = 50.  # [Hz]
        f_nyquist = f_sampling // 2
        cutoff = f_cutoff / f_nyquist

        return scipy.signal.firwin(order, cutoff, pass_zero=True)

    def plot_output(self, spike_times, times, y, title="FIR FILTER", filename="fir_filter_output.png"):
        """
        Generate the filtered output plot computed via NESTML
        :param spike_times: times when spikes occur
        :param times: total simualtion time
        :param y: output of the filter for the simulation time
        :param filename: file name of the plot
        :param title: title of the plot
        """
        plt.figure()
        plt.scatter(spike_times, np.zeros_like(spike_times), label="input", marker="d", color="orange")
        plt.plot(times, y, label="filter")
        plt.xlabel("Time (ms)")
        plt.ylabel("Filter output")
        plt.legend()
        plt.title(title)
        plt.savefig("/tmp/" + filename)
