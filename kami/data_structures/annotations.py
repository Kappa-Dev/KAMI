"""Collection of data structures for annotation of corpora/models."""


class CorpusAnnotation:
    """."""

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
