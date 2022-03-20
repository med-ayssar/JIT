import os
import unittest
import numpy as np

from jit import nest


class NestMultithreadingTest(unittest.TestCase):

    neuron_model = "iaf_psc_exp_test"

    number_of_threads = 2

    def test_neuron_multithreading(self):
        nest.set_verbosity("M_ALL")

        nest.ResetKernel()

        nest.SetKernelStatus({'resolution': 0.1, 'local_num_threads': self.number_of_threads})
        spike_times = np.arange(10, 100, 9).astype(np.float)
        sg = nest.Create('spike_generator',
                         params={'spike_times': spike_times})

        n = nest.Create(self.neuron_model, 5)
        nest.Connect(sg, n)

        multimeter = nest.Create('multimeter', params={"record_from": ["V_m"]})
        nest.Connect(multimeter, n)

        nest.Simulate(1000.)
        events = multimeter.get("events")
        v_m = events["V_m"]
        np.testing.assert_almost_equal(v_m[-1], -70.)
        pass

    def test_neuron_synapse_multithreading(self):
        pre_spike_times = np.array([2.,   4.,   7.,   8.,  12.,  13.,  19.,  23.,  24.,  28.,  29.,  30.,  33.,  34.,
                                    35.,  36.,  38.,  40.,  42.,  46.,  51.,  53.,  54.,  55.,  56.,  59.,  63.,  64.,
                                    65.,  66.,  68.,  72.,  73.,  76.,  79.,  80.,  83.,  84.,  86.,  87.,  90.,  95.])
        post_spike_times = np.array([4.,   5.,   6.,   7.,  10.,  11.,  12.,  16.,  17.,  18.,  19.,  20.,  22.,  23.,
                                     25.,  27.,  29.,  30.,  31.,  32.,  34.,  36.,  37.,  38.,  39.,  42.,  44.,  46.,
                                     48.,  49.,  50.,  54.,  56.,  57.,  59.,  60.,  61.,  62.,  67.,  74.,  76.,  79.,
                                     80.,  81.,  83.,  88.,  93.,  94.,  97.,  99.])

        nest.set_verbosity("M_ALL")
        nest.ResetKernel()

        nest.SetKernelStatus({'resolution': 0.1, 'local_num_threads': self.number_of_threads})

        wr = nest.Create('weight_recorder')
        nest.CopyModel("stdp_test", "stdp_nestml_rec",
                       {"weight_recorder": wr[0], "w": 1., "the_delay": 1., "receptor_type": 0})

        # Spike generators
        pre_sg = nest.Create("spike_generator", 2,
                             params={"spike_times": pre_spike_times})
        post_sg = nest.Create("spike_generator", 2,
                              params={"spike_times": post_spike_times,
                                      'allow_offgrid_times': True})

        pre_neuron = nest.Create(self.neuron_model, 2)
        post_neuron = nest.Create(self.neuron_model, 2)
        sr_pre = nest.Create("spike_recorder")
        sr_post = nest.Create("spike_recorder")
        mm = nest.Create("multimeter", params={"record_from": ["V_m"]})

        nest.Connect(pre_sg, pre_neuron, "one_to_one", syn_spec={"delay": 1.})
        nest.Connect(pre_neuron, post_neuron, "all_to_all", syn_spec={'synapse_model': 'stdp_nestml_rec'})
        nest.Connect(post_sg, post_neuron, "one_to_one", syn_spec={"delay": 1., "weight": 9999.})
        nest.Connect(mm, post_neuron)
        nest.Connect(pre_neuron, sr_pre)
        nest.Connect(post_neuron, sr_post)

        nest.Simulate(100.)

        V_m = nest.GetStatus(mm, "events")[0]["V_m"]
        print(V_m)
        np.testing.assert_almost_equal(V_m[-4],  -59.17946541)
