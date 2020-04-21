"""Set of unit tests for the KAMIql engine."""
from kami import KamiCorpus
from kamiql.engine import KAMIqlEngine


class TestKAMIql:
    """Unit tests for KAMIql."""

    def __init__(self):
        """Initialize tests."""
        # parsed = parser.parseString("a.b-c.d;").asDict()
        # print(parsed)
        pass

    def test_ag_queries(self):
        """Test queries on the action graph."""
        query1 = (
            """
            MATCH (p1:protoform)<--(r1:REGION)-->(i:interaction)-..-(n4:protoform),
            (x:protoform)-..->(y:protoform), (n200:component)
            RETURN p1, i, p2;
            """
        )

        corpus = KamiCorpus("hello")
        engine = KAMIqlEngine(corpus)
        engine.query_action_graph(query1)
