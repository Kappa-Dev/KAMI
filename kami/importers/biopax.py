"""Importer from Biopax to KAMI interactions."""
import copy
import os
import re
import warnings
from jpype import (java, startJVM, getDefaultJVMPath,
                   JPackage, isJVMStarted)

from kami.data_structures.entities import Protoform, Residue, Region, State, RegionActor
from kami.data_structures.interactions import Modification, Binding, AnonymousModification


AA = {
    "alanine": ("ala", "A"),
    "arginine": ("arg", "R"),
    "asparagine": ("asn", "N"),
    "aspartic acid": ("asp", "D"),
    "cysteine": ("cys", "C"),
    "glutamine": ("gln", "Q"),
    "glutamic acid": ("glu", "E"),
    "glycine": ("gly", "G"),
    "histidine": ("his", "H"),
    "isoleucine": ("ile", "I"),
    "leucine": ("leu", "L"),
    "lysine": ("lys", "K"),
    "methionine": ("met", "M"),
    "phenylalanine": ("phe", "F"),
    "proline": ("pro", "P"),
    "serine": ("ser", "S"),
    "threonine": ("thr", "T"),
    "tryptophan": ("trp", "W"),
    "tyrosine": ("tyr", "Y"),
    "valine": ("val", "V")
}

STATE_KEYS = {
    "phospho": "phosphorylation",
    "palmitoyl": "palmitoylation",
    "acetyl": "acetylation",
    "ubiquit": "ubiquitination",
    "methyl": "methylation",
    "glycosyl": "glycosylation",
    "sumoyl": "sumoylation",
    "geranylgeranyl": "geranylgeranylation",
    "hydroxyl": "hydroxylation",
    "myristoyl": "myristoylation",
    "farnesyl": "farnesylation",
}


def resolve_aa(modification):
    """Resolve the name of residue amino acid to one letter code."""
    term = list(modification.getTerm())[0]
    letter_aa = "\[residue=([A-Z])\]"
    results = [re.findall(aa, term) for aa in AA.keys()]
    matched_aa = None
    for r in results:
        if len(r) > 0:
            matched_aa = r[0]
    if matched_aa is not None:
        return AA[matched_aa][1]
    else:
        matched_letter_aa = re.findall(letter_aa, term)
        if len(matched_letter_aa) > 0:
            return matched_letter_aa[0]
        else:
            warnings.warn("Could not resolve amino-acid!")
            return None


def resolve_state(state):
    """."""
    for key, name in STATE_KEYS.items():
        if state:
            if "de" + key in state:
                return name, False
            elif key in state:
                return name, True
        else:
            return state
    if state == "residue modification, active":
        return "activity", True
    elif state == "residue modification, inactive":
        return "activity", False
    return state


class BioPAXModel():
    """Paxtools model for BioPAX data and utils."""

    def __init__(self):
        """Initialize Java and load BioPAX classes of interest."""
        if not isJVMStarted():
            startJVM(
                getDefaultJVMPath(),
                "-ea",
                "-Xmx1g",
                "-Djava.class.path=%s" %
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

    def is_fragment(self, protein_id):
        """Check if the protein object is a fragment (region)."""
        protein = self.model_.getByID(protein_id)
        features = protein.getFeature()
        for f in features:
            if f.getModelInterface() == self.fragment_feature_class_:
                return True
        return False

    def get_modifications(self, physical_entity_uri, ignore_features=None):
        """Get all residues and state flags of the physical entity."""
        residues = set()
        flags = set()
        entity = self.model_.getByID(physical_entity_uri)
        features = entity.feature
        for f in features:
            if ignore_features is None or f.getUri() not in ignore_features:
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

    def fetch_protein_reference(self, uri):
        """."""
        protein_reference = self.model_.getByID(uri)
        xrefs = set(protein_reference.getXref())
        uniprotid = None
        # if len(xref) > 1:
        #     warnings.warn(
        #         "Protein reference %s (%s) has ambiguous Unified Reference!" %
        #         (str(protein_reference.getName()), str(protein_reference)))
        # elif len(xref) < 1:
        #     warnings.warn(
        #         "Protein reference %s (%s) does not have Unified Reference!" %
        #         (str(protein_reference.getName()), str(protein_reference)))
        result_xrefs = {}
        for ref in xrefs:
            db = ref.getDb()
            if "uniprot" in ref.getDb().lower():
                uniprotid = ref.getId()
            else:
                result_xrefs[db] = ref.getId()

        if uniprotid is None:
            warnings.warn(
                "Protein reference '{}' does not contain a UniProt ID !".format(
                    protein_reference.getName()))

        name = list(protein_reference.getName())
        locations = set()
        for entity in protein_reference.getEntityReferenceOf():
            location = entity.getCellularLocation()
            if location is not None:
                locations.update(list(location.getTerm()))
        return (uniprotid, result_xrefs, name, locations)

    def fetch_region_reference(self, uri):
        region_feature = self.model_.getByID(uri)
        location = region_feature.getFeatureLocation()

        start = None
        end = None
        start_ref = location.getSequenceIntervalBegin()
        if start_ref is not None:
            start = start_ref.getSequencePosition()
        end_ref = location.getSequenceIntervalEnd()
        if end_ref is not None:
            end = end_ref.getSequencePosition()

        return (start, end)

    def fetch_residue_reference(self, uri):
        residue = self.model_.getByID(uri)
        references = set(
            [el.getEntityReference().getUri() for el in residue.getFeatureOf()]
        )
        if len(references) > 1:
            warnings.warn(
                "Residue (%s) references to more than one protein!" %
                (uri))
        loc =\
            residue.getFeatureLocation().getSequencePosition()
        aa = resolve_aa(residue.getModificationType())
        return (aa, loc)

    def fetch_state_reference(self, uri):
        flag = self.model_.getByID(uri)
        references = set()
        for el in flag.getFeatureOf():
            if el.getModelInterface() == self.complex_class_:
                references.add(el.getUri())
            else:
                references.add(el.getEntityReference().getUri())

        if len(references) > 1:
            warnings.warn(
                "State flag (%s) references to more than one protein!" %
                (uri))
        states = list(flag.getModificationType().getTerm())
        if len(states) == 1:
            return states[0]
        else:
            warnings.warn("Ambiguous state (%s)! Cannot convert to node" %
                          states)

    def get_by_id(self, uri):
        return self.model_.getByID(uri)


class BioPaxImporter(object):

    def __init__(self):
        self.data = BioPAXModel()

    def _process_residues(self, data):
        res = []
        for el in data:
            if el['aa'] is not None or el['loc'] is not None:
                name, val = resolve_state(el['state'])
                res.append(Residue(aa=el['aa'], loc=el['loc'],
                                   state=State(name, val)))
        return res

    def _process_states(self, data):
        res = []
        for el in data:
            s = resolve_state(el)
            if s:
                name, val = s
                res.append(State(name, val))
        return res

    def process_feature(self, feature_uri):
        f = self.data.get_by_id(feature_uri)
        if f.getModelInterface() == self.data.modification_feature_class_:
            if f.getFeatureLocation() is not None:
                aa, loc = self.data.fetch_residue_reference(feature_uri)
                name, value = resolve_state(self.data.fetch_state_reference(
                    feature_uri))
                return (aa, loc, name, value), "residue"
            else:
                name, value = resolve_state(
                    self.data.fetch_state_reference(feature_uri))
                return (name, value), "state"

    def process_protein(self, uri, ignore_features=None):
        protein = self.data.get_by_id(uri)
        ref_uri = protein.getEntityReference().getUri()
        if not self.data.is_protein_family(ref_uri):
            uniprot, xrefs, name, locations =\
                self.data.fetch_protein_reference(ref_uri)
            if uniprot is not None:
                protoform = {}
                protoform["uniprot"] = uniprot
                protoform["xrefs"] = xrefs
                protoform["names"] = name
                protoform["locations"] = locations
                protoform["regions"] = []
                protoform["residues"] = []
                protoform["states"] = []
                region = None
                mods = self.data.get_modifications(uri, ignore_features)
                if self.data.is_fragment(uri):
                    features = protein.getFeature()
                    regions = set()
                    for f in features:
                        if f.getModelInterface() ==\
                           self.data.fragment_feature_class_:
                            regions.add(f.getUri())

                    start, end = self.data.fetch_region_reference(
                        list(regions)[0])
                    region = {"start": start, "end": end, "residues": []}
                    for r_uri in mods["residues"]:
                        aa, loc = self.data.fetch_residue_reference(r_uri)
                        name = self.data.fetch_state_reference(r_uri)
                        protoform["residues"].append(
                            {"aa": aa, "loc": loc, "state": name})
                    for s_uri in mods["flags"]:
                        name = self.data.fetch_state_reference(s_uri)
                        protoform["states"].append(name)
                    if region["start"] is not None or\
                       region["end"] is not None:
                        res = RegionActor(
                            protoform=Protoform(
                                uniprotid=protoform["uniprot"],
                                synonyms=protoform["names"],
                                xrefs=protoform["xrefs"],
                                location=protoform["locations"]),
                            region=Region(
                                start=region["start"],
                                end=region["end"],
                                residues=self._process_residues(
                                    protoform["residues"]),
                                states=self._process_states(protoform["states"])
                            )
                        )
                    else:
                        res = Protoform(
                            uniprotid=protoform["uniprot"],
                            synonyms=protoform["names"],
                            xrefs=protoform["xrefs"],
                            location=protoform["locations"],
                            residues=self._process_residues(protoform["residues"]),
                            states=self._process_states(protoform["states"]))
                else:
                    for r_uri in mods["residues"]:
                        aa, loc = self.data.fetch_residue_reference(r_uri)
                        name = self.data.fetch_state_reference(r_uri)
                        protoform["residues"].append(
                            {"aa": aa, "loc": loc, "state": name})
                    for s_uri in mods["flags"]:
                        name = self.data.fetch_state_reference(s_uri)
                        protoform["states"].append(name)
                    res = Protoform(
                        uniprotid=protoform["uniprot"],
                        synonyms=protoform["names"],
                        xrefs=protoform["xrefs"],
                        location=protoform["locations"],
                        residues=self._process_residues(protoform["residues"]),
                        states=self._process_states(protoform["states"])
                    )
                return res
        return None

    def get_mod_targets(self, source_uri, target_uri):
        mod_targets = {}
        source_features = [
            f.getUri()
            for f in self.data.get_by_id(source_uri).getFeature()]
        target_features = [
            f.getUri()
            for f in self.data.get_by_id(target_uri).getFeature()]
        invariant_set = set(source_features).intersection(set(target_features))
        source_states = dict()
        source_residues = dict()
        for f in source_features:
            if f not in invariant_set:
                res = self.process_feature(f)
                if res is not None:
                    data, t = res
                    if t == "residue":
                        source_residues[(data[0], data[1])] = (data[2], data[3], f)
                    elif t == "state":
                        source_states[data[0]] = (data[1], f)
        target_states = dict()
        target_residues = dict()
        for f in target_features:
            if f not in invariant_set:
                res = self.process_feature(f)
                if res is not None:
                    data, t = res
                    if t == "residue":
                        target_residues[(data[0], data[1])] = (data[2], data[3], f)
                    elif t == "state":
                        target_states[data[0]] = (data[1], f)
        for key, val in source_states.items():
            if key in target_states.keys() and\
               val[0] != target_states[key][0]:
                mod_targets[val[1]] = (key, val[0], target_states[key][0])
            elif key not in target_states.keys():
                mod_targets[val[1]] = (key, val[0], not val[1])
        for key, val in source_residues.items():
            if key in target_residues.keys():
                target_val = target_residues[key]
                if target_val[0] == val[0] and target_val[1] != target_val[1]:
                    mod_targets[val[2]] = (key, val[0], val[1], target_val[1])
            else:
                mod_targets[val[2]] = (key, val[0], val[1], not val[1])

        for key, val in target_states.items():
            if key not in source_states.keys() and\
               val[1] not in mod_targets.keys():
                mod_targets[val[1]] = (key, not val[0], val[0])
        for key, val in target_residues.items():
            if key not in source_residues.keys() and\
               val[2] not in mod_targets.keys():
                mod_targets[val[2]] = (key, val[0], not val[1], val[1])
        return mod_targets

    def get_kami_mod_targets(self, target_dict):
        result = []
        for val in target_dict.values():
            if len(val) == 3:
                name, old_value, new_value = val
                result.append((State(name, old_value), new_value))
            elif len(val) == 4:
                (aa, loc), name, old_value, new_value = val
                result.append((
                    Residue(aa=aa, loc=loc, state=State(name, old_value)),
                    new_value))
        return result

    def get_kami_modification(self, reaction_id, data):
        mods = []
        enzyme_uri = data["enzyme"]
        enzyme = self.process_protein(enzyme_uri)

        init_substrate_uri = data["initial_substrate"]
        res_substrate_uri = data["result_substrate"]
        mod_targets = self.get_mod_targets(
            init_substrate_uri, res_substrate_uri)
        init_substrate = self.process_protein(
            init_substrate_uri, ignore_features=mod_targets.keys())
        mod_targets = self.get_kami_mod_targets(mod_targets)

        if enzyme is not None and init_substrate is not None:
            for target, v in mod_targets:
                mods.append(
                    Modification(
                        enzyme=enzyme,
                        substrate=init_substrate,
                        target=target,
                        value=v
                    )
                )

        activity_def = self.get_activity_def(
            self.process_protein(res_substrate_uri), mod_targets)
        if activity_def is not None:
            mods.append(activity_def)

        return mods

    def get_activity_def(self, substrate, mod_targets):
        activity_def = None

        activation = False
        inactivation = False

        if len(mod_targets) > 1:
            for t, v in mod_targets:
                if isinstance(t, State):
                    if t.name == "activity":
                        if v is True:
                            activation = True
                            break
                        else:
                            inactivation = True
                            break

            if activation is True:
                # remove activity state from the right
                if isinstance(substrate, Protoform):
                    new_substrate = copy.deepcopy(substrate)
                    new_states = []
                    for state in new_substrate.states:
                        if state.name != "activity":
                            new_states.append(state)
                    new_substrate.states = new_states
                    activity_def = AnonymousModification(
                        new_substrate, State("activity", False), True)

                if inactivation is True:
                    if isinstance(substrate, Protoform):
                        new_substrate = copy.deepcopy(substrate)
                        new_states = []
                        for state in new_substrate.states:
                            if state.name != "activity":
                                new_states.append(state)
                        new_substrate.states = new_states
                        activity_def = AnonymousModification(
                            new_substrate, State("activity", True), False)
        return activity_def

    def get_kami_binding(self, reaction_id, data):
        bnds = []
        components = list(data["components"])
        left_uri = components[0].getUri()
        right_uri = components[1].getUri()
        left = self.process_protein(left_uri)
        right = self.process_protein(right_uri)
        if left is not None and right is not None:
            bnds.append(Binding(left, right))

        return bnds

    def collect_modifications(self):
        """Detect and collect modifications and their participants."""
        catalysis = self.data.model_.getObjects(
            self.data.catalysis_class_)
        modification_data = {}
        for reaction in catalysis:
            uri = reaction.getUri()
            # Get controlled reactions (with specified enzyme)
            for controlled_reaction in reaction.getControlled():
                # We are intereseted only in biochemical reactions
                if controlled_reaction.getModelInterface() ==\
                   self.data.biochemical_reaction_class_:
                    lhs = controlled_reaction.getLeft()
                    rhs = controlled_reaction.getRight()
                    if len(lhs) == 1 and len(rhs) == 1:
                        initial_entity = list(lhs)[0]
                        resulting_entity = list(rhs)[0]
                        # If elements match and they are not complexes
                        elements_match = False
                        if initial_entity.getModelInterface() ==\
                           resulting_entity.getModelInterface():
                            if initial_entity.getModelInterface() !=\
                               self.data.complex_class_:
                                if initial_entity.getEntityReference().getUri() ==\
                                   resulting_entity.getEntityReference().getUri():
                                    elements_match = True

                        # If both sides have the same entity
                        if elements_match:
                            modification_data[uri] = {
                                "enzyme": None,
                                "initial_substrate": None,
                                "result_substrate": None
                            }
                            # extract reaction controllers
                            enzymes = []
                            for controller in reaction.getController():
                                if controller.getModelInterface() !=\
                                   self.data.complex_class_:
                                    enzymes.append(controller.getUri())
                            if len(enzymes) == 1:
                                modification_data[uri]["enzyme"] = enzymes[0]

                                # get feature of the substrate before reaction
                                modification_data[uri]["initial_substrate"] =\
                                    initial_entity.getUri()
                                modification_data[uri]["result_substrate"] =\
                                    resulting_entity.getUri()
                            if modification_data[uri]["enzyme"] is None or\
                               modification_data[uri]["initial_substrate"] is None:
                                del modification_data[uri]

        return modification_data

    def collect_bnd(self):
        complex_assembly = self.data.model_.getObjects(
            self.data.complex_assembly_class_)
        bnd_data = {}
        for reaction in complex_assembly:
            uri = reaction.getUri()
            components = reaction.getLeft()
            comp = reaction.getRight()
            if len(components) == 2 and len(comp) == 1:
                # Check component types
                all_proteins = True
                for c in components:
                    if c.getModelInterface() !=\
                       self.data.protein_class_:
                        all_proteins = False
                        break

                # Check stochiometry (expecting 1/1)
                stochiometry = reaction.getParticipantStoichiometry()
                all_single_molecule = True
                for s in stochiometry:
                    coef = s.getStoichiometricCoefficient()
                    if int(coef) != 1:
                        all_single_molecule = False
                        break

                if all_single_molecule and all_proteins:
                    bnd_data[uri] = {
                        "components": components,
                        "complex": comp
                    }
        return bnd_data

    def generate_interactions(self):
        """Protoformrate interactions from loaded BioPAX model."""
        interactions = []
        mod_data = self.collect_modifications()
        for k, v in mod_data.items():
            interactions += self.get_kami_modification(k, v)

        bnd_data = self.collect_bnd()
        for k, v in bnd_data.items():
            interactions += self.get_kami_binding(k, v)

        return interactions

    def import_model(self, filename):
        """Collect the data from BioPAX and generate KAMI interactions."""
        self.data.load(filename)
        interactions = self.generate_interactions()
        return interactions
