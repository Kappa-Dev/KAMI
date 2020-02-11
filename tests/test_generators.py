"""Unit testing of nugget generators functionality."""

from regraph import print_graph

from kami.aggregation.identifiers import EntityIdentifier
from kami.aggregation.generators import (KamiGraph, Generator,
                                         ModGenerator, SelfModGenerator,
                                         LigandModGenerator, BndGenerator,
                                         AnonymousModGenerator)
from kami import (Modification,
                  Binding, SelfModification,
                  LigandModification, AnonymousModification)
from kami import (Protoform, Region, RegionActor, Residue,
                  Site, SiteActor, State)
from kami import KamiCorpus
from kami.exceptions import KamiError


class TestGenerators(object):
    """Test class for `kami.resolvers.generators` module."""

    def __init__(self):
        """Define some initial content of the corpus."""
        corpus = KamiCorpus("test")
        protoform = Protoform("A")
        gene_id = corpus.add_gene(protoform)
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        self.generator = Generator(identifier)
        self.default_ag_gene = gene_id

    def test_state_generator(self):
        """Test generation of graph components for a State object."""
        state_true = State("activity", True)
        state_false = State("activity", False)

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        state1 = self.generator.generate_state(
            nugget, state_true, self.default_ag_gene)

        state2 =\
            self.generator.generate_state(
                nugget, state_true, self.default_ag_gene)
        state3 =\
            self.generator.generate_state(
                nugget, state_false, self.default_ag_gene)

        state4 =\
            self.generator.generate_state(
                nugget, state_false, self.default_ag_gene)

        assert(len(nugget.graph.nodes()) == 4)

        assert("name" in nugget.graph.node[state1].keys())
        assert("activity" in nugget.graph.node[state1]["name"])
        assert("name" in nugget.graph.node[state2].keys())
        assert("activity" in nugget.graph.node[state2]["name"])
        assert("name" in nugget.graph.node[state3].keys())
        assert("activity" in nugget.graph.node[state3]["name"])
        assert("name" in nugget.graph.node[state4].keys())
        assert("activity" in nugget.graph.node[state4]["name"])

        assert(nugget.meta_typing[state1] == "state")
        assert(nugget.meta_typing[state2] == "state")
        assert(nugget.meta_typing[state3] == "state")
        assert(nugget.meta_typing[state4] == "state")

        return

    def test_residue_generator(self):
        """Test generation of graph components for a Residue object."""
        t = Residue("T")
        t100 = Residue("T", 100)
        y100_phospho = Residue("Y", 100, State("phosphorylation", True))
        y100_active = Residue("Y", 100, State("activity", True))

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        residue1, state1 =\
            self.generator.generate_residue(
                nugget, t, self.default_ag_gene, self.default_ag_gene)
        assert(state1 is None)
        assert(residue1 in nugget.nodes())

        residue2, _ =\
            self.generator.generate_residue(
                nugget, t, self.default_ag_gene, self.default_ag_gene)

        residue3, _ =\
            self.generator.generate_residue(
                nugget, t100, self.default_ag_gene, self.default_ag_gene)

        residue4, state4 =\
            self.generator.generate_residue(
                nugget, y100_phospho, self.default_ag_gene, self.default_ag_gene)
        assert(state4 is not None)

        residue5, state5 =\
            self.generator.generate_residue(
                nugget, y100_active, self.default_ag_gene, self.default_ag_gene)

        assert(len(nugget.nodes()) == 7)
        assert("T" in nugget.graph.node[residue1]["aa"])
        assert("T" in nugget.graph.node[residue2]["aa"])
        assert("T" in nugget.graph.node[residue3]["aa"])
        assert(nugget.meta_typing[residue1] == "residue")
        assert(nugget.meta_typing[residue2] == "residue")
        assert(nugget.meta_typing[residue3] == "residue")
        assert(nugget.meta_typing[residue4] == "residue")
        assert(nugget.meta_typing[residue5] == "residue")

    def test_site_generator(self):
        """Test generation of graph components for a Site object."""
        # Site identification
        site_bob = Site(name="bob")
        site100_200 = Site(start=100, end=200)
        site110_150 = Site(start=110, end=150)

        site_bob_500_600 = Site(name="bob", start=500, end=600)
        site_bob_800_1000 = Site(name="bob", start=800, end=1000)
        site_bob_1 = Site(name="bob", order=1)
        site_bob_2 = Site(name="bob", order=2)

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        site_bob_id_1 =\
            self.generator.generate_site(
                nugget, site_bob, self.default_ag_gene, self.default_ag_gene)
        assert(site_bob_id_1 in nugget.nodes())

        site_bob_id_2 =\
            self.generator.generate_site(
                nugget, site_bob, self.default_ag_gene, self.default_ag_gene)
        assert(site_bob_id_2 in nugget.nodes())
        # assert(site_bob_id_2 in nugget.reference_typing.keys())

        site100_200_id =\
            self.generator.generate_site(
                nugget, site100_200, self.default_ag_gene, self.default_ag_gene)
        site110_150_id =\
            self.generator.generate_site(
                nugget, site110_150, self.default_ag_gene, self.default_ag_gene)

        site_bob_500_600_id =\
            self.generator.generate_site(
                nugget, site_bob_500_600,
                self.default_ag_gene, self.default_ag_gene)
        site_bob_800_1000_id =\
            self.generator.generate_site(
                nugget, site_bob_800_1000,
                self.default_ag_gene, self.default_ag_gene)
        site_bob_1_id =\
            self.generator.generate_site(
                nugget, site_bob_1, self.default_ag_gene, self.default_ag_gene)
        site_bob_2_id =\
            self.generator.generate_site(
                nugget, site_bob_2, self.default_ag_gene, self.default_ag_gene)
        assert(len(nugget.nodes()) == 8)

        # Test generation of the site conditions
        complex_site = Site(
            start=500, end=600,
            states=[State('active', True)],
            residues=[Residue("Y", 1000, State('phosphorylation', True))],
        )
        try:
            self.generator.generate_site(
                nugget, complex_site, self.default_ag_gene, self.default_ag_gene)
            raise ValueError("Invalid residue was not caught!")
        except:
            pass

        complex_site = Site(
            start=500, end=600,
            states=[State('active', True)],
            residues=[Residue("Y", 505, State('phosphorylation', True))]
        )
        complex_site_id = self.generator.generate_site(
            nugget, complex_site, self.default_ag_gene, self.default_ag_gene)
        # assert(
        #     nugget.reference_typing[complex_site_id] ==
        #     nugget.reference_typing[site_bob_500_600_id])
        assert(len(nugget.nodes()) == 13)
        assert(len(nugget.edges()) == 3)

    def test_region_generator(self):
        """Test generation of graph components for a Region object."""
        kinase_region = Region(
            name="Pkinase",
            start=300,
            end=500,
            states=[State("activity", True)],
            residues=[Residue("Y", 1000)],
        )

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        try:
            self.generator.generate_region(
                nugget, kinase_region, self.default_ag_gene)
            raise ValueError("Invalid residue was not caught!")
        except KamiError:
            pass

        kinase_region = Region(
            name="Pkinase",
            start=300,
            end=500,
            states=[State("activity", True)],
            residues=[Residue("Y", 350, State("phosphorylation", True))],
            sites=[
                # Site(name="bob", residues=[Residue("Y", 350)]),
                Site(name="alice", start=1000, end=2000)
            ]
        )
        try:
            self.generator.generate_region(
                nugget, kinase_region, self.default_ag_gene)
            raise ValueError("Invalid site was not caught!")
        except KamiError:
            pass

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        kinase_region = Region(
            name="Pkinase",
            start=300,
            end=500,
            states=[State("activity", True)],
            residues=[Residue("Y", 350, State("phosphorylation", True))],
            sites=[
                Site(name="alice", start=350, end=450)
            ]
        )

        kinase_region_id = self.generator.generate_region(
            nugget, kinase_region, self.default_ag_gene)

        assert(len(nugget.nodes()) == 5)

    def test_gene_generator(self):
        """Test generation of graph components for a Protoform object."""
        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        gene1 = Protoform("B")

        self.generator.generate_gene(nugget, gene1)
        self.generator.generate_gene(
            nugget, gene1)

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        gene2 = Protoform(
            "P00519",
            synonyms=["ABL1"],
            states=[State("active", True), State("active", False)],
            residues=[
                Residue("Y", 100, State("phosphorylation", True)),
                Residue("T", 100, State("phosphorylation", True)),
                Residue("S", 500),
                Residue("T")
            ],
            sites=[
                Site("bob"),
                Site(start=100, end=300,
                     name="super_site", residues=[Residue("T", 150)])
            ],
            regions=[
                Region(name="sh2"),
                Region(
                    start=0, end=1000, name="big_region",
                    states=[State("activity", True)])
            ],
            bound_to=[gene1],
        )

        gene_id = self.generator.generate_gene(nugget, gene2)

        # check it is consistent
        assert(len(nugget.nodes()) == 17)
        assert(len(nugget.edges()) == 16)
        assert(gene_id in nugget.graph.nodes())
        assert("P00519" in nugget.graph.node[gene_id]['uniprotid'])

    def test_region_actor_generator(self):
        """Test generation of graph components for a RegionActor object."""
        region_actor = RegionActor(
            protoform=Protoform("B"), region=Region("SH2"))

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        (gene_id, region_id) =\
            self.generator.generate_region_actor(nugget, region_actor)

        assert((region_id, gene_id) in nugget.edges())

    def test_site_actor_generator(self):
        """Test generation of graph components for a SiteActor object."""
        # no region
        site_actor = SiteActor(
            protoform=Protoform("B"), site=Site("pY"))

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        (gene_id, site_id, region_id) =\
            self.generator.generate_site_actor(nugget, site_actor)
        assert((site_id, gene_id) in nugget.edges())

        # with a region in the middle
        site_actor_with_region = SiteActor(
            protoform=Protoform("B"), site=Site("pY"), region=Region("kinase"))

        (gene_id, site_id, region_id) =\
            self.generator.generate_site_actor(nugget, site_actor_with_region)

        assert((site_id, region_id) in nugget.edges())
        assert((region_id, gene_id) in nugget.edges())

    def test_is_bnd_generator(self):
        """Test generation of graph components for a bound condition."""
        protoform = Protoform("A")
        site_actor = SiteActor(protoform=Protoform("A"), site=Site("pY"))
        region_actor = RegionActor(
            protoform=Protoform("A"), region=Region("Pkinase"))

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bound_to=[protoform, protoform]
        )
        site_id =\
            self.generator.generate_site(
                nugget, site,
                self.default_ag_gene, self.default_ag_gene)

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bound_to=[site_actor]
        )
        site_id =\
            self.generator.generate_site(
                nugget, site, self.default_ag_gene,
                self.default_ag_gene)

        nugget = KamiGraph()
        nugget.reference_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bound_to=[region_actor]
        )
        self.generator.generate_site(
            nugget, site, self.default_ag_gene, self.default_ag_gene)

    def test_mod_generator(self):
        """Test generation of a modification nugget graph."""
        enzyme_gene = Protoform("A")
        enzyme_region_actor = RegionActor(
            protoform=enzyme_gene,
            region=Region("Pkinase"))
        enzyme_site_actor = SiteActor(
            protoform=enzyme_gene,
            region=Region("Pkinase"),
            site=Site("tail"))

        substrate_gene = Protoform("B")
        substrate_region_actor = RegionActor(
            protoform=substrate_gene,
            region=Region("SH2"))
        substrate_site_actor = SiteActor(
            protoform=substrate_gene,
            region=Region("SH2"),
            site=Site("finger"))

        residue_mod_target = Residue("Y", 100, State("activity", False))
        state_mod_target = State("activity", False)

        mod1 = Modification(
            enzyme=enzyme_gene,
            substrate=substrate_gene,
            target=state_mod_target
        )

        mod2 = Modification(
            enzyme=enzyme_region_actor,
            substrate=substrate_gene,
            target=state_mod_target
        )

        mod3 = Modification(
            enzyme=enzyme_site_actor,
            substrate=substrate_gene,
            target=state_mod_target
        )

        mod4 = Modification(
            enzyme=enzyme_site_actor,
            substrate=substrate_region_actor,
            target=state_mod_target
        )

        mod5 = Modification(
            enzyme=enzyme_site_actor,
            substrate=substrate_site_actor,
            target=residue_mod_target
        )
        corpus = KamiCorpus("test")
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        generator = ModGenerator(identifier)
        n, _, _, _ = generator.generate(mod5)
        print_graph(n.graph)

    def test_anonymous_mod_generation(self):
        """Test generation of an anonymous modification nugget graph."""
        protoform = Protoform("A")
        region_actor = RegionActor(
            protoform=protoform,
            region=Region("Pkinase"))

        mod = AnonymousModification(
            region_actor,
            Residue("Y", 100, State("phosphorylation", False)),
            value=True)

        corpus = KamiCorpus("test")
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        generator = AnonymousModGenerator(identifier)
        n, _, _, _ = generator.generate(mod)
        print_graph(n.graph)

    def test_selfmod_generation(self):
        """Test generation of an automodification nugget graph."""
        enzyme_gene = Protoform("A")
        enzyme_region_actor = RegionActor(
            protoform=enzyme_gene,
            region=Region("Pkinase"))

        automod = SelfModification(
            enzyme_region_actor,
            Residue("Y", 100, State("phosphorylation", True)),
            value=True,
            substrate_region=Region("Region"),
            substrate_site=Site("Site"))

        corpus = KamiCorpus("test")
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        generator = SelfModGenerator(identifier)
        n, _, _, _ = generator.generate(automod)
        print_graph(n.graph)

    def test_ligandmod_generation(self):
        """Test generation of a transmodification nugget graph."""
        enzyme_gene = Protoform("A")
        enzyme_region_actor = RegionActor(
            protoform=enzyme_gene,
            region=Region("Pkinase"))

        substrate = Protoform("B")

        automod = LigandModification(
            enzyme_region_actor,
            substrate,
            Residue("Y", 100, State("phosphorylation", True)),
            value=True,
            enzyme_bnd_region=Region("EbndRegion"),
            substrate_bnd_region=Region("SbndRegion"),
            substrate_bnd_site=Site("SbndSite"))

        corpus = KamiCorpus("test")
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        generator = LigandModGenerator(identifier)
        n, _, _, _ = generator.generate(automod)
        print_graph(n.graph)

        inter = LigandModification(
            enzyme=RegionActor(protoform=Protoform(uniprotid="P30530",
                                         hgnc_symbol="AXL"),
                               region=Region(name="Tyr_kinase",
                                             interproid="IPR020635",
                                             start=536, end=807)),
            substrate=SiteActor(protoform=Protoform(uniprotid="P06239",
                                          hgnc_symbol="LCK"),
                                site=Site(name="pY394",
                                          start=391, end=397)),
            target=Residue(aa="Y", loc=394,
                           state=State("phosphorylation", False)),
            value=True,
            rate=10,
            enzyme_bnd_region=Region(name="Tyr_kinase",
                                     interproid="IPR020635",
                                     start=536, end=807),
            substrate_bnd_site=Site(name='pY394',
                                    start=391, end=397)
        )
        corpus = KamiCorpus("test")
        corpus.add_interaction(inter, anatomize=False)
        print_graph(corpus.get_nugget('test_nugget_1'))

    def test_bnd_generation(self):
        """Test generation of a binding nugget graph."""
        left = SiteActor(Protoform("A"), Site("pY"), Region("Reg"))
        right = Protoform("B")
        bnd = Binding(left, right)

        corpus = KamiCorpus("test")
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        generator = BndGenerator(identifier)
        n, _, _, _ = generator.generate(bnd)
        print_graph(n.graph)

    def test_advanced_ligand_mod_generator(self):
        """Test generation with advanced usage of LigandModification."""

        corpus = KamiCorpus("test")
        identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing())
        generator = LigandModGenerator(identifier)

        enzyme = SiteActor(
            protoform=Protoform("A"),
            region=Region(name="RegionActor"),
            site=Site(name="SiteActor"))
        substrate = SiteActor(
            protoform=Protoform("B"),
            region=Region(name="RegionActor"),
            site=Site(name="SiteActor"))

        # simple subactors switching
        subactors = ["protoform", "region", "site"]
        for ea in subactors:
            for sa in subactors:
                mod = LigandModification(
                    enzyme=enzyme,
                    substrate=substrate,
                    target=Residue("Y", 100, State("phosphorylation", True)),
                    value=False,
                    enzyme_bnd_subactor=ea,
                    substrate_bnd_subactor=sa)

            n, _, _, _ = generator.generate(mod)

        mod = LigandModification(
            enzyme=enzyme,
            substrate=substrate,
            target=Residue("Y", 100, State("phosphorylation", True)),
            value=False,
            enzyme_bnd_region=Region(name="SpecialBindingRegion"),
            substrate_bnd_region=Region(name="SpecialBindingRegion"))

        n, _, _, _ = generator.generate(mod)

        mod = LigandModification(
            enzyme=enzyme,
            substrate=substrate,
            target=Residue("Y", 100, State("phosphorylation", True)),
            value=False,
            enzyme_bnd_subactor="region",
            substrate_bnd_subactor="region",
            enzyme_bnd_site=Site(name="SpecialBindingSite"),
            substrate_bnd_site=Site(name="SpecialBindingSite"))

        n, _, _, _ = generator.generate(mod)

        mod = LigandModification(
            enzyme=enzyme,
            substrate=substrate,
            target=Residue("Y", 100, State("phosphorylation", True)),
            value=False,
            enzyme_bnd_region=Region(name="SpecialBindingRegion"),
            substrate_bnd_region=Region(name="SpecialBindingRegion"),
            enzyme_bnd_site=Site(name="SpecialBindingSite"),
            substrate_bnd_site=Site(name="SpecialBindingSite"))

        n, _, _, _ = generator.generate(mod)
        print_graph(n.graph)
        # adding binding components
