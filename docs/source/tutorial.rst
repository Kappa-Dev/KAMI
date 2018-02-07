.. _tutorial:

Tutorial
========
* :ref:`installation` 
* :ref:`entities`
* :ref:`kami_hierarchy`
* :ref:`black_box`  
* :ref:`instantiation`

**DISCLAIMER** 
All PPI examples presented in this tutorial are created by computer scientist, do not make any sense, but serve purely illustrative purpose.

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

------------------------------
KAMI entities and interactions
------------------------------

Similarly to such representations in `BioPAX <http://www.biopax.org/>`_ or `INDRA <http://indra.readthedocs.io/en/latest/modules/statements.html>`_, KAMI entites and interactions specify an intermediary representation format for defining protein-protein interactions (PPIs), their agents (roughly speaking proteins) and agents' components such as regions, sites, residues etc.

^^^^^^^^^^^^^
Genes in KAMI
^^^^^^^^^^^^^

In KAMI the basic agent of a PPI is a *gene*, from which we can further define its products (i.e. proteins) by providing specific regions, sites, residues, states and bounds. Therefore, in our system an agent corresponding to a gene actually represents not a single protein, but a feasible 'neighbourhood in the sequence space' of gene products.

Genes are defined by their Uniprot accession numbers. For example, we can define an object corresponding to the `EGFR <http://www.uniprot.org/uniprot/P00533>`_ gene as follows:

>>> egfr = Gene("P00533")

Now we would like to define *EGFR* who has key residue *Y* at the location *155* and, moreover, this residue should be phosphorylated:

>>> egfr_Y155 = Gene("P00533", residues=[Residue("Y", 155, state=State("phosphorylation", True))])

Define the gene _MAPK1_ who has protein kinase region:

>>> mapk1_PK = Gene("P28482", regions=[Region(name="Protein kinase", start=25, end=313)])


Simarly to the conditions on presence of regions we also can define conditions on presence of particular sites:

>>> mapk1_ = Gene("P28482", sites=[Site(name="", start=34, end=34)])


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sites and Regions as agents of interactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^




^^^^^^^^^^^^^^^^^^^^^^^^^
Modification interactions
^^^^^^^^^^^^^^^^^^^^^^^^^

Modifications in KAMI are defined as follows:

`Modification(enzyme, substrate, mod_target, mod_value=True, annotation=None, direct=False)`

Here, `enzyme` and `substrate` are instances of the base `Actor` class, `mod_target` is either an object of the `Residue` or the `State` class (represents an object of modification), `mod_value` is a boolean flag which says whether the state of the target is being set to True or Flase. 

Example statement: *"Active MEK1 phosphorylates residue S727 of STAT3"*

>>> mek1 = Gene("Q02750", states=[State("activity", True)])
>>> stat3 = Gene("P40763")
>>> mod_target = Residue("S", 727, State("phosphorylation", False))
>>> mod1 = Modification(mek1, stat3, mod_target, mod_state=True)
>>> print(mod1)
Modification:
	Enzyme: Q02750
	Substrate: P40763
	Mod target: S727
	Value: True
	Direct? True


^^^^^^^^^^^^^^^^^^^^
Binding interactions
^^^^^^^^^^^^^^^^^^^^





For example, we can specify an interaction, for which a particular gene product should have a specific mutation of some residue, by attaching a Residue node with a fixed value of amino acid corresponding to the mutation. More examples of
the biological facts expressed with graphs typed by the meta-model M will follow.

So, before defining a physical agent we actually need to define objects correspodning to regions, residues, states and bounds. Consider an example below where we define a state object (State) corresponding to activity state of a protein and pass it to the list of states of a physical agent, we also specify two residues (1) Residue T222 (whithout state it means that we just require that there is this particular amino acid at this particular location) (2) Phosphorylated residue S121 (here we require that this particular location with this amino acid is phosphorylated):



Actor vs Physical entity



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