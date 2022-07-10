.. JIT documentation master file, created by
   sphinx-quickstart on Sun Nov 28 19:28:54 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Fully automated model generation in PyNEST
==========================================
NEST [1]_ is a simulator for large-scale
networks of spiking and non-spiking neural networks used in computational neuroscience to
build models of brain-like or brain-inspired neuronal circuits. It profits from the efficiency
of C++ to simulate networks with large numbers of neurons and synaptic connections
and is parallelized using MPI and OpenMP. By providing a Python interface (PyNEST [2]_) that interacts with the NestKernel in C++ [3]_, users can easily define their simulations and add new models dynamically at the
runtime by means of the function ``nest.Install()``.
Originally, models had to be manually written in C++. Since some years, the model
creation process is supported by NESTML [4]_, which generates the
required code from a high-level specification and compiles them into dynamic libraries that
are ready to be used from within PyNEST. NESTML is a user-friendly, flexible and Turing-
complete domain-specific language. It simplifies the modeling process for neuroscientists
by allowing them to express their models in domain terminology, both with and without
prior training in computer science. By specifying the target type – either a different
hardware or new supported simulator – the user can use the same model to generate code
for the given target without any manual interventions.
Running a simulation script in NEST using an external custom model requires the user to
provide certain configurations to the NESTML code generator. Such configurations cover
the model source code location, model dependencies to other models (e.g., custom synapse
models) and the target platform. Although the NESTML code generation is completely
automated, the user still has to explicitly invoke the NESTML interface for the model
to be processed and compiled into an extension module for NEST, which is especially
cumbersome if many neuron/synapse combinations are used.
The first goal of this thesis is to eliminate the explicit calls to the NESTML interface
in the simulation script by a seamless extension to PyNEST that intercepts calls to
``nest.Create()`` and ``nest.Connect()`` and controls the workflow logic of the NESTML
functions behind the scenes. Depending on certain conditions this integration decides if
the model should be instantiated right away, or if the code generation and compilation
can be delayed to a later point in time. As the workflow is only triggered when the user
invokes specific functions instead of invoking NESTML upfront, this extension is called
just-in-time compilation (JIT ).
One problem that arises from a delayed availability of the model instances when using JIT
is that model parameters cannot be queried before the actual start of the simulation. This
prohibits adaptive parameter choices for following calls to PyNEST and thus restricts
the flexibility for the users. A possible solution would be to cache parameters on the
Python level until the instances are available, albeit at the cost of doubling the memory
requirements. A more efficient solution is to provide a model independent storage of
parameters in the form of data vectors. This second solutions also vastly increases the
cache-efficiency of models by applying a single-instruction-multiple-data (SIMD) [5]_ paradigm that increases the performance of the simulation script by storing
all objects as an array of structures (AoS).



References
++++++++++

.. [1] Gewaltig, M.-O., & Diesmann, M. (2007). 
         NEST (neural simulation tool). Scholarpe-dia 2 (4), 1430.
.. [2] Eppler, J., Helias, M., Muller, E., Diesmann, M., & Gewaltig, M.-O. (2009).
         Pynest: a convenient interface to the nest simulator. Frontiers in Neuroinformatics 2, 12.

.. [3] Zaytsev, Y., & Morrison, A. (2014)
         Cynest: a maintainable cython-based interface for
         the nest simulator.
.. [4] Plotnikov, D., Rumpe, B., Blundell, I., Ippen, T., Eppler, J. M., & Morrison, A. (2016).
         Nestml: a modeling language for spiking neurons.

.. [5] Nuzman, D., Rosen, I., & Zaks, A. (2006).
         Auto-vectorization of interleaved data for simd.
         ACM SIGPLAN Notices 41 (6), 132–143.



.. toctree::
   :glob:
   :hidden:
   :maxdepth: 1




   introduction
   api/index
