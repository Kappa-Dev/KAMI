"""Collection of classes implementing interactions."""
from kami.entities import (Gene, SiteActor, RegionActor, Actor)
from kami.exceptions import KamiError


class Interaction:
    """Base class for Kami interaction."""


class Modification(Interaction):
    """Class for Kami mod interaction."""

    def __init__(self, enzyme, substrate, mod_target,
                 mod_value=True, annotation=None, direct=False):
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

    def __init__(self, enzyme_agent, mod_target, mod_value=True,
                 enz_region=None, sub_region=None, annotation=None,
                 direct=False):
        """Initialize modification."""
        self.enzyme = enzyme_agent
        self.enzyme_region = enz_region
        self.substrate_region = sub_region
        self.target = mod_target
        self.value = mod_value
        self.annotation = annotation
        self.direct = direct
        return


class TransModification(Modification):
    """Class for Kami trans mod interaction."""

    def __init__(self, enzyme, substrate, mod_target, mod_value=True,
                 annotation=None, direct=False):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate = enzyme
        self.target = mod_target
        self.value = mod_value
        self.annotation = annotation
        self.direct = direct
        return


class AnonymousModification(Modification):
    """Class for Kami anonymous mod interaction."""

    def __init__(self, substrate_agent, mod_target, mod_value,
                 annotation=None, direct=False):
        """Initialize modification."""
        self.enzyme = None
        self.substrate = substrate_agent
        self.target = mod_target
        self.value = mod_value
        self.annotation = annotation
        self.direct = direct


class Binding:
    """Class for Kami binary binding interaction."""

    def __init__(self, left_members, right_members,
                 annotation=None, direct=True):
        """Initialize binary binding."""
        self.left = left_members
        self.right = right_members
        self.annotation = annotation
        self.direct = direct

    def __str__(self):
        """String representation of Binding class."""
        res = "Binding:\n"
        res += "\tLeft members: %s\n" %\
            ", ".join([str(m) for m in self.left])
        res += "\tRight members: %s\n" %\
            ", ".join([str(m) for m in self.right])
        res += "\tDirect? %s\n" % self.direct
        return res


class Complex:
    """Class for Kami representation of complex."""

    def __init__(self, members, annotation=None):
        """Initialize Kami complex."""
        self.members = members
        self.annotation = annotation
