"""Collection of classes implementing interactions."""
import collections

from kami.entities import (Gene, SiteActor, RegionActor, Actor)
from kami.exceptions import KamiError


class Interaction(object):
    """Base class for Kami interaction."""

    def to_attrs(self):
        attrs = dict()
        if self.rate is not None:
            attrs["rate"] = {self.rate}
        if self.annotation is not None:
            attrs["text"] = {self.annotation}
        attrs["direct"] = {self.direct}
        return attrs


class Modification(Interaction):
    """Class for Kami mod interaction."""

    def __init__(self, enzyme, substrate, mod_target,
                 mod_value=True, rate=None, annotation=None,
                 direct=True):
        """Initialize modification."""
        if not isinstance(enzyme, Actor):
            raise KamiError(
                "Enzyme of Modification interaction should be "
                "an instance of 'kami.entities.Actor' class: "
                "'%s' received instead" % type(enzyme))
        if not isinstance(substrate, Actor):
            raise KamiError(
                "Substrate of Modification interaction should be "
                "an instance of 'kami.entities.Actor' class: "
                "'%s' received instead" % type(substrate))
        self.enzyme = enzyme
        self.substrate = substrate
        self.target = mod_target
        self.value = mod_value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct
        return

    def __str__(self):
        """String representation of Modification class."""
        res = "Modification:\n"
        res += "\tEnzyme: %s\n" % self.enzyme
        res += "\tSubstrate: %s\n" % self.substrate
        res += "\tMod target: %s\n" % self.target
        res += "\tValue: %s\n" % self.value
        res += "\tDirect? %s\n" % self.direct
        return res

    def __repr__(self):
        """Representation of a Modification object."""
        enzyme_rep = self.enzyme.__repr__()
        substrate_rep = self.substrate.__repr__()
        mod_target = self.target.__repr__()

        res = "Modification(enzyme={}, substrate={}, target={}, value={})".format(
            enzyme_rep, substrate_rep, mod_target, self.value)
        return res

    def enzyme_site(self):
        """Test if the enzyme actor is a SiteActor."""
        return isinstance(self.enzyme, SiteActor)

    def enzyme_region(self):
        """Test if the enzyme actor is a RegionActor."""
        return isinstance(self.enzyme, RegionActor)

    def enzyme_gene(self):
        """Test if the enzyme actor is a Gene."""
        return isinstance(self.enzyme, Gene)


class AutoModification(Modification):
    """Class for Kami auto mod interaction."""

    def __init__(self, enzyme, target, value=True,
                 substrate_region=None, substrate_site=None, rate=None,
                 annotation=None, direct=True):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate_region = substrate_region
        self.substrate_site = substrate_site
        self.target = target
        self.value = value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct
        return

    def __str__(self):
        """String representation of AutoModification class."""
        res = "Modification:\n"
        res += "\tEnzyme: {}\n".format(self.enzyme)
        if self.substrate_region is not None:
            res += "Substrate region: {}\n".format(self.substrate_region)
        if self.substrate_site is not None:
            res += "Substrate site: {}\n".format(self.substrate_site)
        res += "\tMod target: {}\n".format(self.target)
        res += "\tValue: {}\n".format(self.value)
        res += "\tDirect? {}\n".format(self.direct)
        return res

    def __repr__(self):
        """Representation of a AutoModificationAutoModification object."""
        enzyme_rep = self.enzyme.__repr__()
        mod_target = self.target.__repr__()

        res = "AutoModification(enzyme={}, target={}, value={}".format(
            enzyme_rep, mod_target, self.value)
        if self.substrate_region is not None:
            res += ", substrate_region={}".format(
                self.substrate_region.__repr__())
        if self. substrate_site is not None:
            res += ", substrate_site={}".format(
                self.substrate_site.__repr__())
        res += ")"
        return res


class TransModification(Modification):
    """Class for Kami trans mod interaction."""

    def __init__(self, enzyme, substrate, target, value=True,
                 rate=None, annotation=None, direct=True):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate = enzyme
        self.target = target
        self.value = value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct
        return

    def __str__(self):
        """String representation of TransModification class."""
        res = "TransModification:\n"
        res += "\tEnzyme: %s\n" % self.enzyme
        res += "\tSubstrate: %s\n" % self.substrate
        res += "\tMod target: %s\n" % self.target
        res += "\tValue: %s\n" % self.value
        res += "\tDirect? %s\n" % self.direct
        return res

    def __repr__(self):
        """Representation of a TransModification object."""
        enzyme_rep = self.enzyme.__repr__()
        substrate_rep = self.substrate.__repr__()
        mod_target = self.target.__repr__()

        res = "TransModification(enzyme={}, substrate={}, target={}, value={})".format(
            enzyme_rep, substrate_rep, mod_target, self.value)
        return res


class AnonymousModification(Modification):
    """Class for Kami anonymous mod interaction."""

    def __init__(self, substrate, target, value=True,
                 rate=None, annotation=None, direct=True):
        """Initialize modification."""
        self.enzyme = None
        self.substrate = substrate
        self.target = target
        self.value = value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct

    def __str__(self):
        """String representation of AnonymousModification class."""
        res = "AnonymousModification:\n"
        res += "\tSubstrate: %s\n" % self.substrate
        res += "\tMod target: %s\n" % self.target
        res += "\tValue: %s\n" % self.value
        res += "\tDirect? %s\n" % self.direct
        return res

    def __repr__(self):
        """Representation of a AnonymousModification object."""
        substrate_rep = self.substrate.__repr__()
        mod_target = self.target.__repr__()

        res = "AnonymousModification(enzyme=None, substrate={}, target={}, value={})".format(
            substrate_rep, mod_target, self.value)
        return res


class Binding(Interaction):
    """Class for Kami binary binding interaction."""

    def __init__(self, left_members, right_members,
                 rate=None, annotation=None, direct=True):
        """Initialize binary binding."""
        if isinstance(left_members, collections.Iterable):
            left_members = set(left_members)
        else:
            left_members = set([left_members])
        if isinstance(right_members, collections.Iterable):
            right_members = set(right_members)
        else:
            right_members = set([right_members])
        self.left = left_members
        self.right = right_members
        self.rate = rate
        self.annotation = annotation
        self.direct = direct

    def __str__(self):
        """String representation of Binding class."""
        res = "Binding:\n"
        res += "\tLeft members: {}\n".format(
            ", ".join([str(m) for m in self.left]))
        res += "\tRight members: {}\n".format(
            ", ".join([str(m) for m in self.right]))
        res += "\tDirect? {}\n".format(self.direct)
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        return res

    def __repr__(self):
        """Representation of a Binding object."""
        res = "Binding(left=[{}], right=[{}])".format(
            ", ".join(el.__repr__() for el in self.left),
            ", ".join(el.__repr__() for el in self.right))
        return res
