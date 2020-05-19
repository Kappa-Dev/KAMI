"""Collection of data structures for annotation of corpora/models."""


class GenericAnnotation:
    """Data structure for generic annotation."""

    def __init__(self, name=None, desc=None, organism=None, text=None):
        """Initialize."""
        self.name = name
        self.desc = desc
        self.organism = organism
        self.text = text

    def to_json(self):
        """Convert to JSON."""
        return {
            "name": self.name,
            "desc": self.desc,
            "organism": self.organism,
            "annotation": self.text
        }

    @classmethod
    def from_json(cls, json_data):
        """Load from JSON."""
        name = None
        desc = None
        organism = None
        text = None
        if "name" in json_data.keys():
            name = json_data["name"]
        if "desc" in json_data.keys():
            desc = json_data["desc"]
        if "organism" in json_data.keys():
            organism = json_data["organism"]
        if "text" in json_data.keys():
            text = json_data["text"]
        return cls(name, desc, organism, text)


class CorpusAnnotation(GenericAnnotation):
    """Data structure for model annotation."""

    pass


class ModelAnnotation(GenericAnnotation):
    """Data structure for model annotation."""

    pass


class ContextAnnotation(GenericAnnotation):
    """Data structure for context annotation."""

    pass
