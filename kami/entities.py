"""Collection of classes implementing KAMI-specific entities.

KAMI entites specify an intermediary representation format for defining
agents of PPIs and their components such as regions, sites, residues etc.

The implemented data structures include:

* `Actor` base class for an actor of PPIs. Such actors include genes
  (see `Gene`), regions of genes (see `RegionActor`), sites of genes or
  sites of regions of genes (see `SiteActor`).
* `PhysicalEntity` base class for physical entities in KAMI. Physical
  entities in KAMI include genes, regions, sites and they are able to
  encapsulate info about PTMs (such as residues with their states,
  states, bounds).
* `Gene`  represents a gene defined by the UniProt accession number and a
   set of regions, sites, residues, states and bounds (possible PTMs).
* `Region` represents a physical region (can be seen as protein dimain) defined
  by a region
  and a set of its sites, residues, states and bounds.
* `Site` represents a physical site (usually binding site etc) defined by some
  short sequence interval and a its residues, states and bounds (PTMs).
* `Residue` represents a residue defined by an amino acid and
  (optionally) its location, it also encapsulates a `State` object
  corresponding to a state of this residue.
* `State` represents a state given by its name and value (value assumed to be
  boolean).
* `RegionActor` represents an actor
* `SiteActor`
* (under construction) `NuggetAnnotation`

"""
import collections


class Actor(object):
    """Base class for actors of interaction."""

    pass


class PhysicalEntity(object):
    """Base class for physical entities in KAMI.

    Implements several methods of common behaviour:
    - `add_residue` - adds a residue to a physical entity
    - `add_state` - adds a state to a physical entity
    - `add_bound` - adds a bound partner to a physical entity
    """

    def _normalize_bounds(self, bounds):
        new_bounds = []
        for el in bounds:
            if not isinstance(el, collections.Iterable):
                new_bounds.append([el])
            else:
                new_bounds.append(el)
        return new_bounds

    def add_residue(self, residue):
        """Add a residue to a list of residues of the entity."""
        self.residues.append(residue)
        return

    def add_state(self, state):
        """Add a state to a list of states of the entity."""
        self.states.append(state)
        return

    def add_bound(self, partner):
        """Add a bound to a list of bound conditions of the entity."""
        self.bound.append(partner)
        pass

    def add_unbound(self, partner):
        """Add an unbound-condition to the entity."""
        self.unbound.append()


class Gene(Actor, PhysicalEntity):
    """Class for a gene."""

    def __init__(self, uniprotid, regions=None, residues=None, sites=None,
                 states=None, bound_to=None, unbound_from=None,
                 hgnc_symbol=None, synonyms=None, xrefs=None, location=None):
        """Initialize kami protein object."""
        self.uniprotid = uniprotid

        self.hgnc_symbol = hgnc_symbol

        if synonyms is None:
            synonyms = []
        self.synonyms = synonyms

        if xrefs is None:
            xrefs = dict()
        self.xrefs = xrefs

        self.location = location

        if regions is None:
            regions = []
        self.regions = regions

        if sites is None:
            sites = []
        self.sites = sites

        if residues is None:
            residues = []
        self.residues = residues

        if states is None:
            states = []
        self.states = states

        if bound_to is None:
            bound_to = []
        self.bound_to = self._normalize_bounds(bound_to)

        if unbound_from is None:
            unbound_from = []
        self.unbound_from = self._normalize_bounds(unbound_from)
        return

    def __repr__(self):
        """Representation of a gene."""
        content = ""

        components = ["uniprot={}".format(self.uniprotid)]

        if self.regions:
            components.append("regions=[{}]".format(", ".join(
                [r.__repr__() for r in self.regions])))
        if self.sites:
            components.append("sites=[{}]".format(", ".join(
                [s.__repr__() for s in self.sites])))
        if self.residues:
            components.append("residues=[{}]".format(", ".join(
                [r.__repr__() for r in self.residues])))
        if self.states:
            components.append("states=[{}]".format(", ".join(
                [s.__repr__() for s in self.states])))
        if self.bound_to:
            components.append("bound_to=[{}]".format(", ".join(
                [b.__repr__() for b in self.bound_to])))
        if self.unbound_from:
            components.append("unbound_from=[{}]".format(", ".join(
                [b.__repr__() for b in self.unbound_from])))

        content = ", ".join(components)

        res = "Gene({})".format(content)
        return res

    def __str__(self):
        """String represenation of a gene."""
        return str(self.uniprotid)

    def to_attrs(self):
        """Convert agent object to attrs."""
        agent_attrs = {
            "uniprotid": {self.uniprotid}
        }
        if self.hgnc_symbol is not None:
            agent_attrs["hgnc_symbol"] = {self.hgnc_symbol}
        if self.synonyms is not None:
            agent_attrs["synonyms"] = set(self.synonyms)
        if self.xrefs is not None:
            agent_attrs["xrefs"] = set(self.xrefs.items())
        return agent_attrs

    def add_region(self, region):
        """Add a region to a list of regions of the entity."""
        self.regions.append(region)
        return

    def add_site(self, site):
        """Add a site to a list of sites of the entity."""
        self.sites.append(site)
        return


class Region(PhysicalEntity):
    """Class for a conserved gene region."""

    def __init__(self, name=None, interproid=None, start=None, end=None,
                 order=None, sites=None, residues=None, states=None,
                 bound_to=None, unbound_from=None, label=None):
        """Initialize kami region object."""
        self.name = name
        self.interproid = interproid
        self.start = start
        self.end = end
        self.order = order
        self.label = label

        if sites is None:
            sites = []
        self.sites = sites

        if residues is None:
            residues = []
        self.residues = residues

        if states is None:
            states = []
        self.states = states

        if bound_to is None:
            bound_to = []
        self.bound_to = self._normalize_bounds(bound_to)

        if unbound_from is None:
            unbound_from = []
        self.unbound_from = self._normalize_bounds(unbound_from)
        return

    def __repr__(self):
        """Representation of a region."""
        content = ""

        components = []
        if self.name:
            components.append("name='{}'".format(self.name))
        if self.interproid:
            if type(self.interproid) is list:
                components.append(
                    "interproid=[{}]".format(
                        ",".join("'{}'".format(i)
                                 for i in self.interproid)))
            else:
                components.append("interproid='{}'".format(self.interproid))
        if self.start:
            components.append("start={}".format(self.start))
        if self.end:
            components.append("end={}".format(self.end))
        if self.order:
            components.append("order={}".format(self.order))
        if self.sites:
            components.append("sites=[{}]".format(", ".join(
                [s.__repr__() for s in self.sites])))
        if self.residues:
            components.append("residues=[{}]".format(", ".join(
                [r.__repr__() for r in self.residues])))
        if self.states:
            components.append("states=[{}]".format(", ".join(
                [s.__repr__() for s in self.states])))
        if self.bound_to:
            components.append("bound_to=[{}]".format(", ".join(
                [b.__repr__() for b in self.bound_to])))
        if self.unbound_from:
            components.append("unbound_from=[{}]".format(", ".join(
                [b.__repr__() for b in self.unbound_from])))
        if len(components) > 0:
            content = ", ".join(components)

        res = "Region({})".format(content)
        return res

    def __str__(self):
        """String representation of a region."""
        res = "region"
        if self.name:
            res += "_{}".format(self.name)
        if self.interproid:
            if type(self.interproid) is list:
                res += "_{}".format("-".join(
                    [str(ipr_id) for ipr_id in self.interproid]))
            else:
                res += "_{}".format(self.interproid)
        if self.start:
            res += "_" + str(self.start)
        if self.end:
            res += "_" + str(self.end)
        if self.order:
            res += "_{}".format(str(self.order))

        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        res = dict()
        if self.interproid:
            res["interproid"] = self.interproid
        if self.start:
            res["start"] = {self.start}
        if self.end:
            res["end"] = {self.end}
        if self.name:
            res["name"] = {self.name}
        if self.order:
            res["order"] = {self.order}
        if self.label:
            res["label"] = {self.label}
        return res

    def add_site(self, site):
        """Add a site to a list of sites of the entity."""
        self.sites.append(site)
        return


class Site(PhysicalEntity):
    """Class for a gene's interaction site."""

    def __init__(self, name=None, start=None, end=None, order=None,
                 residues=None, states=None, bound_to=None, unbound_from=None):
        """Initialize kami site object."""
        self.name = name
        self.start = start
        self.end = end
        self.order = order

        if residues is None:
            residues = []
        self.residues = residues

        if states is None:
            states = []
        self.states = states

        if bound_to is None:
            bound_to = []
        self.bound_to = self._normalize_bounds(bound_to)

        if unbound_from is None:
            unbound_from = []
        self.unbound_from = self._normalize_bounds(unbound_from)
        return

    def __repr__(self):
        """Representation of a site."""
        content = ""

        components = []
        if self.name:
            components.append("name='{}'".format(self.name))
        if self.start:
            components.append("start={}".format(self.start))
        if self.end:
            components.append("end={}".format(self.end))
        if self.order:
            components.append("order={}".format(self.order))

        if self.residues:
            components.append("residues=[{}]".format(", ".join(
                [r.__repr__() for r in self.residues])))
        if self.states:
            components.append("states=[{}]".format(", ".join(
                [s.__repr__() for s in self.states])))
        if self.bound_to:
            components.append("bound_to=[{}]".format(", ".join(
                [b.__repr__() for b in self.bound_to])))
        if self.unbound_from:
            components.append("unbound_from=[{}]".format(", ".join(
                [b.__repr__() for b in self.unbound_from])))
        if len(components) > 0:
            content = ", ".join(components)

        res = "Site({})".format(content)
        return res

    def __str__(self):
        """String representation of a site."""
        res = "site"
        if self.name:
            res += "_{}".format(self.name)
        if self.start:
            res += "_" + str(self.start)
        if self.end:
            res += "_" + str(self.end)
        if self.order:
            res += "_{}".format(str(self.order))
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        res = dict()
        if self.start is not None:
            res["start"] = {self.start}
        if self.end is not None:
            res["end"] = {self.end}
        if self.name:
            res["name"] = {self.name}
        if self.order:
            res["order"] = {self.order}
        return res


class Residue():
    """Class for a residue."""

    def __init__(self, aa, loc=None, state=None):
        """Init residue object."""
        if type(aa) == set:
            pass
        elif isinstance(aa, collections.Iterable):
            aa = set(aa)
        else:
            aa = set([aa])
        self.aa = aa
        if loc is not None:
            self.loc = int(loc)
        else:
            self.loc = None
        self.state = state

    def __repr__(self):
        """Representation of a site."""
        content = ""

        components = ["aa={}".format(self.aa)]
        if self.loc:
            components.append("loc={}".format(self.loc))
        if self.state:
            components.append("state={}".format(self.state.__repr__()))
        if len(components) > 0:
            content = ", ".join(components)

        res = "Residue({})".format(content)
        return res

    def __str__(self):
        """Str representation of residue."""
        res = "".join(self.aa)
        if self.loc:
            res += str(self.loc)
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        res = dict()
        res["aa"] = self.aa
        if self.loc is not None:
            res["loc"] = {int(self.loc)}
        return res


class State(object):
    """Class for a KAMI state."""

    def __init__(self, name, value):
        """Init kami state object."""
        self.name = name
        self.value = value

    def __repr__(self):
        """Representation of a state."""
        return "State(name='{}', value={})".format(self.name, self.value)

    def __str__(self):
        """Str representation of a state."""
        res = str(self.name)
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        return {
            self.name: {self.value}
        }


class RegionActor(Actor):
    """Class for a region of a gene as an actor of PPI."""

    def __init__(self, gene, region):
        """Initialize RegionActor object."""
        self.region = region
        self.gene = gene

    def __repr__(self):
        """Representation of a region actor object."""
        return "RegionActor(gene={}, region={})".format(
            self.gene.__repr__(), self.region.__repr__())

    def __str__(self):
        """String representation of a RegionActor object."""
        res = str(self.region) + "_"
        res += str(self.gene)
        return res


class SiteActor(Actor):
    """Class for a site of a gene as an actor of PPI."""

    def __init__(self, gene, site, region=None):
        """Initialize SiteActor object."""
        self.site = site
        self.region = region
        self.gene = gene

    def __repr__(self):
        """Representation of a site actor object."""
        content = ""
        if self.region is not None:
            content += "region={}, ".format(self.region.__repr__())
        content += "site={}".format(self.site.__repr__())

        return "SiteActor(gene={}, {})".format(
            self.gene.__repr__(), content)

    def __str__(self):
        """String representation of a SiteActor object."""
        res = str(self.gene)
        if self.region is not None:
            res += "_" + str(self.region)
        res += "_" + str(self.site)

        return res
