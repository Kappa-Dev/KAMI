"""Unit testing of nugget generators functionality."""

from regraph.primitives import (print_graph)

from kami.resolvers.generators import NuggetContainer, Generator
from kami.interactions import (Modification,
                               BinaryBinding)
from kami.entities import (Gene, Region, RegionActor, Residue,
                           Site, SiteActor, State)
from kami.hierarchy import KamiHierarchy


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
        """Test state generation."""
        state1 = State("activity", True)
        state2 = State("activity", False)

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        # If the parameter 'add_agents' is set to false
        # this should raise an exception as there is no
        # corresponding state in the ag yet
        # try:
        old_ag_size = len(self.generator.hierarchy.action_graph.nodes())
        state1_id = self.generator._generate_state(
            nugget, state1,
            self.default_ag_gene, add_agents=False)

        state2_id =\
            self.generator._generate_state(
                nugget, state1, self.default_ag_gene)
        state3_id =\
            self.generator._generate_state(
                nugget, state2, self.default_ag_gene, add_agents=False)
        assert(
            False not in
            self.generator.hierarchy.action_graph.node[
                nugget.ag_typing[state2_id]]['activity'])

        state4_id =\
            self.generator._generate_state(
                nugget, state2, self.default_ag_gene, add_agents=True)

        assert(len(nugget.graph.nodes()) == 4)
        # only one node was added to the action graph
        assert(
            len(self.generator.hierarchy.action_graph.nodes()) ==
            old_ag_size + 1)

        assert("activity" in nugget.graph.node[state1_id].keys())
        assert("activity" in nugget.graph.node[state2_id].keys())
        assert("activity" in nugget.graph.node[state3_id].keys())
        assert("activity" in nugget.graph.node[state4_id].keys())

        assert(nugget.meta_typing[state1_id] == "state")
        assert(nugget.meta_typing[state2_id] == "state")
        assert(nugget.meta_typing[state3_id] == "state")
        assert(nugget.meta_typing[state4_id] == "state")

        assert(state1_id not in nugget.ag_typing.keys())
        assert(state3_id not in nugget.ag_typing.keys())
        assert(nugget.ag_typing[state2_id] == nugget.ag_typing[state4_id])
        assert(
            nugget.ag_typing[state2_id] in
            self.generator.hierarchy.action_graph.nodes())
        assert(
            nugget.ag_typing[state4_id] in
            self.generator.hierarchy.action_graph.nodes())
        assert(
            (nugget.ag_typing[state2_id], self.default_ag_gene) in
            self.generator.hierarchy.action_graph.edges())
        assert(
            (nugget.ag_typing[state4_id], self.default_ag_gene) in
            self.generator.hierarchy.action_graph.edges())
        return

    def test_residue_generator(self):
        """Test residue generation."""
        residue1 = Residue("T")
        residue2 = Residue("T", 100)
        residue3 = Residue("Y", 100, State("phosphorylation", True))
        residue4 = Residue("Y", 100, State("phosphorylation", True))

        nugget = NuggetContainer()
        nugget.ag_typing[self.default_ag_gene] = self.default_ag_gene

        residue1_id =\
            self.generator._generate_residue(
                nugget, residue1, self.default_ag_gene)
        residue2_id =\
            self.generator._generate_residue(
                nugget, residue2, self.default_ag_gene)
        residue3_id =\
            self.generator._generate_residue(
                nugget, residue3, self.default_ag_gene)
        residue4_id =\
            self.generator._generate_residue(
                nugget, residue4, self.default_ag_gene)


    # def test_gene_generator(self):
    #     """Test gene genaration."""

    #     hierarchy = KamiHierarchy()
    #     generator = Generator(hierarchy)

    #     nugget = NuggetContainer()

    #     gene = Gene(
    #         "P00519",
    #         synonyms=["ABL1"],
    #         states=[State("active", True), State("active", False)],
    #         residues=[
    #             Residue("Y", 100, State("phosphorylation", True)),
    #             Residue("S", 500),
    #             Residue("T")
    #         ],
    #         sites=[],
    #         regions=[],
    #         bounds=[],
    #     )

    #     nugget_gene_id = generator._generate_gene(
    #         nugget, gene
    #     )

    #     # check it is consistent
    #     assert(len(nugget.graph.nodes()) == 7)
    #     assert(len(nugget.graph.edges()) == 6)
    #     assert(nugget_gene_id in nugget.graph.nodes())
    #     assert("P00519" in nugget.graph.node[nugget_gene_id]['uniprotid'])
    #     assert(nugget.ag_typing["P00519_active"] == nugget.ag_typing["P00519_active_1"])

    #     print(nugget.meta_typing)
    #     print_graph(nugget.graph)
    #     print_graph(hierarchy.action_graph)

    # def test_region_actor_generator(self):
    #     pass

    # def test_site_actor_generator(self):
    #     pass

    # def test_is_bnd_generator(self):
    #     pass

    # def test_mod_generator(self):
    #     pass

    # def test_bnd_generator(self):
    #     pass
