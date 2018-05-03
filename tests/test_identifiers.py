"""Unit testing of entity identification used in aggregation."""
from kami.aggregation import identifiers
from kami.entities import (Gene, Region, Residue,
                           Site, State)
from kami.hierarchy import KamiHierarchy

# from regraph.primitives import print_graph


class TestIdentifiers(object):
    """Test identifiers of entities in the action graph."""

    def __init__(self):
        """Initialize with common hierarchy."""
        self.hierarchy = KamiHierarchy()

        gene = Gene("A")
        self.gene_id = self.hierarchy.add_gene(gene)

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
        """Test gene identification."""
        gene1 = Gene("A")
        gene2 = Gene("B")
        result1 = identifiers.identify_gene(self.hierarchy, gene1)
        result2 = identifiers.identify_gene(self.hierarchy, gene2)
        assert(result1 == self.gene_id)
        assert(result2 is None)

    def test_identify_region(self):
        """Test region identification."""
        res = identifiers.identify_region(
            self.hierarchy, Region("Protein kinase"), self.gene_id)
        assert(res == self.named_region)
        res = identifiers.identify_region(
            self.hierarchy, Region(start=101, end=199), self.gene_id)
        assert(res == self.interval_region)
        res = identifiers.identify_region(
            self.hierarchy, Region("SH2"), self.gene_id)
        assert(res is None)
        res = identifiers.identify_region(
            self.hierarchy, Region("SH2", order=1), self.gene_id)
        assert(res == self.named_ordered_region1)
        res = identifiers.identify_region(
            self.hierarchy, Region("SH2", order=5), self.gene_id)
        assert(res is None)
        res = identifiers.identify_region(
            self.hierarchy, Region("SH2", start=101, end=185, order=2),
            self.gene_id)
        assert(res == self.interval_region)

    def test_identify_site(self):
        """Test site identification."""
        res = identifiers.identify_site(
            self.hierarchy, Site("ATP bind"), self.gene_id)
        assert(res == self.named_site)
        res = identifiers.identify_site(
            self.hierarchy, Site("ATP binding site"), self.gene_id)
        assert(res == self.named_site)

        res = identifiers.identify_site(
            self.hierarchy, Site(start=101, end=199), self.gene_id)
        assert(res == self.interval_site)
        res = identifiers.identify_site(
            self.hierarchy, Site("pY"), self.gene_id)
        assert(res is None)
        res = identifiers.identify_site(
            self.hierarchy, Site("pY", order=1), self.gene_id)
        assert(res == self.named_ordered_site1)
        res = identifiers.identify_site(
            self.hierarchy, Site("pY", order=5), self.gene_id)
        assert(res is None)
        res = identifiers.identify_site(
            self.hierarchy, Site("pY", start=101, end=185, order=2),
            self.gene_id)
        assert(res == self.interval_site)

    def test_identify_residue(self):
        """Test residue identification."""
        res = identifiers.identify_residue(
            self.hierarchy, Residue("S", 150), self.gene_id)
        assert(res == self.residue)
        res = identifiers.identify_residue(
            self.hierarchy, Residue("T"), self.gene_id)
        assert(res == self.residue_no_loc)
        res = identifiers.identify_residue(
            self.hierarchy, Residue("S"), self.gene_id)
        assert(res is None)

    def test_identify_state(self):
        """Test state identification."""
        res = identifiers.identify_state(
            self.hierarchy, State("activity", False), self.residue)
        assert(res == self.residue_state)
        res = identifiers.identify_state(
            self.hierarchy, State("activity", False), self.named_site)
        assert(res == self.site_state)
        res = identifiers.identify_state(
            self.hierarchy, State("activity", False), self.named_region)
        assert(res == self.region_state)
        res = identifiers.identify_state(
            self.hierarchy, State("activity", False), self.gene_id)
        assert(res == self.gene_state)
