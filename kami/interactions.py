"""Collection of classes implementing interactions."""
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

    def __init__(self, enzyme_actor, mod_target, mod_value=True,
                 substrate_region=None, substrate_site=None, rate=None,
                 annotation=None, direct=True):
        """Initialize modification."""
        self.enzyme = enzyme_actor
        self.substrate_region = substrate_region
        self.substrate_site = substrate_site
        self.target = mod_target
        self.value = mod_value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct
        return


class TransModification(Modification):
    """Class for Kami trans mod interaction."""

    def __init__(self, enzyme, substrate, mod_target, mod_value=True,
                 rate=None, annotation=None, direct=True):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate = enzyme
        self.target = mod_target
        self.value = mod_value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct
        return


class AnonymousModification(Modification):
    """Class for Kami anonymous mod interaction."""

    def __init__(self, substrate_agent, mod_target, mod_value,
                 rate=None, annotation=None, direct=True):
        """Initialize modification."""
        self.enzyme = None
        self.substrate = substrate_agent
        self.target = mod_target
        self.value = mod_value
        self.rate = rate
        self.annotation = annotation
        self.direct = direct


class Binding(Interaction):
    """Class for Kami binary binding interaction."""

    def __init__(self, left_members, right_members,
                 rate=None, annotation=None, direct=True):
        """Initialize binary binding."""
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


class Unbinding(Interaction):
    """Class for Kami binary unbinding interaction."""

    def __init__(self, left_members, right_members,
                 rate=None, annotation=None, direct=True):
        """Initialize binary binding."""
        self.left = left_members
        self.right = right_members
        self.rate = rate
        self.annotation = annotation
        self.direct = direct

    def __str__(self):
        """String representation of Binding class."""
        res = "Unbinding:\n"
        res += "\tLeft members: %s\n" %\
            ", ".join([str(m) for m in self.left])
        res += "\tRight members: %s\n" %\
            ", ".join([str(m) for m in self.right])
        res += "\tDirect? %s\n" % self.direct
        return res
