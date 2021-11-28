.. JIT documentation master file, created by
   sphinx-quickstart on Sun Nov 28 19:28:54 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to JIT's documentation!
===============================
NESTML processing is completely automated, and as the first step in this project the manual
steps that are presently needed to integrate NESTML and NEST will be eliminated. In this
context, “Just-in-time” refers to the building of the extension module only at the point where it is
needed, that is, when performing the instantiation of a model in the PyNEST simulation script.
Instead of invoking NESTML upfront, it will be invoked by the JIT mechanism when the user
instantiates the neuron (or synapse) using the PyNEST call ``nest.Create()`` (or ``nest.Connect()``).
Some further constraints may apply. For example, in some cases neurons and their
connecting synapse models cannot be generated separately, but have to be generated in pairs,
because they have strong dependencies on each other.


.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
