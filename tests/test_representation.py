"""Unit testing of nugget generators functionality."""

from regraph import print_graph

from kami.entities import (Gene, Region, RegionActor, Residue,
                           Site, SiteActor, State)
from kami.interactions import (Modification,
                               Binding,
                               AutoModification,
                               TransModification,
                               AnonymousModification)


class TestRepresentation(object):
    """Test class for black box functionality."""
    def __init__(self):
        uniprotid = "P00533"
        simple_region = Region("SH2")
        regions = [simple_region]

        sites = [Site("pY")]

        residues = [
            Residue("Y", 100),
            Residue("S", 155, State("phosphorylation", True))]

        states = [State("activity", True), State("phosphorylation", True)]

        bounds = [
            SiteActor(gene=Gene("Q07890"), site=Site("binding_site")),
            Gene("P00519")]

        self.gene = Gene(
            uniprotid,
            regions=regions,
            residues=residues,
            sites=sites,
            states=states,
            bounds=bounds,
            hgnc_symbol="EGFR",
            synonyms=["EGFR", "Epidermal growth factor receptor"])

        self.enzyme_gene = Gene("Q07890")

        self.enzyme_site_actor = SiteActor(
            gene=self.enzyme_gene,
            region=Region("Pkinase"),
            site=Site("tail"))

        self.substrate_gene = Gene("P00519")
        self.substrate_region_actor = RegionActor(
            gene=self.substrate_gene,
            region=Region("SH2"))

        self.residue_mod_target = Residue("Y", 100, State("activity", False))

    def test_complex_gene(self):
        print(self.gene)
        print(self.gene.__repr__())

    def test_modification(self):
        mod = Modification(
            enzyme=self.enzyme_site_actor,
            substrate=self.substrate_region_actor,
            mod_target=self.residue_mod_target
        )
        print(mod)
        print(mod.__repr__())

    def test_automodification(self):
        automod = AutoModification(
            enzyme=self.enzyme_site_actor,
            target=self.residue_mod_target,
            value=True,
            substrate_region=Region("SH2")
        )
        print(automod)
        print(automod.__repr__())

    def test_transmodification(self):
        mod = TransModification(
            enzyme=self.enzyme_site_actor,
            substrate=self.substrate_region_actor,
            target=self.residue_mod_target
        )
        print(mod)
        print(mod.__repr__())

    def test_anonymousmod(self):
        mod = AnonymousModification(
            substrate=self.substrate_region_actor,
            target=self.residue_mod_target)
        print(mod)
        print(mod.__repr__())

    def test_binding(self):
        bnd = Binding(
            self.substrate_region_actor,
            self.enzyme_site_actor)
        print(bnd)
        print(bnd.__repr__())
