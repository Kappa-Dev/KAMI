.. KAMI: Knowledge Aggregator and Model Instantiator documentation master file, created by
   sphinx-quickstart on Mon Feb  5 12:52:00 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to KAMI's documentation!
================================

KAMI (Knowledge Aggregator and Model Instantiator) is the Python library for semi-automatic bio-curation in 
cellular signalling. It provides a collection of utils for gradual building of complex biological models, it allows a user to aggregate individual protein-protein interactions of different provenance into a meaningful model, use it to instantiate rule-based models of concrete systems and perform various hypothesis testing.

Apart from the aggregated user knowledge, KAMI models contain expert knowledge used for the interpretation of interactions, for example, semantics of particular protein domains, protein families, definitions of activity forms, etc. This expert knowledge is obtained from both publicly available data (such as `UniProt <http://www.uniprot.org/>`_, `Pfam <http://pfam.xfam.org/>`_, `InterPro <https://www.ebi.ac.uk/interpro/>`_
databases) and from collaboration with biologists.

Using knowledge aggregated by a user in a KAMI model, the library allows to automatically instantiate models expressed with `Kappa <https://kappalanguage.org/>`_ rules and perform simulations.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

:ref:`tutorial`
==============

* :ref:`installation` 
* :ref:`entities`
* :ref:`kami_hierarchy`
* :ref:`black_box`  
* :ref:`instantiation`



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
