"""Unit testing of entity identification used in aggregation."""
from kami.aggregation import identifiers
from kami.entities import (Gene, Region, Residue,
                           Site, State)
from kami.hierarchy import KamiHierarchy
# from kami.exceptions import KamiError


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
        self.region_id = self.hierarchy.add_region(named_region, self.gene_id)
        self.hierarchy.add_region(interval_region, self.gene_id)
        self.hierarchy.add_region(named_ordered_region1, self.gene_id)
        self.hierarchy.add_region(named_ordered_region2, self.gene_id)

        named_site = Site("ATP-binding")
        interval_site = Site(start=100, end=200)
        named_ordered_site1 = Site("pY", order=1)
        named_ordered_site2 = Site("pY", order=2)
        self.site_id = self.hierarchy.add_site(named_site, self.gene_id)
        self.hierarchy.add_site(interval_site, self.gene_id)
        self.hierarchy.add_site(named_ordered_site1, self.gene_id)
        self.hierarchy.add_site(named_ordered_site2, self.gene_id)

        residue = Residue("Y", 150)
        residue_no_loc = Residue("T")
        self.residue_id = self.hierarchy.add_residue(residue, self.gene_id)
        self.hierarchy.add_residue(residue_no_loc, self.gene_id)

        residue_state = State("activity", True)
        site_state = State("activity", True)
        region_state = State("activity", True)
        gene_state = State("activity", True)

        self.hierarchy.add_state(residue_state, self.residue_id)
        self.hierarchy.add_state(site_state, self.site_id)
        self.hierarchy.add_state(region_state, self.region_id)
        self.hierarchy.add_state(gene_state, self.gene_id)

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
        region1 = Region("SH2-3")
        result1 = identifiers.identify_region(
            self.hierarchy, region1, self.gene_id)
        assert(result1 == self.region_id)

    def test_identify_site(self):
        """Test site identification."""
        pass

    def test_identify_residue(self):
        """Test residue identification."""
        pass

    def test_identify_state(self):
        """Test state identification."""
        pass
