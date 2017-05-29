"""Collection of classes implementing interactions."""


class Interaction:
    """Base class for Kami interaction."""


class Modification(Interaction):
    """Class for Kami mod interaction."""

    def __init__(self, enzyme, substrate, mod_target,
                 mod_value=True, annotation=None, direct=False):
        """Initialize modification."""
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


class AutoModification(Modification):
    """Class for Kami auto mod interaction."""

    def __init__(self, enzyme_agent, mod_target, mod_value=True,
                 enz_region=None, sub_region=None, annotation=None,
                 direct=False):
        """Initialize modification."""
        self.enzyme = enzyme_agent
        self.enz_region = enz_region
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


class BinaryBinding:
    """Class for Kami binary binding interaction."""

    def __init__(self, left_members, right_members,
                 annotation=None, direct=False):
        """Initialize binary binding."""
        self.left = left_members
        self.right = right_members
        self.annotation = annotation
        self.direct = direct


class Complex:
    """Class for Kami representation of complex."""

    def __init__(self, members, annotation=None):
        """Initialize Kami complex."""
        self.members = members
        self.annotation = annotation