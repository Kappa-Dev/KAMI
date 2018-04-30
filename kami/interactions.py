"""Collection of classes implementing interactions."""
from kami.entities import (Gene, SiteActor, RegionActor)


class Interaction(object):
    """Base class for Kami interaction."""

    def to_attrs(self):
        """Convert interaction to attribute dictionary."""
        attrs = dict()
        if self.rate is not None:
            attrs["rate"] = {self.rate}
        if self.annotation is not None:
            attrs["text"] = {self.annotation}
        return attrs


class Modification(Interaction):
    """Class for Kami mod interaction."""

    def __init__(self, enzyme, substrate, mod_target,
                 mod_value=True, rate=None, annotation=None):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate = substrate
        self.target = mod_target
        self.value = mod_value
        self.rate = rate
        self.annotation = annotation
        return

    def __str__(self):
        """String representation of Modification class."""
        res = "Modification:\n"
        res += "\tEnzyme: {}\n".format(self.enzyme)
        res += "\tSubstrate: {}\n".format(self.substrate)
        res += "\tMod target: {}\n".format(self.target)
        res += "\tValue: {}\n".format(self.value)
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        if self.annotation is not None:
            res += "\tAnnotation: {}\n".format(self.annotation)
        return res

    def __repr__(self):
        """Representation of a Modification object."""
        enzyme_rep = self.enzyme.__repr__()
        substrate_rep = self.substrate.__repr__()
        mod_target = self.target.__repr__()

        res = "Modification(" +\
            "enzyme={}, substrate={}, target={}, value={}".format(
                enzyme_rep, substrate_rep, mod_target, self.value)
        if self.rate is not None:
            res += ", rate={}".format(self.rate)
        if self.annotation is not None:
            res += ", annotation={}".format(str(self.annotation))
        res += ")"
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


class Binding(Interaction):
    """Class for Kami binary binding interaction."""

    def __init__(self, left, right,
                 rate=None, annotation=None):
        """Initialize binary binding."""
        self.left = left
        self.right = right
        self.rate = rate
        self.annotation = annotation

    def __str__(self):
        """String representation of Binding class."""
        res = "Binding: {} binds {}\n".format(str(self.left), str(self.right))
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        if self.annotation is not None:
            res += "\tAnnotation: {}\n".format(self.annotation)
        return res

    def __repr__(self):
        """Representation of a Binding object."""
        res = "Binding(left={}, right={}".format(
            self.left.__repr__(), self.right.__repr__())
        if self.rate is not None:
            res += ", rate={}".format(self.rate)
        if self.annotation is not None:
            res += ", annotation={}".format(self.annotation)
        res += ")"
        return res


class Unbinding(Interaction):
    """Class for Kami unbinding interaction."""

    def __init__(self, left, right,
                 rate=None, annotation=None):
        """Initialize unbinding."""
        self.left = left
        self.right = right
        self.rate = rate
        self.annotation = annotation

    def __str__(self):
        """String representation of Unbinding class."""
        res = "Unbinding: {} unbinds {}\n".format(
            str(self.left), str(self.right))
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        if self.annotation is not None:
            res += "\tAnnotation: {}\n".format(self.annotation)
        return res

    def __repr__(self):
        """Representation of a Unbinding object."""
        res = "Unbinding(left={}, right={}".format(
            self.left.__repr__(), self.right.__repr__())
        if self.rate is not None:
            res += ", rate={}".format(self.rate)
        if self.annotation is not None:
            res += ", annotation={}".format(self.annotation)
        res += ")"
        return res


class AutoModification(Modification):
    """Class for Kami automodification interaction."""

    def __init__(self, enzyme, target, value=True,
                 substrate_region=None, substrate_site=None, rate=None,
                 annotation=None):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate_region = substrate_region
        self.substrate_site = substrate_site
        self.target = target
        self.value = value
        self.rate = rate
        self.annotation = annotation
        return

    def __str__(self):
        """String representation of an AutoModification object."""
        res = "Modification:\n"
        res += "\tEnzyme: {}\n".format(self.enzyme)
        if self.substrate_region is not None:
            res += "Substrate region: {}\n".format(self.substrate_region)
        if self.substrate_site is not None:
            res += "Substrate site: {}\n".format(self.substrate_site)
        res += "\tMod target: {}\n".format(self.target)
        res += "\tValue: {}\n".format(self.value)
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        if self.annotation is not None:
            res += "\tAnnotation: {}\n".format(self.annotation)
        return res

    def __repr__(self):
        """Representation of an AutoModification object."""
        enzyme_rep = self.enzyme.__repr__()
        mod_target = self.target.__repr__()

        res = "AutoModification(enzyme={}, target={}, value={}".format(
            enzyme_rep, mod_target, self.value)
        if self.substrate_region is not None:
            res += ", substrate_region={}".format(
                self.substrate_region.__repr__())
        if self.substrate_site is not None:
            res += ", substrate_site={}".format(
                self.substrate_site.__repr__())
        if self.rate is not None:
            res += ", rate={}".format(self.rate)
        if self.annotation is not None:
            res += ", annotation={}".format(str(self.annotation))
        res += ")"
        return res


class AnonymousModification(Modification):
    """Class for Kami anonymous modification interaction."""

    def __init__(self, substrate, target, value=True,
                 rate=None, annotation=None):
        """Initialize modification."""
        self.enzyme = None
        self.substrate = substrate
        self.target = target
        self.value = value
        self.rate = rate
        self.annotation = annotation

    def __str__(self):
        """String representation of an AnonymousModification object."""
        res = "AnonymousModification:\n"
        res += "\tSubstrate: %s\n" % self.substrate
        res += "\tMod target: %s\n" % self.target
        res += "\tValue: %s\n" % self.value
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        if self.annotation is not None:
            res += "\tAnnotation: {}\n".format(self.annotation)
        return res

    def __repr__(self):
        """Representation of an AnonymousModification object."""
        substrate_rep = self.substrate.__repr__()
        mod_target = self.target.__repr__()

        res = "AnonymousModification(" +\
            "enzyme=None, substrate={}, target={}, value={}".format(
                substrate_rep, mod_target, self.value)
        if self.rate is not None:
            res += ", rate={}".format(self.rate)
        if self.annotation is not None:
            res += ", annotation={}".format(self.annotation)
        res += ")"
        return res


class TransModification(Modification):
    """Class for Kami transmodification interaction."""

    def __init__(self, enzyme, substrate, target, value=True,
                 enzyme_bnd_region=None, enzyme_bnd_site=None,
                 substrate_bnd_region=None, substrate_bnd_site=None,
                 rate=None, annotation=None):
        """Initialize modification."""
        self.enzyme = enzyme
        self.substrate = substrate
        self.target = target
        self.value = value
        self.enzyme_bnd_region = enzyme_bnd_region
        self.enzyme_bnd_site = enzyme_bnd_site
        self.substrate_bnd_region = substrate_bnd_region
        self.substrate_bnd_site = substrate_bnd_site
        self.rate = rate
        self.annotation = annotation
        return

    def __str__(self):
        """String representation of TransModification class."""
        res = "TransModification:\n"
        res += "\tEnzyme: {}\n".format(self.enzyme)
        res += "\tSubstrate: {}\n".format(self.substrate)
        res += "\tMod target: {}\n".format(self.target)
        res += "\tValue: {}\n".format(self.value)

        if self.enzyme_bnd_region is not None:
            res += "\tEnzyme binding region: {}\n".format(
                self.enzyme_bnd_region)
        if self.enzyme_bnd_site is not None:
            res += "\tEnzyme bindind site: {}\n".format(
                self.enzyme_bnd_site)
        if self.substrate_bnd_region is not None:
            res += "\tSubstrate binding region: {}\n".format(
                self.substrate_bnd_region)
        if self.substrate_bnd_site is not None:
            res += "\tSubstrate binding site: {}\n".format(
                self.substrate_bnd_site)
        if self.rate is not None:
            res += "\tRate: {}\n".format(self.rate)
        if self.annotation is not None:
            res += "\tAnnotation: {}\n".format(self.annotation)
        return res

    def __repr__(self):
        """Representation of a TransModification object."""
        enzyme_rep = self.enzyme.__repr__()
        substrate_rep = self.substrate.__repr__()
        mod_target = self.target.__repr__()

        res = "TransModification(" +\
            "enzyme={}, substrate={}, target={}, value={}".format(
                enzyme_rep, substrate_rep, mod_target, self.value)

        if self.enzyme_bnd_region is not None:
            res += ", enzyme_bnd_region={}".format(
                self.enzyme_bnd_region.__repr__())
        if self.enzyme_bnd_site is not None:
            res += ", enzyme_bnd_site={}".format(
                self.enzyme_bnd_site.__repr__())
        if self.substrate_bnd_region is not None:
            res += ", substrate_bnd_region={}".format(
                self.substrate_bnd_region.__repr__())
        if self.substrate_bnd_site is not None:
            res += ", substrate_bnd_site={}".format(
                self.substrate_bnd_site.__repr__())
        if self.rate is not None:
            res += ", rate={}".format(self.rate)
        if self.annotation is not None:
            res += ", annotation={}".format(str(self.annotation))
        res += ")"
        return res
