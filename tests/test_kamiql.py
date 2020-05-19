"""Set of unit tests for the KAMIql engine."""
import time
import warnings

from regraph import Neo4jHierarchy

from kami import KamiCorpus
from kami import (Protoform, Region, State, RegionActor,
                  LigandModification, Residue, Site,
                  SiteActor, Binding, SelfModification, AnonymousModification,
                  Product, Definition, Unbinding
                  )

from kamiql.engine import KamiQLEngine


class TestKamiQL:
    """Unit tests for KamiQL."""

    def __init__(self):
        """Initialize tests."""
        # Create an empty KAMI corpus
        self.nxcorpus = KamiCorpus("EGFR_signalling")
        try:
            h = Neo4jHierarchy(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="admin")
            h._clear()
            self.neo4jcorpus = KamiCorpus(
                "egfr",
                backend="neo4j",
                uri="bolt://localhost:7687",
                user="neo4j",
                password="admin")

        except:
            warnings.warn(
                "Neo4j is down, skipping Neo4j-related tests")
            self.neo4jcorpus = None

        # Create an interaction object
        egfr = Protoform("P00533")
        egf = Protoform("P01133")

        kinase = Region(
            name="Protein kinase",
            start=712,
            end=979,
            states=[State("activity", True)])

        egfr_kinase = RegionActor(
            protoform=egfr,
            region=kinase)

        interaction1 = LigandModification(
            enzyme=egfr_kinase,
            substrate=egfr,
            target=Residue(
                "Y", 1092,
                state=State("phosphorylation", False)),
            value=True,
            rate=1,
            desc="Phosphorylation of EGFR homodimer")

        # Aggregate the interaction object to the corpus
        self.nxcorpus.add_interaction(interaction1)
        self.neo4jcorpus.add_interaction(interaction1)

        grb2 = Protoform("P62993", states=[State("activity", True)])
        grb2_sh2 = RegionActor(
            protoform=grb2,
            region=Region(name="SH2"))

        shc1 = Protoform("P29353")
        shc1_pY = SiteActor(
            protoform=shc1,
            site=Site(
                name="pY",
                residues=[Residue("Y", 317, State("phosphorylation", True))]))
        interaction1 = Binding(grb2_sh2, shc1_pY)

        grb2_sh2_with_residues = RegionActor(
            protoform=grb2,
            region=Region(
                name="SH2",
                residues=[
                    Residue("S", 90, test=True),
                    Residue("D", 90, test=False)]))

        egfr_pY = SiteActor(
            protoform=egfr,
            site=Site(
                name="pY",
                residues=[Residue("Y", 1092, State("phosphorylation", True))]))

        interaction2 = Binding(grb2_sh2_with_residues, egfr_pY)

        axl_PK = RegionActor(
            protoform=Protoform("P30530", hgnc_symbol="AXL"),
            region=Region("Protein kinase", start=536, end=807))
        interaction3 = SelfModification(
            axl_PK,
            target=Residue("Y", 821, State("phosphorylation", False)),
            value=True)

        interaction4 = AnonymousModification(
            RegionActor(
                protoform=Protoform(
                    "P30530", hgnc_symbol="AXL",
                    residues=[
                        Residue(
                            "Y", 703, state=State("phosphorylation", True)),
                        Residue(
                            "Y", 779, state=State("phosphorylation", True))
                    ]),
                region=Region(
                    "Protein kinase", start=536, end=807)),
            target=State("activity", False),
            value=True)

        egf_egfr = Protoform(
            egfr.uniprotid,
            bound_to=[egf])
        interaction5 = Binding(
            egf_egfr, egf_egfr)
        interaction6 = Unbinding(egf_egfr, egf_egfr)

        interaction7 = LigandModification(
            egfr_kinase,
            shc1,
            target=Residue("Y", 317, State("phosphorylation", False)),
            value=True,
            enzyme_bnd_region=Region("egfr_BND"),
            enzyme_bnd_site=Site("egfr_BND"),
            substrate_bnd_region=Region("shc1_BND"),
            substrate_bnd_site=Site("sch1_BND"))

        interactions = [
            interaction1,
            interaction2,
            interaction3,
            interaction4,
            interaction5,
            interaction6,
            interaction7
        ]

        self.nxcorpus.add_interactions(interactions)
        self.neo4jcorpus.add_interactions(interactions)

        # Create a protein definition for GRB2
        # protoform = Protoform(
        #     "P62993",
        #     regions=[Region(
        #         name="SH2",
        #         residues=[
        #             Residue("S", 90, test=True),
        #             Residue("D", 90, test=False)])])

        # ashl = Product("Ash-L", residues=[Residue("S", 90)])
        # s90d = Product("S90D", residues=[Residue("D", 90)])
        # grb3 = Product("Grb3", removed_components={"regions": [Region("SH2")]})

        # self.grb2_definition = Definition(protoform, [ashl, s90d, grb3])

        # self.model = self.nxcorpus.instantiate(
        #     "EGFR_signalling_GRB2", [self.grb2_definition],
        #     default_bnd_rate=0.1,
        #     default_brk_rate=0.1,
        #     default_mod_rate=0.1)
        self.query1 = (
            """
            MATCH (:protoform)<--(r1:REGION)-->(i:interaction)-*-(n4:protoform)
            RETURN p1, i, p2;
            """
        )

    # def test_nx_ag_queries(self):
    #     """Test queries on the action graph."""
    #     engine = KamiQLEngine(self.nxcorpus)
    #     start_time = time.time()
    #     engine.query_action_graph(self.query1)
    #     print("NX time: ", time.time() - start_time)

    def test_neo4j_ag_queries(self):
        """Test queries on the action graph."""
        engine = KamiQLEngine(self.neo4jcorpus)
        start_time = time.time()
        engine.query_action_graph(self.query1)
        print("Neo4j time: ", time.time() - start_time)
