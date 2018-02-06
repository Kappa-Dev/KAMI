.. _tutorial:

Tutorial
========
* :ref:`installation` 
* :ref:`entities`
* :ref:`interactions`
* :ref:`kami_hierarchy`
* :ref:`black_box`  
* :ref:`instantiation`

.. _installation:

------------
Installation 
------------

    In order to install the KAMI library you have to clone this repository using SSH

    .. code-block:: console

        git clone git@github.com:Kappa-Dev/KAMI.git

    or using HTTPS

    .. code-block:: console

        git clone https://github.com/Kappa-Dev/KAMI.git


    Install the library and its dependencies with `setup.py`

    .. code-block:: console

        cd KAMI
        python setup.py install


.. _entities:

-------------
KAMI entities
-------------

KAMI entites specify an intermediary representation format for defining
agents of PPIs and their components such as regions, sites, residues etc.



The implemented data structures include:

* `Actor` base class for an actor of PPIs. Such actors include genes (see `Gene`),
  regions of genes (see `RegionActor`), sites of genes or sites of regions of genes
  (see `SiteActor`).
* `PhysicalEntity` base class for physical entities in KAMI. Physical
  entities in KAMI include genes, regions, sites and they are able to encapsulate info 
  about PTMs (such as residues with their states, states, bounds).
* `Gene`  represents a gene defined by the UniProt accession number and a
   set of regions, sites, residues, states and bounds (possible PTMs).
* `Region` represents a physical region (can be seen as protein dimain) defined by a region
  and a set of its sites, residues, states and bounds.
* `Site` represents a physical site (usually binding site etc) defined by some
  short sequence interval and a its residues, states and bounds (PTMs).
* `Residue` represents a residue defined by an amino acid and
  (optionally) its location, it also encapsulates a `State` object
  corresponding to a state of this residue.
* `State` represents a state given by its name and value (value assumed to be boolean).
* `RegionActor` represents an actor
* `SiteActor`



.. _interactions:

-----------------
KAMI interactions
-----------------


.. _kami_hierarchy:

------------------------
Hierarchies: KAMI models
------------------------


.. _black_box:

---------
Black box
---------


.. _instantiation:

----------------------------
Concrete model instantiation
----------------------------