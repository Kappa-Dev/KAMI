"""Collection of classes implementing KAMI-specific entities.

KAMI entites specify an intermediary representation format for defining
agents of PPIs.

The implemented classes include:

- `Actor`
- `PhysicalEntity` base class for physical entities in KAMI. Physical
entities encapsulate info about PTMs (residues, states, bounds)
- `Gene`  represents a gene defined by the UniProt accession number and a
set of regions, residues, states and bounds (possible PTMs).
- `Region` represents a physical region defined by a region
and a set of residues, states and bounds.
- `Site`
- `Residue` represents a residue defined by an amino acid and
(optionally) its location, it also encapsulates a `State` object
corresponding to a state of this residue.
- `State` represents a state given by its name and value;
- `RegionActor`
- `SiteActor`
- (under construction) `NuggetAnnotation`

"""
import collections


class Actor():
    pass


class PhysicalEntity():
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
        """Add a state to a list of residues of the entity."""
        self.states.append(state)
        return

    def add_bound(self, partner):
        """Add a bound to a list of residues of the entity."""
        self.bounds.append(partner)
        pass


class Gene(Actor, PhysicalEntity):

    def __init__(self, uniprotid, regions=None, residues=None, sites=None,
                 states=None, bounds=None, hgnc_symbol=None,
                 synonyms=None, xrefs=None, location=None):
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

        if bounds is None:
            bounds = []
        self.bounds = self._normalize_bounds(bounds)

        return

    def __str__(self):
        """String represenation of an agent."""
        return str(self.uniprotid)

    def to_attrs(self):
        """Convert agent object to attrs."""
        agent_attrs = {
            "uniprotid": {self.uniprotid},
            "hgnc_symbol": {self.hgnc_symbol},
            "synonyms": set(self.synonyms),
            "xrefs": set(self.xrefs.items())
        }
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

    def __init__(self, start=None, end=None, name=None, order=None,
                 sites=None, residues=None, states=None, bounds=None,
                 label=None):
        """Initialize kami region object."""
        self.start = start
        self.end = end
        self.name = name
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

        if bounds is None:
            bounds = []
        self.bounds = self._normalize_bounds(bounds)
        return

    def __str__(self):
        """String representation of the region."""
        res = "region"
        if self.start:
            res += "_" + str(self.start)
        if self.end:
            res += "_" + str(self.end)
        if self.name:
            res += "_%s" % self.name
        if self.order:
            res += "_%s" % str(self.order)
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
        if self.label:
            res["label"] = {self.label}
        return res

    def add_site(self, site):
        """Add a site to a list of sites of the entity."""
        self.sites.append(site)
        return


class Site(PhysicalEntity):

    def __init__(self, start=None, end=None, name=None, order=None,
                 residues=None, states=None, bounds=None):
        """Initialize kami site object."""
        self.start = start
        self.end = end
        self.name = name
        self.order = order

        if residues is None:
            residues = []
        self.residues = residues

        if states is None:
            states = []
        self.states = states

        if bounds is None:
            bounds = []
        self.bounds = self._normalize_bounds(bounds)
        return

    def __str__(self):
        """String representation of the region."""
        res = "region"
        if self.start:
            res += "_" + str(self.start)
        if self.end:
            res += "_" + str(self.end)
        if self.name:
            res += "_%s" % self.name
        if self.order:
            res += "_%s" % str(self.order)
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
    """Class implementing KAMI residue."""

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
    """Class implementing KAMI state."""

    def __init__(self, name, value):
        """Init kami state object."""
        self.name = name
        self.value = value

    def __str__(self):
        """Str representation of state."""
        res = "%s" % (self.name)
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        return {
            self.name: {self.value}
        }


class RegionActor(Actor):
    def __init__(self, gene, region):
        """."""
        self.region = region
        self.gene = gene

    def __str__(self):
        """String representation of  region/agent."""
        res = ""
        res += str(self.gene) + "_region_" + \
            str(self.region)

        return res


class SiteActor(Actor):
    def __init__(self, site, gene, region=None):
        """."""
        self.site = site
        self.region = region
        self.gene = gene

    def __str__(self):
        """String representation of  region/agent."""
        res = str(self.gene)
        if self.region is not None:
            res += "_region_" + str(self.region)
        res += "_site_" + str(self.site)

        return res
