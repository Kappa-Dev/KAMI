"""."""
# import warnings
import os
from jpype import (java, startJVM, getDefaultJVMPath, JPackage, isJVMStarted)

# from kami.entities import (Gene, Region, RegionActor,
#                            Residue, Site, SiteActor, State)
# from kami.exceptions import BiopaxImportError, BiopaxImportWarning
# from kami.interactions import (Modification,
#                                AutoModification,
#                                TransModification,
#                                BinaryBinding,
#                                AnonymousModification,
#                                Complex)
# from kami.utils.xrefs import (uniprot_from_xrefs,
#                               names_from_uniprot,
#                               uniprot_from_names
#                               )


class BioPAXModel():
    """Paxtools model for BioPAX data and utils."""

    def __init__(self):
        """Initialize Java and load BioPAX classes of interest."""
        if not isJVMStarted():
            startJVM(
                getDefaultJVMPath(),
                "-ea",
                "-Xmx1g",
                os.path.join(
                    os.path.dirname(__file__), "paxtools/paxtools.jar"))

        self.java_io_ = JPackage("java.io")
        self.paxtools_ = JPackage("org.biopax.paxtools")
        self.io_ = self.paxtools_.io.SimpleIOHandler(
            self.paxtools_.model.BioPAXLevel.L3)

        self.protein_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.Protein", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.protein_reference_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.ProteinReference", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.fragment_feature_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.FragmentFeature", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.modification_feature_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.ModificationFeature", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.small_molecule_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.SmallMolecule", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.small_molecule_reference_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.SmallMoleculeReference", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.rna_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.Rna", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.rna_reference_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.RnaReference", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.complex_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.Complex", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.dna_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.Dna", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.dna_reference_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.DnaReference", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.catalysis_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.Catalysis", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.biochemical_reaction_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.BiochemicalReaction", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.complex_assembly_class_ = java.lang.Class.forName(
            "org.biopax.paxtools.model.level3.ComplexAssembly", True,
            java.lang.ClassLoader.getSystemClassLoader())
        self.model_ = None

    def load(self, filename):
        """Import a BioPAX model from the file."""
        file_is = self.java_io_.FileInputStream(
            filename)
        self.model_ = self.io_.convertFromOWL(file_is)
        file_is.close()

    def is_protein_family(self, reference_id):
        """Check if the protein object is a family."""
        reference = self.model_.getByID(reference_id)
        if len(reference.getMemberEntityReference()) > 0:
            return True
        else:
            physical_entities = reference.getEntityReferenceOf()
            for entity in physical_entities:
                if len(entity.getMemberPhysicalEntity()) > 0:
                    return True
            return False

class BioPaxImporter(object):

    def __init__(self):
        """Initialize BioPaxImporter with empty model."""
        self.data_ = BioPAXModel()

    def collect_modifications(self):
        """Detect and collect modifications and their participants."""
        modifications = []
        catalysis = self.data_.model_.getObjects(
            self.data_.catalysis_class_)
        for reaction in catalysis:
            uri = reaction.getUri()
            print(uri)
        return modifications

    def generate_interactions(self):
        """Generate interactions from loaded BioPAX model."""
        interactions = []
        interactions += self.collect_modifications()
        return interactions

    def import_model(self, filename):
        """Collect the data from BioPAX and generate KAMI interactions."""
        self.data_.load(filename)
        interactions = self.generate_interactions()
        return interactions
