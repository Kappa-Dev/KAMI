"""Kami exceptions."""


class KamiException(Exception):
    """Base class for all Kami exceptions."""


class KamiWarning(UserWarning):
    """Base class for Kami warnings."""


class KamiError(KamiException):
    """Class for general Kami errors."""


class IndraImportError(KamiException):
    """Class for INDRA import errors."""


class NuggetGenerationError(KamiException):
    """Class for errors in nugget generation."""


class KamiHierarchyError(KamiException):
    """Class for errors in Kami hierarchy."""


class IndraImportWarning(KamiWarning):
    """Class for INDRA import warnings."""
