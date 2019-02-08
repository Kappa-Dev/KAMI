"""Unit testing of black box functionality."""

from regraph.primitives import (print_graph)

from kami.exporters.old_kami import ag_to_edge_list
from kami import (Modification, Binding, LigandModification)
from kami import (Gene, Region, RegionActor, Residue,
                  Site, SiteActor, State)
from kami import KamiCorpus


class TestBlackBox(object):
    """Test class for black box functionality."""

    def __init__(self):
        """Initialize with an empty corpus."""
        self.corpus = KamiCorpus("test")

    def test_simple_mod_nugget(self):
        """Simple modification interaction example."""
        enz_res = Residue("S", 100, State("phospho", True))
        enz_reg = Region(
            start=150,
            end=170,
            states=[State("activity", True)]
        )
        enzyme_entity = Gene("P00533", regions=[enz_reg], residues=[enz_res])

        sub_bound_1 = Gene("P28482", states=[State("activity", True)])
        sub_bound_2 = Gene("P28482", states=[State("activity", True)])

        substrate_entity = Gene("P04049", bound_to=[sub_bound_1, sub_bound_2])

        mod_state = State("activity", False)
        value = True

        mod1 = Modification(
            enzyme_entity, substrate_entity, mod_state, value
        )
        # Create corresponding nugget in the corpus
        self.corpus.add_interaction(mod1, add_agents=True, anatomize=False)

    def test_complex_mod_nugget(self):
        """Complex modification interaction example."""
        enzyme_agent = Gene("P04049")
        enzyme_region = Region(start=100, end=200, name="lala")
        enzyme = RegionActor(enzyme_agent, enzyme_region)

        state = State("phosphorylation", True)
        reg_residue = Residue("S", 550, state)
        substrate_region = Region(
            start=500,
            end=600,
            residues=[reg_residue]
        )

        substrate_residues = [
            Residue("T", 100),
            Residue("S", 56, State("phosphorylation", True))
        ]

        substrate_state = State("activity", True)

        next_level_bound = RegionActor(
            Gene("P04637"),
            Region(start=224, end=234)
        )

        substrate_bound = Gene(
            "P12931",
            bound_to=[next_level_bound]
        )

        substrate = Gene(
            "P00533",
            regions=[substrate_region],
            residues=substrate_residues,
            states=[substrate_state],
            bound_to=[substrate_bound]
        )

        mod_target = Residue("S", "33", State("phosphorylation", False))
        mod2 = Modification(enzyme, substrate, mod_target, True)
        self.corpus.add_interaction(mod2, add_agents=True, anatomize=False)

    def test_phospho_semantics(self):
        """Test black box processing using phosphorylation semantics."""
        mek1 = Gene("Q02750")
        stat3 = Gene("P40763")
        mod_state = Residue("S", 727, State("phosphorylation", False))
        value = True

        mod1 = Modification(mek1, stat3, mod_state, value)

        mod_state_1 = Residue("Y", 705, State("phosphorylation", False))

        mod2 = Modification(mek1, stat3, mod_state_1, value)

        erk1 = Gene("P27361")

        mod_state_2 = Residue("T", 201, State("phosphorylation", False))

        mod3 = Modification(mek1, erk1, mod_state_2, value)

        erk2 = Gene("P28482")
        mod_state_3 = Residue("T", 182, State("phosphorylation", False))

        mod4 = Modification(mek1, erk2, mod_state_3, value)

        interactions = [mod1, mod2, mod3, mod4]

        corpus = KamiCorpus("test")
        corpus.add_interactions(
            interactions,
            add_agents=True,
            anatomize=True
        )
        print(corpus.action_graph.nodes())
        print(corpus._hierarchy.relation["test_action_graph"]["semantic_action_graph"])
        print(corpus)
        print_graph(corpus.action_graph)
        print(corpus._hierarchy.relation["test_action_graph"]["semantic_action_graph"])

    def test_sh2_py_semantics(self):
        """."""
        phos = State("phosphorylation", True)
        dok1_py398 = Gene(
            "Q99704",
            synonyms=["DOK1", "p62DOK1"],
            residues=[Residue("Y", 398, phos)]
        )

        abl2 = Gene("P42684", synonyms=["ABL2"])
        sh2 = Region(name="SH2")

        abl2_sh2 = RegionActor(abl2, sh2)

        bnd = Binding(dok1_py398, abl2_sh2)

        corpus = KamiCorpus("test")
        nugget_id = corpus.add_interaction(bnd)

        semantic_entities = [
            "sh2_domain",
            "sh2_domain_pY_bnd",
            "pY_site",
            "pY_residue",
            "phosphorylation"]

        assert("pY_site" in corpus.nugget[nugget_id].nodes())
        assert("pY_residue" in corpus.nugget[nugget_id].nodes())
        assert("pY_residue_phospho" in corpus.nugget[nugget_id].nodes())

        assert((nugget_id, "sh2_pY_binding_semantic_nugget") in corpus.nugget_relations())

        for entity in semantic_entities:
            assert(entity in corpus._hierarchy.relation[
                "sh2_pY_binding_semantic_nugget"][nugget_id].keys())

        site_actor_no_residue = SiteActor(
            Gene("A"),
            Site("pY-site", start=100, end=150))

        bnd = Binding(abl2_sh2, site_actor_no_residue)
        nugget_id = corpus.add_interaction(bnd)
        assert(len(corpus.nugget[nugget_id].nodes()) == 7)
        binding_nodes = []
        for n in corpus.action_graph.nodes():
            if corpus.get_action_graph_typing()[n] == "bnd":
                binding_nodes.append(n)
        assert(len(binding_nodes) == 1)

        assert((nugget_id, "sh2_pY_binding_semantic_nugget") in corpus.nugget_relations())

        for entity in semantic_entities:
            assert(entity in corpus._hierarchy.relation[
                "sh2_pY_binding_semantic_nugget"][nugget_id].keys())

        site_actor_no_phospho = SiteActor(
            Gene("A"),
            Site("pY-site", start=100, end=150, residues=[Residue("Y")]))
        bnd = Binding(abl2_sh2, site_actor_no_phospho)
        nugget_id = corpus.add_interaction(bnd)
        assert(len(corpus.nugget[nugget_id].nodes()) == 8)
        binding_nodes = []
        for n in corpus.action_graph.nodes():
            if corpus.get_action_graph_typing()[n] == "bnd":
                binding_nodes.append(n)
        assert(len(binding_nodes) == 1)
        assert((nugget_id, "sh2_pY_binding_semantic_nugget") in corpus.nugget_relations())

        for entity in semantic_entities:
            assert(entity in corpus._hierarchy.relation[
                "sh2_pY_binding_semantic_nugget"][nugget_id].keys())

        site_actor_with_residue = SiteActor(
            Gene("A"),
            Site("pY-site", start=100, end=150,
                 residues=[Residue(
                     "Y", loc=145, state=State("phosphorylation"))
                 ]))

        bnd = Binding(abl2_sh2, site_actor_with_residue)
        nugget_id = corpus.add_interaction(bnd)
        assert(len(corpus.nugget[nugget_id].nodes()) == 7)
        binding_nodes = []
        for n in corpus.action_graph.nodes():
            if corpus.get_action_graph_typing()[n] == "bnd":
                binding_nodes.append(n)
        assert(len(binding_nodes) == 1)
        assert((nugget_id, "sh2_pY_binding_semantic_nugget") in corpus.nugget_relations())

        for entity in semantic_entities:
            assert(entity in corpus._hierarchy.relation[
                "sh2_pY_binding_semantic_nugget"][nugget_id].keys())

        site_actor_with_residue1 = SiteActor(
            Gene("B"),
            Site("pY-site",
                 residues=[Residue(
                     "Y", loc=145, state=State("phosphorylation"))
                 ]))
        site_actor_with_residue2 = SiteActor(
            Gene("B"),
            Site("some site",
                 residues=[Residue(
                     "Y", loc=145, state=State("phosphorylation"))
                 ]))
        bnd1 = Binding(abl2_sh2, site_actor_with_residue1)
        bnd2 = Binding(abl2_sh2, site_actor_with_residue2)
        corpus.add_interactions([bnd1, bnd2])
        print_graph(corpus.action_graph)

    def test_multiple_sh2(self):
        """."""
        phos = State("phosphorylation", True)
        sh2n = Region(name="SH2", order=1)
        sh2c = Region(name="SH2", order=2)

        pik3r1 = Gene("P27986", synonyms=["PIK3R1", "PI3K1"])
        pik3r1_sh2n = RegionActor(pik3r1, sh2n)
        pik3r1_sh2c = RegionActor(pik3r1, sh2c)

        frs2_py196 = Gene(
            "Q8WU20",
            synonyms=["FRS2"],
            residues=[Residue("Y", 196, phos)]
        )
        frs2_py349 = Gene(
            "Q8WU20",
            synonyms=["FRS2"],
            residues=[Residue("Y", 349, phos)]
        )

        bnds = []
        bnds.append(Binding(frs2_py196, pik3r1_sh2n))
        bnds.append(Binding(frs2_py349, pik3r1_sh2c))
        corpus = KamiCorpus("test")
        corpus.add_interactions(bnds, anatomize=True)

    def test_sites(self):
        # Create genes.
        egfr = Gene("P00533")
        grb2 = Gene("P62993")

        # Create a RegionActor and a SiteActor fo GRB2.
        grb2_sh2 = RegionActor(gene=grb2, region=Region(name="SH2"))
        grb2_site = SiteActor(gene=grb2, site=Site(name="pY"))

        inters = []
        # This works (RegionActor).
        # inters.append(BinaryBinding([egfr], [grb2_sh2]))
        # This does not work (SiteActor)
        inters.append(Binding(egfr, grb2_site))

        corpus = KamiCorpus("test")
        corpus.add_interactions(inters, anatomize=True)
        print_graph(corpus.nugget["test_nugget_1"])

    def test_regionactor(self):
        # Phosphorylated and unphosphrylated states.
        phos = State("phosphorylation", True)
        unphos = State("phosphorylation", False)

        inters = []
        # Phosphorylation with RegionActor as substrate.
        m = Modification(
            enzyme=Gene("P00519"),
            substrate=RegionActor(
                Gene("P00533", regions=[
                    Region(name='PVPEyINQS',
                           start=280, end=290),
                    Region(name="L receptor",
                           start=57, end=167, states=[phos])]),
                Region(start=1000, end=1500)),
            target=Residue(aa="Y", loc=1092, state=unphos),
            value=True
        )
        inters.append(m)

        corpus = KamiCorpus("test")
        corpus.add_interactions(inters, anatomize=True)
        print_graph(corpus.nugget["test_nugget_1"])

    def test_siteactor(self):
        """Generate sh2 pY bnd interactions."""
        # General phosphorylation state.
        phos = State("phosphorylation", True)
        unphos = State("phosphorylation", False)

        # General SH2 regions.
        sh2 = Region(name="SH2")
        sh2n = Region(name="SH2", order=1)
        sh2c = Region(name="SH2", order=2)

        inters = []

        enz_uniprot = 'P00519'
        sub_uniprot = 'P00533'
        rsd = 'Y1092'
        location = int(rsd[1:])
        strt = location - 4
        stop = location + 4
        site_name = 'b%i' % location

        m = Modification(
            enzyme=Gene(enz_uniprot),
            substrate=SiteActor(
                gene=Gene(sub_uniprot),
                site=Site(name=site_name, start=strt, end=stop)),
            target=Residue(aa="Y", loc=location, state=unphos),
            value=True)
        inters.append(m)
        corpus = KamiCorpus("test")
        corpus.add_interactions(inters, anatomize=True)

    def test_complicated_site_actor(self):
        m = Modification(
            enzyme=SiteActor(
                gene=Gene("P00519",
                          sites=[Site(name="bob", start=120, end=150)],
                          regions=[Region(name="alice", start=100, end=200)],
                          residues=[Residue("Y", 122)]
                          ),
                site=Site(name="jack", start=550, end=600,
                          residues=[Residue("T")]),
                region=Region(name="Pkinase",
                              start=500, end=800,
                              sites=[Site(name="billy")])
            ),
            substrate=SiteActor(gene=Gene("P00533"),
                                site=Site(name="target"),
                                region=Region(name="bla")),
            target=Residue("Y", 100, State("phosphorylation", False)),
            value=True
        )
        corpus = KamiCorpus("test")
        corpus.add_interactions([m], anatomize=True)
        print_graph(corpus.nugget["test_nugget_1"])
        print(ag_to_edge_list(corpus))

    def test_advanced_site_actor(self):
        # General phosphorylation state.
        phos = State("phosphorylation", True)
        unphos = State("phosphorylation", False)

        # General SH2 regions.
        sh2 = Region(name="SH2")
        sh2n = Region(name="SH2", order=1)
        sh2c = Region(name="SH2", order=2)

        # Test site.
        s1 = Site(name="test_site")

        inters = []

        # Modification using SiteActor.
        m = Modification(
            enzyme=Gene("P00519", hgnc_symbol="ABL1"),
            substrate=SiteActor(gene=Gene("P00519", hgnc_symbol="ABL1"),
                                site=Site(name="site800", start=796, end=804)),
            target=Residue("Y", 800, State("phosphorylation", False)),
            value=True
        )
        inters.append(m)
        m = Modification(
            enzyme=Gene("P00519", hgnc_symbol="ABL1"),
            substrate=SiteActor(gene=Gene("P00533", hgnc_symbol="EGFR"),
                                site=Site(name="site800", start=796, end=804)),
            target=Residue("Y", 800, State("phosphorylation", False)),
            value=True
        )
        inters.append(m)

        # Binding using SiteActor.
        b = Binding(

            SiteActor(gene=Gene("P00533", hgnc_symbol="EGFR"),
                      site=Site(name="site800", start=796, end=804)),
            RegionActor(gene=Gene("P62993", hgnc_symbol="GRB2"), region=sh2)
        )
        inters.append(b)
        corpus = KamiCorpus("test")
        corpus.add_interactions(inters, anatomize=True)

    def test_site_residue_reconnect(self):
        sh2 = Region(name="SH2")
        b = Binding(
            SiteActor(gene=Gene(uniprotid="P00533", hgnc_symbol="EGFR",
                                residues=[
                                    Residue(
                                        "Y", 1092,
                                        state=State("phosphorylation", True))]),
                      site=Site(name="motif1092", start=1088, end=1096)),
            RegionActor(gene=Gene("P62993", hgnc_symbol="GRB2"), region=sh2)
        )
        corpus = KamiCorpus("test")
        corpus.add_interaction(b)

    def test_bookkeeping(self):
        interactions = []

        i1 = LigandModification(
            RegionActor(Gene("P00533"), Region(start=712, end=979)),
            Gene("P00533"),
            Residue("Y", 1092, state=State("phosphorylation", False)))
        interactions.append(i1)

        i2 = Modification(
            Gene("P00519"),
            Gene("P00533"),
            Residue("S", 800, state=State("phosphorylation", False)))
        interactions.append(i2)

        i3 = Binding(
            Gene("P00424"),
            SiteActor(
                Gene("P00533"),
                Site(start=799, end=900)))
        interactions.append(i3)

        corpus = KamiCorpus("test")
        corpus.add_interactions(interactions)
