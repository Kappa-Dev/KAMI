"""Tests related to KamiCorpus data structure."""
from regraph import (print_graph, get_edge)

from kami import KamiCorpus
from kami import (Gene, Region, Site, Residue,
                  State, RegionActor, SiteActor)
from kami import Binding, Modification
from kami.aggregation.identifiers import EntityIdentifier


class TestKamiCorpus(object):
    """Class for testing KAMI model."""

    def __init__(self):
        """Initialize test class with a model."""
        self.model = KamiCorpus("test")

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

        self.model.add_interactions(
            [modification, binding])

    def test_empty_hierarchy(self):
        """Test getters for various model components."""
        model = KamiCorpus("test")
        assert(model.action_graph is not None)
        assert(len(model.nuggets()) == 0)
        assert(model.empty())

        model.export_json("test_empty_hierarchy.json")
        new_model = KamiCorpus.load("test", "test_empty_hierarchy.json")
        assert(isinstance(new_model, KamiCorpus))
        assert(new_model._hierarchy == model._hierarchy)

        assert(model.mod_template is
               model._hierarchy.graph["mod_template"])
        assert(model.bnd_template is model._hierarchy.graph["bnd_template"])
        assert(model.semantic_action_graph is
               model._hierarchy.graph["semantic_action_graph"])

    def test_non_empty_hierarchy(self):
        """."""
        model = KamiCorpus("test")

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

        model.add_interactions([bnd], model)
        assert(model.empty() is False)

        model.export_json("test_non_empty_hierarchy.json")
        new_model = KamiCorpus.load("test", "test_non_empty_hierarchy.json")
        assert(isinstance(new_model, KamiCorpus))
        assert(("test_action_graph", "meta_model") in new_model._hierarchy.edges())
        assert(model._hierarchy == new_model._hierarchy)

    def test_add_gene_component(self):
        identifier = EntityIdentifier(
            self.model.action_graph,
            self.model.get_action_graph_typing())
        gene = identifier.identify_gene(Gene("P00533"))

        residue = Residue("Y", 200)
        residue_id = self.model.add_residue(residue, gene)
        assert((residue_id, gene) in self.model.action_graph.edges())
        for region in self.model.get_attached_regions(gene):
            edge = get_edge(self.model.action_graph, region, gene)
            if "start" in edge.keys() and\
               "end" in edge.keys() and\
               min(edge["start"]) < 200 and\
               max(edge["end"]) > 200:
                assert(
                    (residue_id, region) in self.model.action_graph.edges())
        for site in self.model.get_attached_sites(gene):
            edge = get_edge(self.model.action_graph, site, gene)
            if "start" in edge.keys() and\
               "end" in edge.keys() and\
               min(edge["start"]) < 200 and\
               max(edge["end"]) > 200:
                assert(
                    (residue_id, site) in self.model.action_graph.edges())

        site = Site("TestSite", start=200, end=250)
        site_id = self.model.add_site(
            site, gene, semantics="pY_site", rewriting=True)

        assert((site_id, gene) in self.model.action_graph.edges())

        for region in self.model.get_attached_regions(gene):
            edge = get_edge(self.model.action_graph, region, gene)
            if "start" in edge.keys() and\
               "end" in edge.keys() and\
               min(edge["start"]) < 200 and\
               max(edge["end"]) > 250:
                assert(
                    (site_id, region) in self.model.action_graph.edges())

        for residue in self.model.get_attached_residues(gene):
            edge = get_edge(self.model.action_graph, residue, gene)
            if "loc" in edge.keys() and\
               list(edge["loc"])[0] > 200 and\
               list(edge["loc"])[0] < 250:
                assert(
                    (residue, site_id) in self.model.action_graph.edges())

        region = Region("TestRegion", start=100, end=500)
        region_id = self.model.add_region(
            region, gene, semantics="protein_kinase", rewriting=True)

        for residue in self.model.get_attached_residues(gene):
            edge = get_edge(self.model.action_graph, residue, gene)
            if "loc" in edge.keys() and\
               list(edge["loc"])[0] > 100 and\
               list(edge["loc"])[0] < 500:
                assert(
                    (residue, region_id) in self.model.action_graph.edges())

        for site in self.model.get_attached_sites(gene):
            edge = get_edge(self.model.action_graph, site, gene)
            if "start" in edge.keys() and\
               "end" in edge.keys() and\
               min(edge["start"]) > 100 and\
               max(edge["end"]) < 500:
                assert(
                    (site, region_id) in self.model.action_graph.edges())
