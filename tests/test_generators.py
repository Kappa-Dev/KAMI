"""Unit testing of nugget generators functionality."""

from regraph import print_graph

from kami import add_interactions
from kami.resolvers.generators import (NuggetContainer, Generator,
                                       ModGenerator)
from kami.interactions import (Modification,
                               Binding)
from kami.entities import (Gene, Region, RegionActor, Residue,
                           Site, SiteActor, State)
from kami.hierarchy import KamiHierarchy
from kami.exceptions import KamiError


class TestBlackBox(object):
    """Test class for black box functionality."""

    def __init__(self):
        """Define some initial content of the hierarchy."""
        hierarchy = KamiHierarchy()
        gene = Gene("P00533")
        gene_id = hierarchy.add_gene(gene)
        self.generator = Generator(hierarchy)
        self.default_ag_gene = gene_id

    def test_state_generator(self):
        """Testing State generation."""
        state_true = State("activity", True)
        state_false = State("activity", False)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        # If the parameter 'add_agents' is set to false
        # this should raise an exception as there is no
        # corresponding state in the ag yet

        # old_ag_size = len(self.generator.hierarchy.action_graph.nodes())
        state1 = self.generator._generate_state(
            nugget, state_true, self.default_ag_gene)

        state2 =\
            self.generator._generate_state(
                nugget, state_true, self.default_ag_gene)
        state3 =\
            self.generator._generate_state(
                nugget, state_false, self.default_ag_gene)

        # assert(
        #     False not in
        #     self.generator.hierarchy.action_graph.node[
        #         nugget.ag_typing[state2]]['activity'])

        state4 =\
            self.generator._generate_state(
                nugget, state_false, self.default_ag_gene)

        assert(len(nugget.graph.nodes()) == 4)
        # only one node was added to the action graph
        # assert(
        #     len(self.generator.hierarchy.action_graph.nodes()) ==
        #     old_ag_size + 1)

        assert("activity" in nugget.graph.node[state1].keys())
        assert("activity" in nugget.graph.node[state2].keys())
        assert("activity" in nugget.graph.node[state3].keys())
        assert("activity" in nugget.graph.node[state4].keys())

        assert(nugget.meta_typing[state1] == "state")
        assert(nugget.meta_typing[state2] == "state")
        assert(nugget.meta_typing[state3] == "state")
        assert(nugget.meta_typing[state4] == "state")

        # assert(state1 not in nugget.ag_typing.keys())
        # assert(state3 not in nugget.ag_typing.keys())
        # assert(nugget.ag_typing[state2] == nugget.ag_typing[state4])
        # assert(
        #     nugget.ag_typing[state2] in
        #     self.generator.hierarchy.action_graph.nodes())
        # assert(
        #     nugget.ag_typing[state4] in
        #     self.generator.hierarchy.action_graph.nodes())
        # assert(
        #     (nugget.ag_typing[state2], self.default_ag_gene) in
        #     self.generator.hierarchy.action_graph.edges())
        # assert(
        #     (nugget.ag_typing[state4], self.default_ag_gene) in
        #     self.generator.hierarchy.action_graph.edges())
        return

    def test_residue_generator(self):
        """Testing Residue generation."""
        t = Residue("T")
        t100 = Residue("T", 100)
        y100_phospho = Residue("Y", 100, State("phosphorylation", True))
        y100_active = Residue("Y", 100, State("activity", True))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        old_ag_size = len(self.generator.hierarchy.action_graph.nodes())
        residue1, state1 =\
            self.generator._generate_residue(
                nugget, t, self.default_ag_gene, self.default_ag_gene)
        assert(state1 is None)
        # assert(residue1 not in nugget.ag_typing.keys())
        assert(residue1 in nugget.nodes())

        residue2, _ =\
            self.generator._generate_residue(
                nugget, t, self.default_ag_gene, self.default_ag_gene)
        # assert(residue2 in nugget.ag_typing.keys())

        residue3, _ =\
            self.generator._generate_residue(
                nugget, t100, self.default_ag_gene, self.default_ag_gene)
        # assert(nugget.ag_typing[residue2] != nugget.ag_typing[residue3])

        residue4, state4 =\
            self.generator._generate_residue(
                nugget, y100_phospho, self.default_ag_gene, self.default_ag_gene)
        assert(state4 is not None)
        # assert(nugget.ag_typing[residue4] == nugget.ag_typing[residue3])

        residue5, state5 =\
            self.generator._generate_residue(
                nugget, y100_active, self.default_ag_gene, self.default_ag_gene)

        assert(len(nugget.nodes()) == 7)
        # assert(
        #     len(self.generator.hierarchy.action_graph.nodes()) ==
        #     old_ag_size + 4)

        assert("T" in nugget.graph.node[residue1]["aa"])
        assert("T" in nugget.graph.node[residue2]["aa"])
        assert("T" in nugget.graph.node[residue3]["aa"])
        # assert(
        #     "T" in self.generator.hierarchy.action_graph.node[
        #         nugget.ag_typing[residue2]]["aa"])
        assert(100 in nugget.graph.node[residue3]["loc"])
        # assert(
        #     100 in self.generator.hierarchy.action_graph.node[
        #         nugget.ag_typing[residue3]]["loc"])

        assert(nugget.meta_typing[residue1] == "residue")
        assert(nugget.meta_typing[residue2] == "residue")
        assert(nugget.meta_typing[residue3] == "residue")
        assert(nugget.meta_typing[residue4] == "residue")
        assert(nugget.meta_typing[residue5] == "residue")

        # assert(
        #     nugget.ag_typing[residue3] ==
        #     nugget.ag_typing[residue4] ==
        #     nugget.ag_typing[residue5])

        # assert(
        #     (nugget.ag_typing[state5], nugget.ag_typing[residue3]) in
        #     self.generator.hierarchy.action_graph.edges() and
        #     (nugget.ag_typing[state4], nugget.ag_typing[residue3]) in
        #     self.generator.hierarchy.action_graph.edges()
        # )

    def test_site_generator(self):
        """Testing Site generation."""
        # Test site identification
        site_bob = Site(name="bob")
        site100_200 = Site(start="100", end="200")
        site110_150 = Site(start="110", end="150")

        site_bob_500_600 = Site(name="bob", start=500, end=600)
        site_bob_800_1000 = Site(name="bob", start=800, end=1000)
        site_bob_1 = Site(name="bob", order=1)
        site_bob_2 = Site(name="bob", order=2)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        old_ag_size = len(self.generator.hierarchy.action_graph.nodes())

        site_bob_id_1 =\
            self.generator._generate_site(
                nugget, site_bob, self.default_ag_gene, self.default_ag_gene)
        assert(site_bob_id_1 in nugget.nodes())
        # assert(site_bob_id_1 not in nugget.ag_typing.keys())

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
        # assert(
        #     nugget.ag_typing[site110_150_id] ==
        #     nugget.ag_typing[site100_200_id])

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
        # assert(
        #     nugget.ag_typing[site_bob_1_id] ==
        #     nugget.ag_typing[site_bob_500_600_id])
        # assert(
        #     nugget.ag_typing[site_bob_2_id] ==
        #     nugget.ag_typing[site_bob_800_1000_id])

        assert(len(nugget.nodes()) == 8)
        # assert(
        #     len(self.generator.hierarchy.action_graph.nodes()) ==
        #     old_ag_size + 3)

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
        """Testing Region generation."""
        kinase_region = Region(
            name="Pkinase",
            start=300,
            end=500,
            states=[State("activity", True)],
            residues=[Residue("Y", 1000)],
        )

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        old_ag_size = len(self.generator.hierarchy.action_graph.nodes())

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

        # This names may be changed if the procedures of id generation will change
        site_id = "P00533_region_Pkinase_300_500_site_alice_350_450"
        residue_id = "P00533_region_Pkinase_300_500_Y350"

        # assert(
        #     (nugget.ag_typing[kinase_region_id], self.default_ag_gene) in
        #     self.generator.hierarchy.action_graph.edges()
        # )
        # assert(
        #     (nugget.ag_typing[site_id], self.default_ag_gene) in
        #     self.generator.hierarchy.action_graph.edges() and
        #     (nugget.ag_typing[site_id], nugget.ag_typing[kinase_region_id]) in
        #     self.generator.hierarchy.action_graph.edges()
        # )

        # assert(
        #     (nugget.ag_typing[residue_id], self.default_ag_gene) in
        #     self.generator.hierarchy.action_graph.edges() and
        #     (nugget.ag_typing[residue_id], nugget.ag_typing[kinase_region_id]) in
        #     self.generator.hierarchy.action_graph.edges() and
        #     (nugget.ag_typing[residue_id], nugget.ag_typing[site_id]) in
        #     self.generator.hierarchy.action_graph.edges()
        # )
        # assert(
        #     len(self.generator.hierarchy.action_graph.nodes()) ==
        #     old_ag_size + 5
        # )

    def test_gene_generator(self):
        """Testing Gene genaration."""
        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        gene1 = Gene("Q07890")

        old_ag_size = len(self.generator.hierarchy.action_graph.nodes())
        self.generator._generate_gene(nugget, gene1)
        # assert(
        #     old_ag_size == len(self.generator.hierarchy.action_graph.nodes()))
        self.generator._generate_gene(
            nugget, gene1)
        # assert(
        #     old_ag_size + 1 ==
        #     len(self.generator.hierarchy.action_graph.nodes()))

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
        # assert(
        #     nugget.ag_typing["P00519_active"] ==
        #     nugget.ag_typing["P00519_active_1"])
        # big_region_id = "P00519_region_big_region_1000"
        # super_site_id = "P00519_site_super_site_100_300"
        # y100_res_id = "P00519_Y100"
        # t100_res_id = "P00519_T100"
        # s500_res_id = "P00519_S500"
        # assert(nugget.ag_typing[y100_res_id] == nugget.ag_typing[t100_res_id])
        # assert(
        #     (nugget.ag_typing[super_site_id], nugget.ag_typing[big_region_id]) in
        #     self.generator.hierarchy.action_graph.edges())
        # assert(
        #     (nugget.ag_typing[y100_res_id], nugget.ag_typing[super_site_id]) in
        #     self.generator.hierarchy.action_graph.edges())
        # assert(
        #     (nugget.ag_typing[y100_res_id], nugget.ag_typing[big_region_id]) in
        #     self.generator.hierarchy.action_graph.edges())
        # assert(
        #     (nugget.ag_typing[s500_res_id], nugget.ag_typing[big_region_id]) in
        #     self.generator.hierarchy.action_graph.edges())

    def test_region_actor_generator(self):
        """Testing RegionActor generation."""
        region_actor = RegionActor(
            gene=Gene("P00519"), region=Region("SH2"))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        (gene_id, region_id) =\
            self.generator._generate_region_actor(nugget, region_actor)

        assert((region_id, gene_id) in nugget.edges())
        # assert(
        #     (nugget.ag_typing[region_id], nugget.ag_typing[gene_id]) in
        #     self.generator.hierarchy.action_graph.edges())

    def test_site_actor_generator(self):
        """Testing SiteActor generation."""
        # no region
        site_actor = SiteActor(
            gene=Gene("P00519"), site=Site("pY"))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        (gene_id, site_id, region_id) =\
            self.generator._generate_site_actor(nugget, site_actor)
        assert((site_id, gene_id) in nugget.edges())

        # with a region in the middle
        site_actor_with_region = SiteActor(
            gene=Gene("P00519"), site=Site("pY"), region=Region("kinase"))

        (gene_id, site_id, region_id) =\
            self.generator._generate_site_actor(nugget, site_actor_with_region)

        assert((site_id, region_id) in nugget.edges())
        assert((region_id, gene_id) in nugget.edges())

    def test_is_bnd_generator(self):

        gene = Gene("Q07890")
        site_actor = SiteActor(gene=Gene("Q07890"), site=Site("pY"))
        region_actor = RegionActor(
            gene=Gene("Q07890"), region=Region("Pkinase"))

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
            self.generator._generate_site(nugget, site, self.default_ag_gene,
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
        site_id =\
            self.generator._generate_site(
                nugget, site, self.default_ag_gene, self.default_ag_gene)

        # region = Region(
        #     "sh2",
        #     bounds=[]
        # )
        # gene = Gene(
        #     "P00519",
        #     bounds=[]
        # )

    def test_mod_generator(self):
        enzyme_gene = Gene("Q07890")
        enzyme_region_actor = RegionActor(
            gene=enzyme_gene,
            region=Region("Pkinase"))
        enzyme_site_actor = SiteActor(
            gene=enzyme_gene,
            region=Region("Pkinase"),
            site=Site("tail"))

        substrate_gene = Gene("P00519")
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
        print(mod5)
        hierarchy = KamiHierarchy()
        generator = ModGenerator(hierarchy)
        n, t = generator._create_nugget(mod5)
        print_graph(n.graph)
