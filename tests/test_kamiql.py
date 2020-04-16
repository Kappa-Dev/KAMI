"""Set of unit tests for the KAMIql engine."""
from kamiql.parser import parse_query


class TestKAMIql:
    """Unit tests for KAMIql."""

    def __init__(self):
        """Initialize tests."""
        pass

    def test_ag_query1(self):
        query = (
            """
            MATCH (p1:protoform)<--(r1:region)--(i:interaction)-..-(p2:protoform)
            RETURN p1, i, p2;
            """
        )
        print(query)
        parse_query(query)
