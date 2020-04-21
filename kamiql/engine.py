"""Collection of data structures for querying KAMI corpora and models."""
from kamiql.parser import parse_query


class KAMIqlEngine(object):
    """KAMIql engine."""

    def __init__(self, kb):
        """Initialize a KAMIqlEngine."""
        self._kb = kb

    def query_action_graph(self, query):
        """Execute a KAMIql query on the action graph."""
        patterns = parse_query(query)

        result = []
        for pattern_dict, pattern_typing in patterns:
            print(pattern_dict, pattern_typing)
            result += self._kb._hierarchy.advanced_find_matching(
                self._kb._action_graph_id,
                pattern_dict, pattern_typing)
