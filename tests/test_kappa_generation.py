"""Unit tests for Kappa generation."""
from kami import KamiCorpus
from kami.data_structures.entities import *
from kami.data_structures.interactions import *
from kami.data_structures.definitions import *
from kami.exporters.kappa import (ModelKappaGenerator,
                                  CorpusKappaGenerator,
                                  KappaInitialCondition)


class TestKappaGeneration(object):
    """Class for testing Kappa generation."""

    def __init__(self):
        """."""
        # Create an empty KAMI corpus
        self.corpus = KamiCorpus("EGFR_signalling")

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
        nugget1_id = self.corpus.add_interaction(interaction1)

        # Manually add a new protoform
        new_protoform_node = self.corpus.add_protoform(Protoform("P62993"))

        # Manually add a new components to an arbitrary protoform
        self.corpus.add_site(Site("New site"), new_protoform_node)

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

        nuggets = self.corpus.add_interactions([
            interaction1,
            interaction2,
            interaction3,
            interaction4,
            interaction5,
            interaction6,
            interaction7
        ])

        # Create a protein definition for GRB2
        protoform = Protoform(
            "P62993",
            regions=[Region(
                name="SH2",
                residues=[
                    Residue("S", 90, test=True),
                    Residue("D", 90, test=False)])])

        ashl = Product("Ash-L", residues=[Residue("S", 90)])
        s90d = Product("S90D", residues=[Residue("D", 90)])
        grb3 = Product("Grb3", removed_components={"regions": [Region("SH2")]})

        self.grb2_definition = Definition(protoform, [ashl, s90d, grb3])

        self.model = self.corpus.instantiate(
            "EGFR_signalling_GRB2", [self.grb2_definition],
            default_bnd_rate=0.1,
            default_brk_rate=0.1,
            default_mod_rate=0.1)

        # The following initial condition specifies:
        # 150 molecules of the canonical EGFR protein (no PTMs, bounds or activity)
        # 75 molecules of the EGFR protein with active kinase
        # 30 molecules of the EGFR protein with phosphorylated Y1092
        # 30 molecules of the EGFR protein bound to the SH2 domain of Ash-L through its pY site
        # 30 instances of the EGFR protein dimers
        egfr_initial = KappaInitialCondition(
            canonical_protein=Protein(Protoform("P00533")),
            canonical_count=150,
            stateful_components=[
                (kinase, 75),
                (Residue("Y", 1092, state=State("phosphorylation", True)), 30),
                (Site(
                    name="pY",
                    residues=[Residue("Y", 1092,
                                      state=State("phosphorylation", True))],
                    bound_to=[
                        RegionActor(
                            protoform=grb2, region=Region(name="SH2"),
                            variant_name="Ash-L")
                    ]), 30)
            ],
            bonds=[
                (Protein(Protoform("P00533")), 30, "is_bnd"),
            ])

        # The following initial conditions specify:
        # 200 molecules of the canonical Ash-L (no PTMs, bounds or activity)
        # 40 molecules of Ash-L bound to the pY site of SHC1
        ashl_initial = KappaInitialCondition(
            canonical_protein=Protein(Protoform("P62993"), "Ash-L"),
            canonical_count=200,
            stateful_components=[
                (State("activity", True), 20),
                (Region(name="SH2", bound_to=[shc1_pY]), 40)
            ])

        # 20 mutant molecules S90D
        # 10 molecules of S90D bound to the pY site of EGFR
        s90d_initial = KappaInitialCondition(
            canonical_protein=Protein(Protoform("P62993"), "S90D"),
            canonical_count=45,
            stateful_components=[
                (State("activity", True), 20),
                (Region(name="SH2", bound_to=[egfr_pY]), 10)
            ])

        # 70 molecules of the splice variant Grb3
        grb3_initial = KappaInitialCondition(
            canonical_protein=Protein(Protoform("P62993"), "Grb3"),
            canonical_count=70)

        # The following initial condition specifies:
        # 100 molecules of the canonical SHC1 protein (no PTMs, bounds or activity)
        # 30 molecules of the SHC1 protein phosphorylated at Y317
        shc1_initial = KappaInitialCondition(
            canonical_protein=Protein(Protoform("P29353")),
            canonical_count=100,
            stateful_components=[
                (Residue("Y", 317, state=State("phosphorylation", True)), 30)
            ],
        )

        self.initial_conditions = [
            egfr_initial,
            ashl_initial,
            s90d_initial,
            grb3_initial,
            shc1_initial
        ]

    def test_generate_from_corpus(self):
        """Test generation from corpus."""
        # try:
        g = CorpusKappaGenerator(
            self.corpus, [self.grb2_definition],
            default_bnd_rate=0.1,
            default_brk_rate=0.1,
            default_mod_rate=0.1)
        k = g.generate(self.initial_conditions)
        print(k)
        # except:
        #     pass

    def test_generate_from_model(self):
        """Test generation from model.."""
        # try:
        g = ModelKappaGenerator(self.model)
        k = g.generate(self.initial_conditions)
        print(k)
        # except:
        #     pass

    def test_hardcore_is_bound(self):
        dummy_partner = SiteActor(
            protoform=Protoform("C"),
            region=Region(name="Cr"),
            site=Site(name="Cs"))

        enzyme = SiteActor(
            protoform=Protoform("A", bound_to=[dummy_partner]),
            region=Region(name="Ar", bound_to=[dummy_partner]),
            site=Site(name="As", bound_to=[dummy_partner]))
        substrate = SiteActor(
            protoform=Protoform("B", bound_to=[dummy_partner]),
            region=Region(name="Br", bound_to=[dummy_partner]),
            site=Site(name="Bs", bound_to=[dummy_partner]))

        mod = Binding(
            enzyme,
            substrate)

        corpus = KamiCorpus("test")
        nugget_id = corpus.add_interaction(mod)

        g = CorpusKappaGenerator(corpus, [])
        k = g.generate()
        print(k)

    def test_toy_example(self):
        a = Protoform("A")
        b = Protoform("B")
        c = Protoform("C")
        d = Protoform("D")
        e = Protoform("E")

        interactions = [
            Binding(a, b),
            Modification(a, b, State("activity", False), True),
            SelfModification(a, target=State("activity", False), value=True),
            AnonymousModification(c, target=State("activity", False), value=True),
            LigandModification(a, b, target=State("activity", False), value=True),
            Binding(
                RegionActor(a, Region("REGION", bound_to=[Protoform("C")])),
                # Protoform("A", ),
                Protoform("B", bound_to=[Protoform("D", bound_to=[Protoform("E")])])),
            Modification(
                Protoform("A", bound_to=[Protoform("C")]),
                Protoform("B", bound_to=[Protoform("D")]),
                State("activity", False), True
            )
        ]
        corpus = KamiCorpus("test")
        corpus.add_interactions(interactions)

        a1 = Product("A1")
        a2 = Product("A2")
        a1_def = Definition(a, [a1, a2])

        b1 = Product("B1")
        b2 = Product("B2")
        b1_def = Definition(b, [b1, b2])

        c1 = Product("C1")
        c2 = Product("C2")
        c1_def = Definition(c, [c1, c2])

        d1 = Product("D1")
        d2 = Product("D2")
        d1_def = Definition(d, [d1, d2])

        e1 = Product("E1")
        e2 = Product("E2")
        e_def = Definition(e, [e1, e2])

        # Single variant for every gene
        # try:
        g = CorpusKappaGenerator(
            corpus, [a1_def, b1_def, c1_def, d1_def, e_def])
        k = g.generate()
        print(k)
        # except Exception as e:
        #     print(e)

        model = corpus.instantiate(
            "Model",
            [a1_def, b1_def, c1_def, d1_def, e_def],
            default_bnd_rate=0.1,
            default_brk_rate=0.1,
            default_mod_rate=0.1)
        # try:
        g = ModelKappaGenerator(model)
        k = g.generate()
        print(k)
        # except Exception as e:
        #     print(e)
