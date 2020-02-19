"""Unit testing of entity identification used in aggregation."""
from kami.aggregation.identifiers import EntityIdentifier
from kami import (Protoform, Region, Residue,
                  Site, State)
from kami import KamiCorpus

# from regraph.primitives import print_graph


class TestIdentifiers(object):
    """Test identifiers of entities in the action graph."""

    def __init__(self):
        """Initialize with common hierarchy."""
        self.hierarchy = KamiCorpus("test")

        protoform = Protoform("A")
        self.gene_id = self.hierarchy.add_protoform(protoform)

        named_region = Region("Kinase")
        interval_region = Region(start=100, end=200)
        named_ordered_region1 = Region("SH2", order=1)
        named_ordered_region2 = Region("SH2", order=2)
        self.named_region = self.hierarchy.add_region(
            named_region, self.gene_id)
        self.interval_region = self.hierarchy.add_region(
            interval_region, self.gene_id)
        self.named_ordered_region1 = self.hierarchy.add_region(
            named_ordered_region1, self.gene_id)
        self.named_ordered_region2 = self.hierarchy.add_region(
            named_ordered_region2, self.gene_id)

        named_site = Site("ATP binding")
        interval_site = Site(start=100, end=200)
        named_ordered_site1 = Site("pY", order=1)
        named_ordered_site2 = Site("pY", order=2)
        self.named_site = self.hierarchy.add_site(named_site, self.gene_id)
        self.interval_site = self.hierarchy.add_site(
            interval_site, self.gene_id)
        self.named_ordered_site1 = self.hierarchy.add_site(
            named_ordered_site1, self.gene_id)
        self.named_ordered_site2 = self.hierarchy.add_site(
            named_ordered_site2, self.gene_id)

        residue = Residue("Y", 150)
        residue_no_loc = Residue("T")
        self.residue = self.hierarchy.add_residue(residue, self.gene_id)
        self.residue_no_loc = self.hierarchy.add_residue(
            residue_no_loc, self.gene_id)

        residue_state = State("activity", True)
        site_state = State("activity", True)
        region_state = State("activity", True)
        gene_state = State("activity", True)

        self.residue_state = self.hierarchy.add_state(
            residue_state, self.residue)
        self.site_state = self.hierarchy.add_state(site_state, self.named_site)
        self.region_state = self.hierarchy.add_state(
            region_state, self.named_region)
        self.gene_state = self.hierarchy.add_state(gene_state, self.gene_id)

    def test_identify_gene(self):
        """Test protoform identification."""
        gene1 = Protoform("A")
        gene2 = Protoform("B")
        identifier = EntityIdentifier(
            self.hierarchy.action_graph,
            self.hierarchy.get_action_graph_typing())
        result1 = identifier.identify_gene(gene1)
        result2 = identifier.identify_gene(gene2)
        assert(result1 == self.gene_id)
        assert(result2 is None)

    def test_identify_region(self):
        """Test region identification."""
        identifier = EntityIdentifier(
            self.hierarchy.action_graph,
            self.hierarchy.get_action_graph_typing())
        res = identifier.identify_region(
            Region("Protein kinase"), self.gene_id)
        assert(res == self.named_region)
        res = identifier.identify_region(
            Region(start=101, end=199), self.gene_id)
        assert(res == self.interval_region)
        res = identifier.identify_region(
            Region("SH2"), self.gene_id)
        assert(res is None)
        res = identifier.identify_region(
            Region("SH2", order=1), self.gene_id)
        assert(res == self.named_ordered_region1)
        res = identifier.identify_region(
            Region("SH2", order=5), self.gene_id)
        assert(res is None)
        res = identifier.identify_region(
            Region("SH2", start=101, end=185, order=2),
            self.gene_id)
        assert(res == self.interval_region)

    def test_identify_site(self):
        """Test site identification."""
        identifier = EntityIdentifier(
            self.hierarchy.action_graph,
            self.hierarchy.get_action_graph_typing())
        res = identifier.identify_site(
            Site("ATP bind"), self.gene_id)
        assert(res == self.named_site)
        res = identifier.identify_site(
            Site("ATP binding site"), self.gene_id)
        assert(res == self.named_site)

        res = identifier.identify_site(
            Site(start=101, end=199), self.gene_id)
        assert(res == self.interval_site)
        res = identifier.identify_site(
            Site("pY"), self.gene_id)
        assert(res is None)
        res = identifier.identify_site(
            Site("pY", order=1), self.gene_id)
        assert(res == self.named_ordered_site1)
        res = identifier.identify_site(
            Site("pY", order=5), self.gene_id)
        assert(res is None)
        res = identifier.identify_site(
            Site("pY", start=101, end=185, order=2),
            self.gene_id)
        assert(res == self.interval_site)

    def test_identify_residue(self):
        """Test residue identification."""
        identifier = EntityIdentifier(
            self.hierarchy.action_graph,
            self.hierarchy.get_action_graph_typing())
        res = identifier.identify_residue(
            Residue("S", 150), self.gene_id)
        assert(res == self.residue)
        res = identifier.identify_residue(
            Residue("T"), self.gene_id)
        assert(res == self.residue_no_loc)
        res = identifier.identify_residue(
            Residue("S"), self.gene_id)
        assert(res is None)

    def test_identify_state(self):
        """Test state identification."""
        identifier = EntityIdentifier(
            self.hierarchy.action_graph,
            self.hierarchy.get_action_graph_typing())
        res = identifier.identify_state(
            State("activity", False), self.residue)
        assert(res == self.residue_state)
        res = identifier.identify_state(
            State("activity", False), self.named_site)
        assert(res == self.site_state)
        res = identifier.identify_state(
            State("activity", False), self.named_region)
        assert(res == self.region_state)
        res = identifier.identify_state(
            State("activity", False), self.gene_id)
        assert(res == self.gene_state)
