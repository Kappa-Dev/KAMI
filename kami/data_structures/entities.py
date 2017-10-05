"""Collection of classes implementing KAMI-specific entities.

KAMI entites specify an intermediary representation format for defining
agents of PPIs.

The implemented classes include:

- `Agent` represents a gene defined by the UniProt accession number.

- `Region` represents a domain defined by !....!

- `State` represents a state given by its name and value;

- `Residue` represents a residue defined by an amino acid and
(optionally) its location, it also encapsulates a `State` object
corresponding to a state of this residue.

- `PhysicalEntity` base class for physical entities in KAMI. Physical
entities encapsulate info about PTMs (residues, states, bounds)

- `PhysicalRegion` represents a physical region defined by a region
and a set of residues, states and bounds.

- `PhysicalAgent` represents a gene product, it can be thought of as
a physical protein defined by an agent (some gene) and by a set of regions,
residues, states and bounds (possible PTMs).

- `PhysicalRegionAgent`

- `NuggetAnnotation`

"""
import collections


class Agent(object):
    """Class implementing KAMI agent (gene)."""

    def __init__(self, uniprotid, hgnc_symbol=None,
                 synonyms=None, xrefs=None, location=None):
        """Initialize kami agent object."""
        self.uniprotid = uniprotid
        if hgnc_symbol:
            self.hgnc_symbol = hgnc_symbol
        else:
            self.hgnc_symbol = None
        if synonyms:
            self.synonyms = synonyms
        else:
            self.synonyms = []
        if xrefs:
            self.xrefs = xrefs
        else:
            self.xrefs = dict()
        self.location = location

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


class Region(object):
    """Class implementing KAMI region (domain)."""

    def __init__(self, start=None, end=None, name=None, order=None):
        """Initialize KAMI region object."""
        self.start = start
        self.end = end
        self.name = name
        self.order = order
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


class Residue(object):
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
        self.loc = loc
        self.state = state

    def __str__(self):
        """Str representation of residue."""
        res = "".join(self.aa)
        if self.loc:
            res += str(self.loc)
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        return {
            "aa": self.aa,
            "loc": {self.loc}
        }


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
        """Add a state to a list of residues of the entity."""
        self.states.append(state)
        return

    def add_bound(self, partner):
        """Add a bound to a list of residues of the entity."""
        self.bounds.append(partner)
        pass


class PhysicalRegion(PhysicalEntity):
    """Class implementing KAMI physical region (physical domain)."""

    def __init__(self, region, residues=None, states=None, bounds=None):
        """Initialize kami physical region object."""
        self.region = region
        if residues:
            self.residues = residues
        else:
            self.residues = []
        if states:
            self.states = states
        else:
            self.states = []
        if bounds:
            self.bounds = self._normalize_bounds(bounds)
        else:
            self.bounds = []
        return

    def __str__(self):
        """String representation of a physical region."""
        return str(self.region)


class PhysicalAgent(PhysicalEntity):
    """Class implementing KAMI physical agent (protein product)."""

    def __init__(self, agent, regions=None,
                 residues=None, states=None, bounds=None):
        """Initialize KAMI physical agent object."""
        self.agent = agent
        if regions:
            self.regions = regions
        else:
            self.regions = []
        if residues:
            self.residues = residues
        else:
            self.residues = []
        if states:
            self.states = states
        else:
            self.states = []
        if bounds:
            self.bounds = self._normalize_bounds(bounds)
        else:
            self.bounds = []
        return

    def __str__(self):
        """String representation of a physical agent."""
        return str(self.agent)


class PhysicalRegionAgent(PhysicalEntity):
    """."""

    def __init__(self, physical_region, physical_agent):
        """."""
        self.physical_region = physical_region
        self.physical_agent = physical_agent

    def __str__(self):
        """String representation of  region/agent."""
        res = ""
        res += str(self.physical_agent) + "_region_" + \
            str(self.physical_region)

        return res


class Motif(PhysicalEntity):
    """Class implementing KAMI residue motif."""

    def __init__(self, residue_list, name):
        """."""
        self.residue_list = residue_list
        self.name = name

    def __str__(self):
        """String represenation of motif."""
        res = ""
        for residue in self.residue_list:
            if len(residue.aa) > 1:
                res += "(" + "/".join(residue.aa)
                if res.loc:
                    res += str(res.loc)
                res += ")"
            else:
                res += list(residue.aa)[0]
                if residue.loc:
                    res += str(residue.loc)
        return res

    def to_physical_region(self):
        """Convert motif object to region object."""
        res_locs = []

        for residue in self.residue_list:
            if residue.loc:
                res_locs.append(residue.loc)

        start = None
        end = None
        if len(res_locs) > 0:
            start = min(res_locs)
            end = max(res_locs)

        region = Region(start=start, end=end, name=self.name)
        res = PhysicalRegion(region, residues=self.residue_list)
        return res

    def to_attrs(self):
        """Convert motif object to attrs."""
        res = dict()
        if self.name:
            res["name"] = {self.name}
        return res


class MotifAgent(PhysicalEntity):
    """."""

    def __init__(self, motif, physical_agent):
        """."""
        self.motif = motif
        self.physical_agent = physical_agent

    def __str__(self):
        """String representation of  region/agent."""
        res = ""
        res += str(self.physical_agent) + "_motif_" + \
            str(self.motif)

        return res


class NuggetAnnotation(object):
    """Class implementing kami nugget (fact) annotation."""

    def __init__(self, epistemics=None, source=None, text=None):
        """Init nugget annotation object."""
        self.epistemics = epistemics
        self.source = source
        self.text = text

    def to_attrs(self):
        """Convert agent object to attrs."""
        attrs = dict()
        if self.epistemics:
            attrs["epistemics"] = {self.epistemics}
        if self.source:
            attrs["source"] = {self.source}
        if self.text:
            attrs["text"] = {self.text}
        return attrs
