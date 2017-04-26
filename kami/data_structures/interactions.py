"""."""


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
        res = "Modifications:\n"
        res += "Enzyme: " + str(self.enzyme)
        res += "Substrate: " + str(self.substrate)
        res += "Mod target: " + str(self.mod_target)
        res += "Value: " + str(self.value)
        res += "Direct? " + str(self.direct)


class AutoModification:
    """."""


class TransModification:
    """."""


class AnonymousModification:
    """."""


class BinaryBinding:
    """."""


class Complex:
    """."""
