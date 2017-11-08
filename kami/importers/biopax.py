"""."""
from jpype import (java, startJVM, getDefaultJVMPath, JPackage)

from kami.entities import (Agent, Residue, State,
                           NuggetAnnotation,
                           PhysicalAgent)
from kami.exceptions import IndraImportError, IndraImportWarning
from kami.interactions import (Modification,
                               AutoModification,
                               TransModification,
                               BinaryBinding,
                               AnonymousModification,
                               Complex)
from kami.utils.xrefs import (uniprot_from_xrefs,
                              names_from_uniprot,
                              uniprot_from_names
                              )


class BioPAXModel():
    """Paxtools model for BioPAX data and utils."""

    def __init__(self):
        """Initialize Java and load BioPAX classes of interest."""
        startJVM(
            getDefaultJVMPath(),
            "-ea",
            "-Xmx1g",
            "-Djava.class.path=paxtools.jar")

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

    def is_complex_family(self, complex_id):
        """Check if the complex object is a family."""
        complex = self.model_.getByID(complex_id)
        return len(complex.getMemberPhysicalEntity()) > 0

    def is_fragment(self, protein_id):
        """Check if the protein object is a fragment (region)."""
        protein = self.model_.getByID(protein_id)
        features = protein.getFeature()
        for f in features:
            if f.getModelInterface() == self.fragment_feature_class_:
                return True
        return False

    def is_flag(self, feature_id):
        """Check if the feature is a state flag."""
        feature = self.model_.getByID(feature_id)
        if feature.getModelInterface() == self.modification_feature_class_:
            if feature.getFeatureLocation() is None:
                return True
        return False

    def is_residue(self, feature_id):
        """Check if the feature is a residue."""
        feature = self.model_.getByID(feature_id)
        if feature.getModelInterface() == self.modification_feature_class_:
            if feature.getFeatureLocation() is not None:
                return True
        return False

    def is_fragment_feature(self, feature_id):
        """Check if the feature is a fragment (region) definition."""
        feature = self.model_.getByID(feature_id)
        if feature.getModelInterface() == self.fragment_feature_class_:
            return True
        return False

    def protein_reference_to_node(self, protein_reference_id):
        """Convert protein reference data to node."""
        protein_reference = self.model_.getByID(protein_reference_id)
        xref = set(protein_reference.getXref())
        if len(xref) > 1:
            warnings.warn(
                "Protein reference %s (%s) has ambiguous Unified Reference!" %
                (str(protein_reference.getName()), str(protein_reference)))
        elif len(xref) < 1:
            warnings.warn(
                "Protein reference %s (%s) does not have Unified Reference!" %
                (str(protein_reference.getName()), str(protein_reference)))

        protein_attrs = {}
        if len(xref) == 1:
            protein_id = list(xref)[0]
            protein_attrs[protein_id.getDb()] = protein_id.getId()
        if len(xref) > 1:
            for el in xref:
                protein_attrs[el.getDb()] = el.getId()

        protein_attrs["Name"] = list(protein_reference.getName())
        locations = set()
        for entity in protein_reference.getEntityReferenceOf():
            location = entity.getCellularLocation()
            if location is not None:
                locations.update(list(location.getTerm()))
        if len(locations) > 0:
            protein_attrs["loc"] = list(locations)

        return (protein_reference.getUri(), "protein", protein_attrs)

    def region_to_node(self, region_feature_id):
        """Convert region data to node."""
        region_feature = self.model_.getByID(region_feature_id)
        location = region_feature.getFeatureLocation()
        region_id = region_feature.getUri()
        region_attrs = {}
        start = location.getSequenceIntervalBegin()
        if start is not None:
            region_attrs["start"] = start.getSequencePosition()
        end = location.getSequenceIntervalEnd()
        if end is not None:
            region_attrs["end"] = end.getSequencePosition()

        return (region_id, "region", region_attrs)

    def residue_to_node(self, residue_id, protein_id=None):
        """Convert residue data to node."""
        residue = self.model_.getByID(residue_id)
        references = set(
            [el.getEntityReference().getUri() for el in residue.getFeatureOf()]
        )
        if len(references) > 1:
            warnings.warn(
                "Residue (%s) references to more than one protein!" %
                (residue_id))
        residue_attrs = {}
        residue_attrs["loc"] =\
            residue.getFeatureLocation().getSequencePosition()
        aa = resolve_aa(residue.getModificationType())
        if aa is not None:
            residue_attrs["aa"] = aa
        return ("%s_residue_%s" %
                (protein_id, residue_id), "residue", residue_attrs)

    def flag_to_node(self, flag_id, protein_id=None):
        """Convert state flag data to node."""
        flag = self.model_.getByID(flag_id)
        references = set()
        for el in flag.getFeatureOf():
            if el.getModelInterface() == self.complex_class_:
                references.add(el.getUri())
            else:
                references.add(el.getEntityReference().getUri())

        if len(references) > 1:
            warnings.warn(
                "State flag (%s) references to more than one protein!" %
                (flag_id))
        flag_attrs = {}
        states = list(flag.getModificationType().getTerm())
        if len(states) == 1:
            flag_attrs[states[0]] = [0, 1]
            return ("%s_flag_%s" % (protein_id, flag_id), "state", flag_attrs)
        else:
            warnings.warn("Ambiguous state (%s)! Cannot convert to node" %
                          states)

    def family_reference_to_node(self, family_reference_id):
        """Convert family reference data to node."""
        family_reference = self.model_.getByID(family_reference_id)
        family_attrs = {}
        family_attrs["Name"] = list(family_reference.getName())

        return (family_reference.getUri(), "family", family_attrs)

    def small_molecule_to_node(self, small_molecule_id):
        """Convert small molecule data to node."""
        small_molecule_reference = self.model_.getByID(small_molecule_id)
        xref = set(small_molecule_reference.getXref())
        if len(xref) > 1:
            warnings.warn(
                "Small molecule reference %s (%s) has ambiguous Unified Reference!" %
                (str(small_molecule_reference.getName()), str(small_molecule_reference)))
        elif len(xref) == 0:
            warnings.warn(
                "Small molecule reference %s (%s) does not have Unified Reference!" %
                (str(small_molecule_reference.getName()), str(small_molecule_reference)))

        molecule_attrs = {}
        if len(xref) == 1:
            molecule_id = list(xref)[0]
            molecule_attrs[molecule_id.getDb()] = molecule_id.getId()
        elif len(xref) > 1:
            for el in xref:
                molecule_attrs[el.getDb()] = el.getId()
        molecule_attrs["Name"] = list(small_molecule_reference.getName())
        physical_entities = small_molecule_reference.getEntityReferenceOf()
        locations = set()
        for entity in physical_entities:
            location = entity.getCellularLocation()
            if location is not None:
                locations.update(list(location.getTerm()))
        if len(locations) > 0:
            molecule_attrs["loc"] = list(locations)
        return (small_molecule_reference.getUri(), "small_molecule", molecule_attrs)

    def complex_to_node(self, complex_id):
        """Convert complex data to node."""
        complex = self.model_.getByID(complex_id)
        complex_attrs = {}
        complex_attrs["Name"] = list(complex.getName())
        if complex.getCellularLocation() is not None:
            complex_attrs["loc"] = list(
                complex.getCellularLocation().getTerm())
        return (complex.getUri(), "complex", complex_attrs)

    def modification_to_node(self, reaction_id, target):
        """Convert modification data to node."""
        reaction = self.model_.getByID(reaction_id)
        reaction_attrs = {}
        for xref in reaction.getXref():
            if xref.getDb() in reaction_attrs.keys():
                reaction_attrs[xref.getDb()].append(xref.getId())
            else:
                reaction_attrs[xref.getDb()] = [xref.getId()]
        if reaction.getCatalysisDirection() is not None:
            reaction_attrs["direction"] = str(reaction.getCatalysisDirection())
        reaction_attrs["evidence"] = set()
        for evidence in reaction.getEvidence():
            code = list(evidence.getEvidenceCode())[0]
            xref = list(code.getXref())[0]
            reaction_attrs["evidence"].add(xref.getId())
        reaction_attrs["evidence"] = list(reaction_attrs["evidence"])
        return ("%s_of_%s" % (reaction_id, target), "MOD", reaction_attrs)

    def get_modifications(self, physical_entities):
        """Get all residues and state flags of the physical entity."""
        residues = set()
        flags = set()
        for e in physical_entities:
            entity = self.model_.getByID(e)
            features = entity.feature
            for f in features:
                if f.getModelInterface() == self.modification_feature_class_:
                    if f.getFeatureLocation() is not None:
                        residues.add(f.getUri())
                    else:
                        flags.add(f.getUri())
        return {"residues": residues, "flags": flags}

    def residue_in_region(self, residue_id, region_id):
        """Test whether residue lies in the given region."""
        residue = self.model_.getByID(residue_id)
        region = self.model_.getByID(region_id)

        region_location = region.getFeatureLocation()
        region_start = region_location.getSequenceIntervalBegin()
        region_end = region_location.getSequenceIntervalEnd()

        residue_location = residue.getFeatureLocation()
        if region_start is not None and\
           region_end is not None and\
           residue_location is not None:
            x = residue_location.getSequencePosition()
            start = region_start.getSequencePosition()
            end = region_end.getSequencePosition()
            return (x >= start) and (x <= end)
        else:
            return False


class BioPaxImporter(object):

    def __init__(self):
        self.data_ = BioPAXModel()

    def import_model(self, filename):
        """Collect the data from BioPAX and generate KAMI interactions."""
        self.data_.load(filename)
        interactions = []

        return interactions
