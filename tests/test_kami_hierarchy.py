"""Tests related to KamiHierarchy data structure."""
from regraph import print_graph

from kami.entities import (Gene, Region, Site, Residue,
                           State, RegionActor, SiteActor)
from kami.interactions import Binding, Modification
from kami.hierarchy import KamiHierarchy
from kami.aggregation.identifiers import identify_gene


class TestKamiHierarchy(object):
    """Class for testing KAMI hierarchy."""

    def __init__(self):
        """Initialize test class with a hierarchy."""
        self.hierarchy = KamiHierarchy()

        egfr = Gene("P00533")
        fgfr1 = Gene("P11362")
        fgfr1_pysite = SiteActor(
            Gene("P11362"),
            Site("pY", residues=[
                Residue(
                    "Y", 463, State("phosphorylation", True))]))
        abl1_sh2 = RegionActor(
            Gene("P00519"),
            Region("SH2"))

        target = Residue(
            "Y", 463, State("phosphorylation", False))
        modification = Modification(
            enzyme=egfr,
            substrate=fgfr1,
            target=target)
        binding = Binding(abl1_sh2, fgfr1_pysite)

        self.hierarchy.add_interactions(
            [modification, binding])

    def test_empty_hierarchy(self):
        """Test getters for various hierarchy components."""
        hierarchy = KamiHierarchy()
        assert(hierarchy.action_graph is None)
        assert(len(hierarchy.nuggets()) == 0)
        assert(hierarchy.empty())

        json_hierarchy = hierarchy.to_json()
        new_hierarchy = KamiHierarchy.from_json(json_hierarchy)
        assert(isinstance(new_hierarchy, KamiHierarchy))
        assert(new_hierarchy == hierarchy)

        hierarchy.export("test_empty_hierarchy.json")
        new_hierarchy = KamiHierarchy.load("test_empty_hierarchy.json")
        assert(isinstance(new_hierarchy, KamiHierarchy))
        assert(new_hierarchy == hierarchy)

        assert(hierarchy.mod_template is
               hierarchy.node["mod_template"].graph)
        assert(hierarchy.bnd_template is hierarchy.node["bnd_template"].graph)
        assert(hierarchy.semantic_action_graph is
               hierarchy.node["semantic_action_graph"].graph)

    def test_non_empty_hierarchy(self):
        """."""
        hierarchy = KamiHierarchy()

        plcg1_pY1253 = Gene(
            "P19174",
            synonyms=["PLCG1"],
            residues=[Residue(
                "Y", 1253,
                state=State("phosphorylation", True)
            )]
        )
        sh2 = Region(name="SH2")
        abl1 = Gene(
            "P00519", synonyms=["ABL1"]
        )
        abl1_sh2 = RegionActor(abl1, sh2)
        bnd = Binding(plcg1_pY1253, abl1_sh2)

        hierarchy.add_interactions([bnd], hierarchy)
        assert(hierarchy.empty() is False)

        hierarchy.export("test_non_empty_hierarchy.json")
        new_hierarchy = KamiHierarchy.load("test_non_empty_hierarchy.json")
        assert(isinstance(new_hierarchy, KamiHierarchy))
        assert(("action_graph", "kami") in new_hierarchy.edges())
        assert(new_hierarchy == hierarchy)

    def test_add_gene_component(self):
        gene = identify_gene(self.hierarchy, Gene("P00533"))

        residue = Residue("Y", 200)
        residue_id = self.hierarchy.add_residue(residue, gene)
        assert((residue_id, gene) in self.hierarchy.action_graph.edges())
        for region in self.hierarchy.get_attached_regions(gene):
            if "start" in self.hierarchy.action_graph.edge[region][gene].keys() and\
               "end" in self.hierarchy.action_graph.edge[region][gene].keys() and\
               min(self.hierarchy.action_graph.edge[region][gene]["start"]) < 200 and\
               max(self.hierarchy.action_graph.edge[region][gene]["end"]) > 200:
                assert(
                    (residue_id, region) in self.hierarchy.action_graph.edges())
        for site in self.hierarchy.get_attached_sites(gene):
            if "start" in self.hierarchy.action_graph.edge[site][gene].keys() and\
               "end" in self.hierarchy.action_graph.edge[site][gene].keys() and\
               min(self.hierarchy.action_graph.edge[site][gene]["start"]) < 200 and\
               max(self.hierarchy.action_graph.edge[site][gene]["end"]) > 200:
                assert(
                    (residue_id, site) in self.hierarchy.action_graph.edges())

        site = Site("TestSite", start=200, end=250)
        site_id = self.hierarchy.add_site(
            site, gene, semantics="pY_site", rewriting=True)

        assert((site_id, gene) in self.hierarchy.action_graph.edges())

        for region in self.hierarchy.get_attached_regions(gene):
            if "start" in self.hierarchy.action_graph.edge[region][gene].keys() and\
               "end" in self.hierarchy.action_graph.edge[region][gene].keys() and\
               min(self.hierarchy.action_graph.edge[region][gene]["start"]) < 200 and\
               max(self.hierarchy.action_graph.edge[region][gene]["end"]) > 250:
                assert(
                    (site_id, region) in self.hierarchy.action_graph.edges())

        for residue in self.hierarchy.get_attached_residues(gene):
            if "loc" in self.hierarchy.action_graph.edge[residue][gene].keys() and\
               list(self.hierarchy.action_graph.edge[residue][gene]["loc"])[0] > 200 and\
               list(self.hierarchy.action_graph.edge[residue][gene]["loc"])[0] < 250:
                assert(
                    (residue, site_id) in self.hierarchy.action_graph.edges())

        region = Region("TestRegion", start=100, end=500)
        region_id = self.hierarchy.add_region(
            region, gene, semantics="protein_kinase", rewriting=True)

        for residue in self.hierarchy.get_attached_residues(gene):
            if "loc" in self.hierarchy.action_graph.edge[residue][gene].keys() and\
               list(self.hierarchy.action_graph.edge[residue][gene]["loc"])[0] > 100 and\
               list(self.hierarchy.action_graph.edge[residue][gene]["loc"])[0] < 500:
                assert(
                    (residue, region_id) in self.hierarchy.action_graph.edges())

        for site in self.hierarchy.get_attached_sites(gene):
            if "start" in self.hierarchy.action_graph.edge[site][gene].keys() and\
               "end" in self.hierarchy.action_graph.edge[site][gene].keys() and\
               min(self.hierarchy.action_graph.edge[site][gene]["start"]) > 100 and\
               max(self.hierarchy.action_graph.edge[site][gene]["end"]) < 500:
                assert(
                    (site, region_id) in self.hierarchy.action_graph.edges())
