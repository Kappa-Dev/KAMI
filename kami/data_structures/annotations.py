"""Collection of data structures for annotation of corpora/models."""


class CorpusAnnotation:
    """Data structure for annotation."""

    def __init__(self, name=None, desc=None, organism=None, text=None):
        """."""
        self.name = name
        self.desc = desc
        self.organism = organism
        self.text = text

    def to_json(self):
        return {
            "name": self.name,
            "desc": self.desc,
            "organism": self.organism,
            "annotation": self.text
        }

    @classmethod
    def from_json(cls, json_data):
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
