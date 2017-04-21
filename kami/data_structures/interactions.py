"""."""


class Interaction:
    """Base class for Kami interaction."""


class Modification:
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
