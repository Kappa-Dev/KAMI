"""Collection of classes implementing kami-specific entities."""
import collections


class PhysicalEntity(object):
    """Base class for physical entities in KAMI."""
    def _normalize_bounds(self, bounds):
        new_bounds = []
        for el in bounds:
            if not isinstance(el, collections.Iterable):
                new_bounds.append([el])
            else:
                new_bounds.append(el)
        return new_bounds

    def add_residue(self, residue):
        pass

    def add_state(self, state):
        pass

    def add_bound(self, partners):
        pass


class Agent(object):
    """Class implementing kami agent."""

    def __init__(self, uniprotid, names=None, xrefs=None, location=None):
        """Initialize kami agent object."""
        self.uniprotid = uniprotid
        if names:
            self.names = names
        else:
            self.names = []
        if xrefs:
            self.xrefs = xrefs
        else:
            self.xrefs = dict()
        self.location = location

    def __str__(self):
        return str(self.uniprotid)

    def to_attrs(self):
        """Convert agent object to attrs."""
        agent_attrs = {
            "uniprotid": {self.uniprotid},
            "names": set(self.names),
            "xrefs": set(self.xrefs.items())
        }
        return agent_attrs


class PhysicalAgent(PhysicalEntity):
    """Class implementing kami physical agent."""

    def __init__(self, agent, regions=None, residues=None, states=None, bounds=None):
        """Initialize kami physical agent object."""
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
        return str(self.agent)


class Region(object):
    """Class implementing kami region."""

    def __init__(self, start=None, end=None, name=None):
        """Initialize kami region object."""
        self.start = start
        self.end = end
        self.name = name
        return

    def __str__(self):
        """String representation of the region."""
        res = "region_%s_%s" % (self.start, self.end)
        if self.name:
            res += "_%s" % self.name
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        res = {
            "start": self.start,
            "end": self.end
        }
        if self.name:
            res["name"] = self.name
        return res


class PhysicalRegion(PhysicalEntity):
    """."""

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
        return str(self.region)


class PhysicalRegionAgent(PhysicalEntity):
    """."""
    def __init__(self, physical_region, physical_agent):
        """."""
        self.physical_region = physical_region
        self.physical_agent = physical_agent


class Residue(object):
    """Class implementing kami residue."""

    def __init__(self, aa, loc=None, state=None):
        """Init kami residue object."""
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
            "loc": self.loc
        }


class State(object):
    """Class implementing kami state."""

    def __init__(self, name, value):
        """Init kami state object."""
        self.name = name
        self.value = value

    def __str__(self):
        """Str representation of state."""
        res = "%s_%s" % (self.name, self.value)
        return res

    def to_attrs(self):
        """Convert agent object to attrs."""
        return {
            self.name: self.value
        }


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
            attrs["epistemics"] = self.epistemics
        if self.source:
            attrs["source"] = self.source
        if self.text:
            attrs["text"] = self.text
        return attrs
