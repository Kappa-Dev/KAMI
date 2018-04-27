"""Unit testing of nugget generators functionality."""

from regraph import print_graph

from kami.resolvers.generators import (NuggetContainer, Generator,
                                       ModGenerator, AutoModGenerator,
                                       TransModGenerator, BndGenerator,
                                       AnonymousModGenerator)
from kami.interactions import (Modification,
                               Binding, AutoModification,
                               TransModification, AnonymousModification)
from kami.entities import (Gene, Region, RegionActor, Residue,
                           Site, SiteActor, State)
from kami.hierarchy import KamiHierarchy
from kami.exceptions import KamiError


class TestGenerators(object):
    """Test class for `kami.resolvers.generators` module."""

    def __init__(self):
        """Define some initial content of the hierarchy."""
        hierarchy = KamiHierarchy()
        gene = Gene("A")
        gene_id = hierarchy.add_gene(gene)
        self.generator = Generator(hierarchy)
        self.default_ag_gene = gene_id

    def test_state_generator(self):
        """Test generation of graph components for a State object."""
        state_true = State("activity", True)
        state_false = State("activity", False)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        state1 = self.generator._generate_state(
            nugget, state_true, self.default_ag_gene)

        state2 =\
            self.generator._generate_state(
                nugget, state_true, self.default_ag_gene)
        state3 =\
            self.generator._generate_state(
                nugget, state_false, self.default_ag_gene)

        state4 =\
            self.generator._generate_state(
                nugget, state_false, self.default_ag_gene)

        assert(len(nugget.graph.nodes()) == 4)

        assert("activity" in nugget.graph.node[state1].keys())
        assert("activity" in nugget.graph.node[state2].keys())
        assert("activity" in nugget.graph.node[state3].keys())
        assert("activity" in nugget.graph.node[state4].keys())

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

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        residue1, state1 =\
            self.generator._generate_residue(
                nugget, t, self.default_ag_gene, self.default_ag_gene)
        assert(state1 is None)
        assert(residue1 in nugget.nodes())

        residue2, _ =\
            self.generator._generate_residue(
                nugget, t, self.default_ag_gene, self.default_ag_gene)

        residue3, _ =\
            self.generator._generate_residue(
                nugget, t100, self.default_ag_gene, self.default_ag_gene)

        residue4, state4 =\
            self.generator._generate_residue(
                nugget, y100_phospho, self.default_ag_gene, self.default_ag_gene)
        assert(state4 is not None)

        residue5, state5 =\
            self.generator._generate_residue(
                nugget, y100_active, self.default_ag_gene, self.default_ag_gene)

        assert(len(nugget.nodes()) == 7)
        assert("T" in nugget.graph.node[residue1]["aa"])
        assert("T" in nugget.graph.node[residue2]["aa"])
        assert("T" in nugget.graph.node[residue3]["aa"])
        assert(100 in nugget.graph.node[residue3]["loc"])
        assert(nugget.meta_typing[residue1] == "residue")
        assert(nugget.meta_typing[residue2] == "residue")
        assert(nugget.meta_typing[residue3] == "residue")
        assert(nugget.meta_typing[residue4] == "residue")
        assert(nugget.meta_typing[residue5] == "residue")

    def test_site_generator(self):
        """Test generation of graph components for a Site object."""
        # Site identification
        site_bob = Site(name="bob")
        site100_200 = Site(start="100", end="200")
        site110_150 = Site(start="110", end="150")

        site_bob_500_600 = Site(name="bob", start=500, end=600)
        site_bob_800_1000 = Site(name="bob", start=800, end=1000)
        site_bob_1 = Site(name="bob", order=1)
        site_bob_2 = Site(name="bob", order=2)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        site_bob_id_1 =\
            self.generator._generate_site(
                nugget, site_bob, self.default_ag_gene, self.default_ag_gene)
        assert(site_bob_id_1 in nugget.nodes())

        site_bob_id_2 =\
            self.generator._generate_site(
                nugget, site_bob, self.default_ag_gene, self.default_ag_gene)
        assert(site_bob_id_2 in nugget.nodes())
        # assert(site_bob_id_2 in nugget.ag_typing.keys())

        site100_200_id =\
            self.generator._generate_site(
                nugget, site100_200, self.default_ag_gene, self.default_ag_gene)
        site110_150_id =\
            self.generator._generate_site(
                nugget, site110_150, self.default_ag_gene, self.default_ag_gene)

        site_bob_500_600_id =\
            self.generator._generate_site(
                nugget, site_bob_500_600,
                self.default_ag_gene, self.default_ag_gene)
        site_bob_800_1000_id =\
            self.generator._generate_site(
                nugget, site_bob_800_1000,
                self.default_ag_gene, self.default_ag_gene)
        site_bob_1_id =\
            self.generator._generate_site(
                nugget, site_bob_1, self.default_ag_gene, self.default_ag_gene)
        site_bob_2_id =\
            self.generator._generate_site(
                nugget, site_bob_2, self.default_ag_gene, self.default_ag_gene)
        assert(len(nugget.nodes()) == 8)

        # Test generation of the site conditions
        complex_site = Site(
            start=500, end=600,
            states=[State('active', True)],
            residues=[Residue("Y", 1000, State('phosphorylation', True))],
        )
        try:
            self.generator._generate_site(
                nugget, complex_site, self.default_ag_gene, self.default_ag_gene)
            raise ValueError("Invalid residue was not caught!")
        except:
            pass

        complex_site = Site(
            start=500, end=600,
            states=[State('active', True)],
            residues=[Residue("Y", 505, State('phosphorylation', True))]
        )
        complex_site_id = self.generator._generate_site(
            nugget, complex_site, self.default_ag_gene, self.default_ag_gene)
        # assert(
        #     nugget.ag_typing[complex_site_id] ==
        #     nugget.ag_typing[site_bob_500_600_id])
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

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        try:
            self.generator._generate_region(
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
            self.generator._generate_region(
                nugget, kinase_region, self.default_ag_gene)
            raise ValueError("Invalid site was not caught!")
        except KamiError:
            pass

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

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

        kinase_region_id = self.generator._generate_region(
            nugget, kinase_region, self.default_ag_gene)

        assert(len(nugget.nodes()) == 5)

    def test_gene_generator(self):
        """Test generation of graph components for a Gene object."""
        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        gene1 = Gene("B")

        self.generator._generate_gene(nugget, gene1)
        self.generator._generate_gene(
            nugget, gene1)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        gene2 = Gene(
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
            bounds=[gene1],
        )

        gene_id = self.generator._generate_gene(nugget, gene2)

        # check it is consistent
        assert(len(nugget.nodes()) == 19)
        assert(len(nugget.edges()) == 18)
        assert(gene_id in nugget.graph.nodes())
        assert("P00519" in nugget.graph.node[gene_id]['uniprotid'])

    def test_region_actor_generator(self):
        """Test generation of graph components for a RegionActor object."""
        region_actor = RegionActor(
            gene=Gene("B"), region=Region("SH2"))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        (gene_id, region_id) =\
            self.generator._generate_region_actor(nugget, region_actor)

        assert((region_id, gene_id) in nugget.edges())

    def test_site_actor_generator(self):
        """Test generation of graph components for a SiteActor object."""
        # no region
        site_actor = SiteActor(
            gene=Gene("B"), site=Site("pY"))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        (gene_id, site_id, region_id) =\
            self.generator._generate_site_actor(nugget, site_actor)
        assert((site_id, gene_id) in nugget.edges())

        # with a region in the middle
        site_actor_with_region = SiteActor(
            gene=Gene("B"), site=Site("pY"), region=Region("kinase"))

        (gene_id, site_id, region_id) =\
            self.generator._generate_site_actor(nugget, site_actor_with_region)

        assert((site_id, region_id) in nugget.edges())
        assert((region_id, gene_id) in nugget.edges())

    def test_is_bnd_generator(self):
        """Test generation of graph components for a bound condition."""
        gene = Gene("A")
        site_actor = SiteActor(gene=Gene("A"), site=Site("pY"))
        region_actor = RegionActor(
            gene=Gene("A"), region=Region("Pkinase"))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bounds=[gene, gene]
        )
        site_id =\
            self.generator._generate_site(
                nugget, site,
                self.default_ag_gene, self.default_ag_gene)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bounds=[[gene, gene]]
        )
        site_id =\
            self.generator._generate_site(
                nugget, site, self.default_ag_gene,
                self.default_ag_gene)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bounds=[site_actor]
        )
        site_id =\
            self.generator._generate_site(
                nugget, site, self.default_ag_gene,
                self.default_ag_gene)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        site = Site(
            "lala",
            bounds=[region_actor]
        )
        self.generator._generate_site(
            nugget, site, self.default_ag_gene, self.default_ag_gene)

    def test_mod_generator(self):
        """Test generation of a modification nugget graph."""
        enzyme_gene = Gene("A")
        enzyme_region_actor = RegionActor(
            gene=enzyme_gene,
            region=Region("Pkinase"))
        enzyme_site_actor = SiteActor(
            gene=enzyme_gene,
            region=Region("Pkinase"),
            site=Site("tail"))

        substrate_gene = Gene("B")
        substrate_region_actor = RegionActor(
            gene=substrate_gene,
            region=Region("SH2"))
        substrate_site_actor = SiteActor(
            gene=substrate_gene,
            region=Region("SH2"),
            site=Site("finger"))

        residue_mod_target = Residue("Y", 100, State("activity", False))
        state_mod_target = State("activity", False)

        mod1 = Modification(
            enzyme=enzyme_gene,
            substrate=substrate_gene,
            mod_target=state_mod_target
        )

        mod2 = Modification(
            enzyme=enzyme_region_actor,
            substrate=substrate_gene,
            mod_target=state_mod_target
        )

        mod3 = Modification(
            enzyme=enzyme_site_actor,
            substrate=substrate_gene,
            mod_target=state_mod_target
        )

        mod4 = Modification(
            enzyme=enzyme_site_actor,
            substrate=substrate_region_actor,
            mod_target=state_mod_target
        )

        mod5 = Modification(
            enzyme=enzyme_site_actor,
            substrate=substrate_site_actor,
            mod_target=residue_mod_target
        )
        hierarchy = KamiHierarchy()
        generator = ModGenerator(hierarchy)
        n, t = generator._create_nugget(mod5)
        print_graph(n.graph)

    def test_anonymous_mod_generation(self):
        """Test generation of an anonymous modification nugget graph."""
        gene = Gene("A")
        region_actor = RegionActor(
            gene=gene,
            region=Region("Pkinase"))

        mod = AnonymousModification(
            region_actor,
            Residue("Y", 100, State("phosphorylation", False)),
            value=True)

        hierarchy = KamiHierarchy()
        generator = AnonymousModGenerator(hierarchy)
        n, t = generator._create_nugget(mod)
        print_graph(n.graph)

    def test_automod_generation(self):
        """Test generation of an automodification nugget graph."""
        enzyme_gene = Gene("A")
        enzyme_region_actor = RegionActor(
            gene=enzyme_gene,
            region=Region("Pkinase"))

        automod = AutoModification(
            enzyme_region_actor,
            Residue("Y", 100, State("phosphorylation", True)),
            value=True,
            substrate_region=Region("Region"),
            substrate_site=Site("Site"))

        hierarchy = KamiHierarchy()
        generator = AutoModGenerator(hierarchy)
        n, t = generator._create_nugget(automod)
        print_graph(n.graph)

    def test_transmod_generation(self):
        """Test generation of a transmodification nugget graph."""
        enzyme_gene = Gene("A")
        enzyme_region_actor = RegionActor(
            gene=enzyme_gene,
            region=Region("Pkinase"))

        substrate = Gene("B")

        automod = TransModification(
            enzyme_region_actor,
            substrate,
            Residue("Y", 100, State("phosphorylation", True)),
            value=True,
            enzyme_bnd_region=Region("EbndRegion"),
            substrate_bnd_region=Region("SbndRegion"),
            substrate_bnd_site=Site("SbndSite"))

        hierarchy = KamiHierarchy()
        generator = TransModGenerator(hierarchy)
        n, t = generator._create_nugget(automod)
        print_graph(n.graph)

    def test_bnd_generation(self):
        """Test generation of a binding nugget graph."""
        left = SiteActor(Gene("A"), Site("pY"), Region("Reg"))
        right = Gene("B")
        bnd = Binding(left, right)

        hierarchy = KamiHierarchy()
        generator = BndGenerator(hierarchy)
        n, t = generator._create_nugget(bnd)
        print_graph(n.graph)
