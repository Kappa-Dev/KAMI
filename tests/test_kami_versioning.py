"""."""
from kami import KamiCorpus, Protoform, Region, Site, Residue, State

from tests.resources import (TEST_CORPUS, TEST_MODEL,
                             TEST_DEFINITIONS,
                             TEST_INITIAL_CONDITIONS)


class TestKamiVersioning(object):
    """Class for testing versioning of KamiCorpus and KamiModel."""

    def __init__(self):
        """Initialize tests."""
        self.corpus = TEST_CORPUS
        # self.corpus._versioning.print_history()
        self.model = TEST_MODEL
        self.model._versioning.print_history()
        print()


    def test_audit_actions(self):
        pass


    def test_record_manual_rewrites(self):
        # Perform a bunch of manual updates
        self.corpus.add_mod()
        self.corpus.add_bnd()
        gene_node = self.corpus.add_protoform(Protoform("P00533"))
        region_node = self.corpus.add_region(
            Region("Protein kinase", start=100, end=200), gene_node)

        self.corpus.add_site(Site("Lala1"), gene_node)
        site_node = self.corpus.add_site(Site("Lala2"), region_node)
        residue_node = self.corpus.add_residue(Residue("S", 100), site_node)
        self.corpus.add_state(State("phosphorylation", True), residue_node)

        # self.corpus._versioning.print_history()
