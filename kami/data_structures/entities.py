"""Collection of classes implementing KAMI-specific entities.

KAMI entites specify an intermediary representation format for defining
agents of PPIs and their components such as regions, sites, residues etc.

The implemented data structures include:

* `Actor` base class for an actor of PPIs. Such actors include protoforms
  (see `Protoform`), regions of protoforms (see `RegionActor`), sites of protoforms or
  sites of regions of protoforms (see `SiteActor`).
* `PhysicalEntity` base class for physical entities in KAMI. Physical
  entities in KAMI include protoforms, regions, sites and they are able to
  encapsulate info about PTMs (such as residues with their states,
  states, bounds).
* `Protoform`  represents a protoform defined by the UniProt accession number and a
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
from collections.abc import Iterable

from kami.utils.generic import normalize_to_set, normalize_to_iterable
from kami.exceptions import KamiEntityError


def actor_to_json(actor):
    """Load an actor object from JSON representation."""
    json_data = {}
    json_data["data"] = actor.to_json()
    if isinstance(actor, Protoform):
        json_data["type"] = "Protoform"
    elif isinstance(actor, RegionActor):
        json_data["type"] = "RegionActor"
    elif isinstance(actor, SiteActor):
        json_data["type"] = "SiteActor"
    return json_data


def actor_from_json(json_data):
    """Load an actor object from JSON representation."""
    if "type" in json_data:
        if json_data["type"] == "Protoform":
            return Protoform.from_json(json_data["data"])
        elif json_data["type"] == "RegionActor":
            return RegionActor.from_json(json_data["data"])
        elif json_data["type"] == "SiteActor":
            return SiteActor.from_json(json_data["data"])
        else:
            raise KamiEntityError(
                "Cannot load an actor: invalid actor type '{}'".format(
                    json_data["type"]))


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


class Protoform(Actor, PhysicalEntity):
    """Class for a protoform."""

    def __init__(self, uniprotid, regions=None, sites=None, residues=None,
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

        self.bound_to = normalize_to_iterable(bound_to)
        self.unbound_from = normalize_to_iterable(unbound_from)
        return

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["uniprotid"] = self.uniprotid
        if self.hgnc_symbol:
            json_data["hgnc_symbol"] = self.hgnc_symbol
        if self.synonyms:
            json_data["synonyms"] = self.synonyms
        if self.xrefs:
            json_data["xrefs"] = self.xrefs
        if self.location:
            json_data["location"] = self.xrefs
        json_data["regions"] = []
        for r in self.regions:
            json_data["regions"].append(r.to_json())
        json_data["sites"] = []
        for s in self.sites:
            json_data["sites"].append(s.to_json())
        json_data["residues"] = []
        for r in self.residues:
            json_data["residues"].append(r.to_json())
        json_data["states"] = []
        for s in self.states:
            json_data["states"].append(s.to_json())
        json_data["bound_to"] = []
        for b in self.bound_to:
            json_data["bound_to"].append(actor_to_json(b))
        json_data["unbound_from"] = []
        for b in self.unbound_from:
            json_data["unbound_from"].append(actor_to_json(b))
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create Protoform object from JSON representation."""
        uniprotid = json_data["uniprotid"]

        regions = None
        if "regions" in json_data.keys():
            regions = []
            for region in json_data["regions"]:
                regions.append(Region.from_json(region))

        sites = None
        if "sites" in json_data.keys():
            sites = []
            for site in json_data["sites"]:
                sites.append(Site.from_json(site))

        residues = None
        if "residues" in json_data.keys():
            residues = []
            for residue in json_data["residues"]:
                residues.append(Residue.from_json(residue))

        states = None
        if "states" in json_data.keys():
            states = []
            for state in json_data["states"]:
                states.append(State.from_json(state))

        bound_to = None
        if "bound_to" in json_data.keys():
            bound_to = []
            for bound in json_data["bound_to"]:
                bound_to.append(actor_from_json(bound))

        unbound_from = None
        if "bound_to" in json_data.keys():
            unbound_from = []
            for bound in json_data["unbound_from"]:
                unbound_from.append(actor_from_json(bound))

        hgnc_symbol = None
        if "hgnc_symbol" in json_data.keys():
            hgnc_symbol = json_data["hgnc_symbol"]

        synonyms = None
        if "synonyms" in json_data.keys():
            synonyms = json_data["synonyms"]

        xrefs = None
        if "xrefs" in json_data.keys():
            xrefs = json_data["xrefs"]

        location = None
        if "location" in json_data.keys():
            location = json_data["location"]

        return cls(
            uniprotid, regions=regions, sites=sites,
            residues=residues, states=states,
            bound_to=bound_to, unbound_from=unbound_from,
            hgnc_symbol=hgnc_symbol, synonyms=synonyms,
            xrefs=xrefs, location=location)

    def __repr__(self):
        """Representation of a protoform."""
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

        res = "Protoform({})".format(content)
        return res

    def __str__(self):
        """String represenation of a protoform."""
        return str(self.uniprotid)

    def same_reference(self, protoform):
        """Test if the input protoform has the same reference UniprotAC."""
        return self.uniprotid == protoform.uniprotid

    def __eq__(self, protoform):
        """Test equality."""
        equal_componets =\
            set(protoform.regions) == set(self.regions) and\
            set(protoform.sites) == set(self.sites) and\
            set(protoform.residues) == set(self.residues) and\
            set(protoform.states) == set(self.states) and\
            set(protoform.bound_to) == set(self.bound_to) and\
            set(protoform.unbound_from) == set(self.unbound_from)

        return self.same_reference(protoform) and equal_componets

    def meta_data(self):
        """Convert agent object to attrs."""
        agent_attrs = {
            "uniprotid": {self.uniprotid}
        }
        if self.hgnc_symbol is not None:
            agent_attrs["hgnc_symbol"] = normalize_to_set(self.hgnc_symbol)
        if self.synonyms is not None:
            agent_attrs["synonyms"] = normalize_to_set(self.synonyms)
        if self.xrefs is not None:
            xrefs = []
            for k, v in self.xrefs.items():
                if type(v) == list:
                    for vv in v:
                        xrefs.append((k, vv))
                else:
                    xrefs.append((k, v))
            agent_attrs["xrefs"] = normalize_to_set(xrefs)
        return agent_attrs

    def add_region(self, region):
        """Add a region to a list of regions of the entity."""
        self.regions.append(region)
        return

    def add_site(self, site):
        """Add a site to a list of sites of the entity."""
        self.sites.append(site)
        return

    def issubset(self, protoform):
        """Test if self is superentity of the input protoform."""
        contains_components =\
            set(protoform.regions).issubset(self.regions) and\
            set(protoform.sites).issubset(self.sites) and\
            set(protoform.residues).issubset(self.residues) and\
            set(protoform.states).issubset(self.states)
        return self.same_reference(protoform) and contains_components

    def generate_desc(self):
        """Generate text description of the actor."""
        return "protoform {}".format(
            self.hgnc_symbol if self.hgnc_symbol else self.uniprotid)


class Protein(Actor, PhysicalEntity):
    """Wrapper around Protoform specifying the protein product."""

    def __init__(self, protoform, name=None):
        """Initialize protein."""
        self.protoform = protoform
        self.name = name

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["protoform"] = self.protoform.to_json()
        if self.name:
            json_data["name"] = self.name

    @classmethod
    def from_json(cls, json_data):
        """Create Protoform object from JSON representation."""
        protoform = Protoform.from_json(json_data["protoform"])
        name = None
        if "name" in json_data:
            name = json_data["name"]
        return cls(protoform, name)

    def __str__(self):
        """String represenation of a protoform."""
        rep = str(self.protoform.uniprotid)
        if self.name:
            rep += "_" + self.name
        return rep

    def __repr__(self):
        """Representation of a protoform."""
        return "Protein(protoform={}, name={}".format(
            self.protoform.__repr__(), self.name)

    def meta_data(self):
        """Convert agent object to attrs."""
        agent_attrs = self.protoform.meta_data()
        if self.name is not None:
            agent_attrs["name"] = {self.name}

    def generate_desc(self):
        """Generate text description of the actor."""
        return "protein {} (product of the {})".format(
            self.name,
            self.protoform.generate_desc())


class Region(PhysicalEntity):
    """Class for a conserved protoform region."""

    def __init__(self, name=None, interproid=None, start=None, end=None,
                 order=None, sites=None, residues=None, states=None,
                 bound_to=None, unbound_from=None, label=None):
        """Initialize kami region object."""
        self.name = name
        self.interproid = interproid
        if start is not None and end is not None:
            if start > end or type(start) != int or type(end) != int:
                raise KamiEntityError(
                    "Region sequence interval {}-{} is not valid".format(
                        start, end))

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

        self.bound_to = normalize_to_iterable(bound_to)
        self.unbound_from = normalize_to_iterable(unbound_from)
        return

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        if self.name:
            json_data["name"] = self.name
        if self.interproid:
            json_data["interproid"] = self.interproid
        if self.start:
            json_data["start"] = self.start
        if self.end:
            json_data["end"] = self.end
        if self.order:
            json_data["order"] = self.order
        if self.label:
            json_data["label"] = self.label
        json_data["sites"] = []
        for s in self.sites:
            json_data["sites"].append(s.to_json())
        json_data["residues"] = []
        for r in self.residues:
            json_data["residues"].append(r.to_json())
        json_data["states"] = []
        for s in self.states:
            json_data["states"].append(s.to_json())
        json_data["bound_to"] = []
        for b in self.bound_to:
            json_data["bound_to"].append(actor_to_json(b))
        json_data["unbound_from"] = []
        for b in self.unbound_from:
            json_data["unbound_from"].append(actor_to_json(b))
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create Region object from JSON representation."""
        name = None
        if "name" in json_data.keys():
            name = json_data["name"]

        interproid = None
        if "interproid" in json_data.keys():
            interproid = json_data["interproid"]

        start = None
        if "start" in json_data.keys():
            start = json_data["start"]

        end = None
        if "end" in json_data.keys():
            end = json_data["end"]

        order = None
        if "order" in json_data.keys():
            order = json_data["order"]

        label = None
        if "label" in json_data.keys():
            label = json_data["label"]

        sites = None
        if "sites" in json_data.keys():
            sites = []
            for site in json_data["sites"]:
                sites.append(Site.from_json(site))

        residues = None
        if "residues" in json_data.keys():
            residues = []
            for residue in json_data["residues"]:
                residues.append(Residue.from_json(residue))

        states = None
        if "states" in json_data.keys():
            states = []
            for state in json_data["states"]:
                states.append(State.from_json(state))

        bound_to = None
        if "bound_to" in json_data.keys():
            bound_to = []
            for bound in json_data["bound_to"]:
                bound_to.append(actor_from_json(bound))

        unbound_from = None
        if "bound_to" in json_data.keys():
            unbound_from = []
            for bound in json_data["unbound_from"]:
                unbound_from.append(actor_from_json(bound))

        return cls(
            name=name, interproid=interproid, start=start, end=end,
            order=order, sites=sites, residues=residues, states=states,
            bound_to=bound_to, unbound_from=unbound_from, label=label)

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
        if self.label is not None:
            components.append("label='{}'".format(self.label))

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
        if self.label:
            res += "_{}".format(self.label)

        return res

    def same_reference(self, protoform):
        """TODO: elaborate, Test if the input protoform has the same reference UniprotAC."""
        return self.name == protoform.name

    def __eq__(self, region):
        """Test equality."""
        equal_componets =\
            set(region.sites) == set(self.sites) and\
            set(region.residues) == set(self.residues) and\
            set(region.states) == set(self.states) and\
            set(region.bound_to) == set(self.bound_to) and\
            set(region.unbound_from) == set(self.unbound_from)

        return self.same_reference(region) and equal_componets

    def meta_data(self):
        """Get a dictionary with region's meta-data."""
        res = dict()
        if self.interproid:
            res["interproid"] = self.interproid
        if self.name:
            res["name"] = normalize_to_set(self.name)
        if self.label:
            res["label"] = normalize_to_set(self.label)
        return res

    def location(self):
        """Get a dictionary with region's location."""
        res = dict()
        if self.start:
            res["start"] = {self.start}
        if self.end:
            res["end"] = {self.end}
        if self.order:
            res["order"] = {self.order}
        return res

    def add_site(self, site):
        """Add a site to a list of sites of the entity."""
        self.sites.append(site)
        return

    def issubset(self, region):
        """Test if self is superentity of the input region."""
        for site in self.sites:
            found_in_region = False
            for reference_site in region.sites:
                if site.issubset(reference_site):
                    found_in_region = True
                    break
            if not found_in_region:
                return False
        for residue in self.residues:
            found_in_region = False
            for reference_residue in region.residues:
                if residue.issubset(reference_residue):
                    found_in_region = True
                    break
            if not found_in_region:
                return False
        for state in self.states:
            found_in_region = False
            for reference_state in region.states:
                if state.issubset(reference_state):
                    found_in_region = True
                    break
            if not found_in_region:
                return False

        return self.same_reference(region)

    def generate_desc(self):
        """Generate text description of the actor."""
        return "region {}{}".format(
            self.name if self.name else "",
            "({}-{})".format(self.start, self.end)
            if self.start and self.end
            else "")


class Site(PhysicalEntity):
    """Class for a protoform's interaction site."""

    def __init__(self, name=None, interproid=None, start=None, end=None,
                 order=None, residues=None, states=None,
                 bound_to=None, unbound_from=None, label=None):
        """Initialize kami site object."""
        self.name = name
        self.interproid = interproid
        if start is not None and end is not None:
            if start > end or type(start) != int or type(end) != int:
                raise KamiEntityError(
                    "Region sequence interval {}-{} is not valid".format(
                        start, end))

        self.start = start
        self.end = end
        self.order = order
        self.label = label

        if residues is None:
            residues = []
        self.residues = residues

        if states is None:
            states = []
        self.states = states

        self.bound_to = normalize_to_iterable(bound_to)
        self.unbound_from = normalize_to_iterable(unbound_from)
        return

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["name"] = self.name
        json_data["interproid"] = self.interproid
        json_data["start"] = self.start
        json_data["end"] = self.end
        json_data["order"] = self.order
        json_data["label"] = self.label
        json_data["sites"] = []
        json_data["residues"] = []
        for r in self.residues:
            json_data["residues"].append(r.to_json())
        json_data["states"] = []
        for s in self.states:
            json_data["states"].append(s.to_json())
        json_data["bound_to"] = []
        for b in self.bound_to:
            json_data["bound_to"].append(actor_to_json(b))
        json_data["unbound_from"] = []
        for b in self.unbound_from:
            json_data["unbound_from"].append(actor_to_json(b))
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create Site object from JSON representation."""
        name = None
        if "name" in json_data.keys():
            name = json_data["name"]

        interproid = None
        if "interproid" in json_data.keys():
            interproid = json_data["interproid"]

        start = None
        if "start" in json_data.keys():
            start = json_data["start"]

        end = None
        if "end" in json_data.keys():
            end = json_data["end"]

        order = None
        if "order" in json_data.keys():
            order = json_data["order"]

        label = None
        if "label" in json_data.keys():
            label = json_data["label"]

        residues = None
        if "residues" in json_data.keys():
            residues = []
            for residue in json_data["residues"]:
                residues.append(Residue.from_json(residue))

        states = None
        if "states" in json_data.keys():
            states = []
            for state in json_data["states"]:
                states.append(State.from_json(state))

        bound_to = None
        if "bound_to" in json_data.keys():
            bound_to = []
            for bound in json_data["bound_to"]:
                bound_to.append(actor_from_json(bound))

        unbound_from = None
        if "bound_to" in json_data.keys():
            unbound_from = []
            for bound in json_data["unbound_from"]:
                unbound_from.append(actor_from_json(bound))

        return cls(
            name=name, interproid=interproid, start=start, end=end,
            order=order, residues=residues, states=states,
            bound_to=bound_to, unbound_from=unbound_from, label=label)

    def __repr__(self):
        """Representation of a site."""
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
        if self.label is not None:
            components.append("label='{}'".format(self.label))

        if len(components) > 0:
            content = ", ".join(components)

        res = "Site({})".format(content)
        return res

    def __str__(self):
        """String representation of a site."""
        res = "site"
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
        if self.label:
            res += "_{}".format(self.label)
        return res

    def meta_data(self):
        """Get a dictionary with site's meta-data."""
        res = dict()
        if self.interproid:
            res["interproid"] = self.interproid
        if self.name:
            res["name"] = normalize_to_set(self.name)
        if self.label:
            res["label"] = normalize_to_set(self.label)
        return res

    def location(self):
        """Get a dictionary with site's location."""
        res = dict()
        if self.start is not None:
            res["start"] = {self.start}
        if self.end is not None:
            res["end"] = {self.end}
        if self.order:
            res["order"] = {self.order}
        return res

    def same_reference(self, protoform):
        """TODO: elaborate, Test if the input protoform has the same reference UniprotAC."""
        return self.name == protoform.name

    def issubset(self, site):
        """Test if self is superentity of the input site."""
        for residue in self.residues:
            found_in_region = False
            for reference_residue in site.residues:
                if residue.issubset(reference_residue):
                    found_in_region = True
                    break
            if not found_in_region:
                return False
        for state in self.states:
            found_in_region = False
            for reference_state in site.states:
                if state.issubset(reference_state):
                    found_in_region = True
                    break
            if not found_in_region:
                return False

        return self.same_reference(site)

    def generate_desc(self):
        """Generate text description of the actor."""
        return "site {}{}".format(
            self.name if self.name else "",
            "({}-{})".format(self.start, self.end)
            if self.start and self.end
            else "")


class Residue():
    """Class for a residue."""

    def __init__(self, aa, loc=None, state=None, test=True):
        """Init residue object."""
        self.aa = normalize_to_set(aa)
        if loc is not None:
            self.loc = int(loc)
        else:
            self.loc = None
        self.state = state
        self.test = normalize_to_set(test)

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["aa"] = list(self.aa)
        json_data["test"] = list(self.test)
        if self.loc:
            json_data["loc"] = self.loc
        if self.state:
            json_data["state"] = self.state.to_json()
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create Residue object from JSON representation."""
        aa = json_data["aa"]
        loc = None
        if "loc" in json_data.keys():
            loc = json_data["loc"]
        state = None
        if "state" in json_data.keys():
            state = State.from_json(json_data["state"])
        test = True
        if "test" in json_data.keys():
            test = normalize_to_set(json_data["test"])
        return cls(aa, loc, state, test)

    def __repr__(self):
        """Representation of a site."""
        content = ""

        components = ["aa={}".format(self.aa)]
        if self.loc:
            components.append("loc={}".format(self.loc))
        if self.state:
            components.append("state={}".format(self.state.__repr__()))
        if self.test:
            components.append("test={}".format(self.test))
        if len(components) > 0:
            content = ", ".join(components)

        res = "Residue({})".format(content)
        return res

    def __str__(self):
        """Str representation of residue."""
        if self.test is False:
            res = "not_"
        else:
            res = ""
        res += "".join(self.aa)
        if self.loc:
            res += str(self.loc)
        return res

    def meta_data(self):
        """Get a dictionary with residue's meta-data."""
        res = dict()
        res["aa"] = self.aa
        res["test"] = self.test
        return res

    def location(self):
        """Get a dictionary with residue's location."""
        res = dict()
        if self.loc is not None:
            res["loc"] = {int(self.loc)}
        return res

    def issubset(self, residue):
        residue_has_state = True
        if self.state:
            if residue.state:
                residue_has_state = self.state == residue.state
            else:
                residue_has_state = False
        residue_has_loc = True
        if residue.loc:
            if self.loc:
                residue_has_loc = self.loc == residue.loc
            else:
                residue_has_loc = False
        return (
            self.aa.issubset(residue.aa) and
            residue_has_loc and
            self.test.issubset(residue.test) and
            residue_has_state)

    def generate_desc(self):
        """Generate text description of the actor."""
        keys_locs = [
            "{}{}".format(el, self.loc if self.loc else "")
            for el in self.aa
        ]
        return "residue{} {}".format(
            "s" if len(keys_locs) > 1 else "",
            ", ".join(keys_locs))


class State(object):
    """Class for a KAMI state."""

    def __init__(self, name, test=True):
        """Init kami state object."""
        self.name = name
        self.test = test

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["name"] = self.name
        json_data["test"] = self.test
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create Site object from JSON representation."""
        name = json_data["name"]
        test = True
        if "test" in json_data.keys():
            test = normalize_to_set(json_data["test"])
        return cls(name, test)

    def __repr__(self):
        """Representation of a state."""
        return "State(name='{}', test={})".format(self.name, self.test)

    def __str__(self):
        """Str representation of a state."""
        res = str(self.name)
        return res

    def __eq__(self, state):
        """Test equality."""
        return self.name == state.name and self.test == state.test

    def meta_data(self):
        """Convert agent object to attrs."""
        return {
            "name": normalize_to_set(self.name),
            "test": normalize_to_set(self.test)
        }

    def generate_desc(self):
        """Generate text description of the actor."""
        return "state {}({})".format(
            self.name, self.test)


class RegionActor(Actor):
    """Class for a region of a protoform as an actor of PPI."""

    def __init__(self, protoform, region, variant_name=None):
        """Initialize RegionActor object."""
        self.region = region
        self.protoform = protoform
        self.variant_name = variant_name

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["protoform"] = self.protoform.to_json()
        json_data["region"] = self.region.to_json()
        if self.variant_name:
            json_data["variant_name"] = self.variant_name
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create RegionActor object from JSON representation."""
        protoform = Protoform.from_json(json_data["protoform"])
        region = Region.from_json(json_data["region"])
        variant_name = None
        if "variant_name" in json_data:
            variant_name = json_data["variant_name"]
        return cls(protoform, region, variant_name)

    def __repr__(self):
        """Representation of a region actor object."""
        res = "RegionActor(protoform={}, region={}".format(
            self.protoform.__repr__(), self.region.__repr__())
        if self.variant_name:
            res += ", variant_name={}".format(self.variant_name)
        return res + ")"

    def __str__(self):
        """String representation of a RegionActor object."""
        res = str(self.region) + "_"
        res += str(self.protoform)
        if self.variant_name:
            res += self.variant_name
        return res

    def generate_desc(self):
        """Generate text description of the actor."""
        return "{} of the {}".format(
            self.region.generate_desc(),
            Protein(self.protoform, self.variant_name).generate_desc()
            if self.variant_name
            else self.protoform.generate_desc())


class SiteActor(Actor):
    """Class for a site of a protoform as an actor of PPI."""

    def __init__(self, protoform, site, region=None, variant_name=None):
        """Initialize SiteActor object."""
        self.site = site
        # We normalize region to be iterable
        self.region = normalize_to_iterable(region)
        self.protoform = protoform
        self.variant_name = variant_name

    def to_json(self):
        """Convert to its JSON repr."""
        json_data = {}
        json_data["protoform"] = self.protoform.to_json()
        if self.region:
            json_data["region"] = self.region.to_json()
        json_data["site"] = self.site.to_json()
        if self.variant_name:
            json_data["variant_name"] = self.variant_name
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create RegionActor object from JSON representation."""
        protoform = Protoform.from_json(json_data["protoform"])
        site = Site.from_json(json_data["site"])
        region = None
        if "region" in json_data.keys():
            region = Region.from_json(json_data["region"])
        variant_name = None
        if "variant_name" in json_data:
            variant_name = json_data["variant_name"]
        return cls(protoform, site, region, variant_name)

    def __repr__(self):
        """Representation of a site actor object."""
        content = ""
        if self.variant_name is not None:
            content += "variant_name={}, ".format(self.variant_name)
        if self.region is not None:
            content += "region={}, ".format(self.region.__repr__())
        content += "site={}".format(self.site.__repr__())

        return "SiteActor(protoform={}, {})".format(
            self.protoform.__repr__(), content)

    def __str__(self):
        """String representation of a SiteActor object."""
        res = str(self.protoform)
        if self.variant_name is not None:
            res += "_" + str(self.variant_name)
        if self.region is not None:
            for r in self.region:
                res += "_" + str(r)
        res += "_" + str(self.site)
        return res

    def generate_desc(self):
        """Generate text description of the actor."""
        regions_desc = " and ".join(
            [r.generate_desc() for r in self.region])
        return "{}{} of the {}".format(
            self.site.generate_desc(),
            ""
            if not len(regions_desc) == 0
            else " of the {}".format(regions_desc),
            Protein(self.protoform, self.variant_name).generate_desc()
            if self.variant_name
            else self.protoform.generate_desc())
