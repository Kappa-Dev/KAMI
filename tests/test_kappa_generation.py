"""Unit tests for Kappa generation."""
from kami import KamiCorpus
from kami.data_structures.entities import *
from kami.data_structures.interactions import *
from kami.data_structures.definitions import *
from kami.exporters.kappa import (ModelKappaGenerator,
                                  CorpusKappaGenerator)
from tests.resources import (TEST_CORPUS, TEST_MODEL,
                             TEST_DEFINITIONS,
                             TEST_INITIAL_CONDITIONS)


class TestKappaGeneration(object):
    """Class for testing Kappa generation."""

    def __init__(self):
        """."""
        # Create an empty KAMI corpus
        self.corpus = TEST_CORPUS
        self.definitions = TEST_DEFINITIONS
        self.model = TEST_MODEL
        self.initial_conditions = TEST_INITIAL_CONDITIONS

    # def test_generate_from_corpus(self):
    #     """Test generation from corpus."""
    #     # try:
    #     g = CorpusKappaGenerator(
    #         self.corpus, self.definitions,
    #         default_bnd_rate=0.1,
    #         default_brk_rate=0.1,
    #         default_mod_rate=0.1)
    #     k = g.generate(self.initial_conditions)
    #     print(k)
    #     # except:
    #     #     pass

    def test_generate_from_model(self):
        """Test generation from model.."""
        # try:
        g = ModelKappaGenerator(self.model)
        k = g.generate(self.initial_conditions)
        print(k)
        # except:
        #     pass

    # def test_hardcore_is_bound(self):
    #     dummy_partner = SiteActor(
    #         protoform=Protoform("C"),
    #         region=Region(name="Cr"),
    #         site=Site(name="Cs"))

    #     enzyme = SiteActor(
    #         protoform=Protoform("A", bound_to=[dummy_partner]),
    #         region=Region(name="Ar", bound_to=[dummy_partner]),
    #         site=Site(name="As", bound_to=[dummy_partner]))
    #     substrate = SiteActor(
    #         protoform=Protoform("B", bound_to=[dummy_partner]),
    #         region=Region(name="Br", bound_to=[dummy_partner]),
    #         site=Site(name="Bs", bound_to=[dummy_partner]))

    #     mod = Binding(
    #         enzyme,
    #         substrate)

    #     corpus = KamiCorpus("test")
    #     nugget_id = corpus.add_interaction(mod)

    #     g = CorpusKappaGenerator(corpus, [])
    #     k = g.generate()
    #     print(k)

    # def test_toy_example(self):
    #     a = Protoform("A")
    #     b = Protoform("B")
    #     c = Protoform("C")
    #     d = Protoform("D")
    #     e = Protoform("E")

    #     interactions = [
    #         Binding(a, b),
    #         Modification(a, b, State("activity", False), True),
    #         SelfModification(a, target=State("activity", False), value=True),
    #         AnonymousModification(c, target=State("activity", False), value=True),
    #         LigandModification(a, b, target=State("activity", False), value=True),
    #         Binding(
    #             RegionActor(a, Region("REGION", bound_to=[Protoform("C")])),
    #             # Protoform("A", ),
    #             Protoform("B", bound_to=[Protoform("D", bound_to=[Protoform("E")])])),
    #         Modification(
    #             Protoform("A", bound_to=[Protoform("C")]),
    #             Protoform("B", bound_to=[Protoform("D")]),
    #             State("activity", False), True
    #         )
    #     ]
    #     corpus = KamiCorpus("test")
    #     corpus.add_interactions(interactions)

    #     a1 = Product("A1")
    #     a2 = Product("A2")
    #     a1_def = Definition(a, [a1, a2])

    #     b1 = Product("B1")
    #     b2 = Product("B2")
    #     b1_def = Definition(b, [b1, b2])

    #     c1 = Product("C1")
    #     c2 = Product("C2")
    #     c1_def = Definition(c, [c1, c2])

    #     d1 = Product("D1")
    #     d2 = Product("D2")
    #     d1_def = Definition(d, [d1, d2])

    #     e1 = Product("E1")
    #     e2 = Product("E2")
    #     e_def = Definition(e, [e1, e2])

    #     # Single variant for every gene
    #     # try:
    #     g = CorpusKappaGenerator(
    #         corpus, [a1_def, b1_def, c1_def, d1_def, e_def])
    #     k = g.generate()
    #     print(k)
    #     # except Exception as e:
    #     #     print(e)

    #     model = corpus.instantiate(
    #         "Model",
    #         [a1_def, b1_def, c1_def, d1_def, e_def],
    #         default_bnd_rate=0.1,
    #         default_brk_rate=0.1,
    #         default_mod_rate=0.1)
    #     # try:
    #     g = ModelKappaGenerator(model)
    #     k = g.generate()
    #     print(k)
    #     # except Exception as e:
    #     #     print(e)
