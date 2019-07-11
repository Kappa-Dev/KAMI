"""Importer from IntAct to KAMI interactions."""

# Usage:
# from kami.importers.intact import IntActImporter
# intact = IntActImporter()
# kami_interactions = intact.import_model([file_list])

# Notes:
#
# The IntAct interaction type dictates if the resulting KAMI interaction will 
# be a Binding or a Modification. The type of a given inteaction is stored in 
# the field "entry/interactionList/interaction/interactionType/names/fullName"
# of the IntAct xml file.
#
#
# IntAct interaction types that express Bindings are
# (from the least to the most detailed):
#                              ___
#  colocalization                |--> Ignored
#  association                   |
#  └─ physical association     __|     ___
#     └─ direct interaction              |
#        ├─ self interaction             |
#        ├─ putative self interaction    |--> Dealt with in method get_binding
#        └─ covalent binding             |
#           └─ disulfide bond          __|
#
# "physical association" accounts for ~87% of all human IntAct data
# (256819 interactions). They are not necessarily direct interactions, so they
# are ignored for now. Some way to include them should be sought. They could
# be included only if they have specified binding features. This would still
# be a very simplistic strategy since specified binding features do not ensure
# that the interaction is a direct binding.
#
#
# IntAct interaction types that express Modifications:
# 
#  enzymatic reaction                 ___
#  ├─ phosphorylation reaction          |
#  ├─ dephosphorylation reaction        |
#  ├─ methylation reaction              |
#  ├─ demethylation reaction            |
#  ├─ acetylation reaction              |
#  ├─ deacetylation reaction            |
#  ├─ ubiquitination reaction           |
#  ├─ deubiquitination reaction         |--> Dealt with in method
#  ├─ palmitoylation reaction           |    get_general_reaction
#  ├─ depalmitoylation reaction         |
#  ├─ demyristoylation reaction         |
#  ├─ deamination reaction              |
#  ├─ deamidation reaction              |
#  ├─ glycosylation reaction            |
#  ├─ hydroxylation reaction            |
#  ├─ sumoylation reaction              |
#  ├─ neddylation reaction              |
#  ├─ ampylation reaction             __|   ___
#  ├─ gtpase reaction                         |
#  ├─ atpase reaction                         |
#  ├─ phospholipase reaction                  |
#  ├─ phosphotransfer reaction                |
#  ├─ adp ribosylation reaction               |
#  ├─ isomerase reaction                      |
#  │  └─ proline isomerization reaction       |--> Not still impletemented
#  ├─ dna strand elongation                   |
#  └─ cleavage reaction                       |
#     ├─ protein cleavage                     |
#     ├─ lipid cleavage                       |
#     ├─ lipoprotein cleavage reaction        |
#     ├─ dna cleavage                         |
#     └─ rna cleavage                       __|

# Only interactions that involve exactly 2 participants are included for now.
# This misses important information, like some interactions where there are 3
# participants given, one of which is an inhibitor.

# By default, Modifications are built following a one-step policy. Thats means 
# there is no binding required before the modification. If a binding region is
# explicitly given in the interaction, then both a Binding and a
# LigandModification that tests the binding are created. The option to impose
# a two-step policy even if no binding region is given should be added in the
# future.

# I never create Sites from IntAct features. This means that binding conflicts
# will never happen in the imported KAMI model with the actual version of the
# IntActImporter.

# For every Binding interaction, I assume that any feature which is not a 
# binding region (binding region, required to bind or sufficient to bind) is 
# a prerequisite, even if it is not explicitly specified from the featureRole.
# For every Modification interaction, I assume that any feature which is not
# a binding region is a resulting modification unless explicitly specified as 
# a prerequisite.

# The featureRange is sometimes given a beginInterval or endInterval instead 
# of just begin and end. Then the beginInterval itself has a begin and a end 
# instead of just a position. Right now I just read the begin of a 
# beginInterval and the end of a endInterval. Maybe we could add to Kami the 
# possibility of having intervals to start and end of regions, for when the 
# exact start and end positions are not certain.

from lxml import etree
import anatomizer.new_anatomizer as anatomizer
from kami.entities import *
from kami.interactions import *


class IntActImporter(object):

    def __init__(self, identify=True, anatomize=True):
        self.identify = identify
        self.anatomize = anatomize
        self.ignore_features = ["tag", "label", "mutation", "uncategorized",
                                "fusion protein", "experimental feature",
                                "biological feature"]
        self.accepted_range_types = ["certain", "range"]
        self.two_or_less_participants = True
        self.interpro_version = "66"
        self.entry_list = None
        self.namespace_map = None
        self.raw_interactions = []
        self.prefiltered_interactions = []

# ------------------------- Reading section ----------------------------------

    def load(self, filename):
        """Load an IntAct xml file."""
        xml_file = open(filename, "rb").read()
        xml_root = etree.fromstring(xml_file)
        self.namespace_map = xml_root.nsmap
        self.entry_list = xml_root.findall('entry', self.namespace_map)

    def read_interactions(self, file_list):
        """
        Read every interaction from every entry of an IntAct xml file.
        Interaction reading must be done per "entry" because interactor ids
        are defined on a per entry basis in the IntAct xml files.
        """
        if not isinstance(file_list, list):
           file_list = [file_list]
        print(len(file_list), "files to read.")
        for filename in file_list:
            print("Reading file", filename)
            self.load(filename)
            for entry in self.entry_list:
                self.collect_interactors(entry)
                entry_inters = self.collect_interactions(entry)
                self.raw_interactions.extend(entry_inters)
        self.compute_statistics()

    def collect_interactors(self, entry):
        """
        Collect the raw interactors from an IntAct xml entry.
        Interactors that are themselves complexes are kept in a separate list.
        """
        interactor_list = entry.findall('interactorList/interactor',
            self.namespace_map)
        self.interactors = {} # overwritten for every new entry.
        for interactor in interactor_list:
            interactor_id = interactor.get('id')
            interactor_name = interactor.find('names/shortLabel',
                self.namespace_map).text
            self.interactors[interactor_id] = interactor_name
        complex_list = entry.findall('interactionList/abstractInteraction',
            self.namespace_map)
        self.complexes = {} # overwritten for every new entry.
        for complexx in complex_list:
            complex_id = complexx.get('id')
            complex_name = complexx.find('names/shortLabel',
                self.namespace_map).text
            self.complexes[complex_id] = complex_name        

    def collect_interactions(self, entry):
        """
        Collect the raw interactions from an IntAct xml entry. 
        Every interaction is kept at this point. Filtering is done in 
        subsequent methods.
        """
        entry_interactions = []
        inter_list = entry.findall('interactionList/interaction',
            self.namespace_map)
        for inter in inter_list:
            inter_dict = {}
            inter_dict["desc"] = inter.find('names/shortLabel',
                self.namespace_map).text
            inter_dict["type"] = inter.find('interactionType/names/fullName',
                self.namespace_map).text
            inter_dict["participants"] = self.collect_participants(inter)
            entry_interactions.append(inter_dict)
        return entry_interactions

    def collect_participants(self, inter):
        """Collect the participants of a given interaction."""
        participants = []
        participant_list = inter.findall('participantList/participant',
            self.namespace_map)
        for participant in participant_list:
            participant_dict = {}
            try: # The participant may be a specific protein.
                interactor_ref = participant.find('interactorRef',
                    self.namespace_map).text
                participant_dict["id"] = self.interactors[interactor_ref]
            except: # Or the participant may be a complex.
                complex_ref = participant.find('interactionRef',
                    self.namespace_map).text
                participant_dict["complex_ac"] = self.complexes[complex_ref]
                participant_dict["id"] = self.complexes[complex_ref]
            participant_dict["biological_role"] = participant.find(
                'biologicalRole/names/shortLabel', self.namespace_map).text
            participant_dict["features"] = self.collect_features(participant)
            participants.append(participant_dict)
        return participants

    def collect_features(self, participant):
        """Collect the features of a given participant."""
        features = []
        feature_list = participant.findall('featureList/feature',
            self.namespace_map)
        for feature in feature_list:
            feature_dict = {}
            feature_dict["name"] = feature.find('names/shortLabel',
                self.namespace_map).text
            feature_dict["type"] = feature.find('featureType/names/shortLabel',
                self.namespace_map).text
            try:
                feature_dict["role"] = feature.find('featureRole/names/shortLabel',
                    self.namespace_map).text
            except:
                pass
            feat_range = self.collect_range(feature)
            feature_dict["start"] = feat_range[0]
            feature_dict["end"] = feat_range[1]
            # Collect InterPro ID if directly specified in file. If not found, 
            # a subsequent method will try to complete it using the anatomizer.
            primary_xref = feature.find('xref/primaryRef', self.namespace_map)
            database = primary_xref.get("db")
            if database == "interpro":
                feature_dict["interpro"] = primary_xref.get("id")
            else:
                feature_dict["interpro"] = None
            features.append(feature_dict)
        return features

    def collect_range(self, feature):
        """
        Collect the range of a given feature. The ouputs of that method are
        strings instead of integers to accomodate values like "n-term range".
        Those value must however be later converted to integers to be readable
        by KAMI.
        """
        feature_range = feature.find('featureRangeList/featureRange',
            self.namespace_map)
        start_status = feature_range.find('startStatus/names/shortLabel',
            self.namespace_map).text
        end_status = feature_range.find('endStatus/names/shortLabel',
            self.namespace_map).text
        # Start position.
        feature_start = "undetermined"
        if start_status in self.accepted_range_types:
            try:
                feature_start = feature_range.find('begin',
                    self.namespace_map).get("position")
            except:
                feature_start = feature_range.find('beginInterval',
                    self.namespace_map).get("begin")
        elif start_status == "n-term range":
            feature_start = "n-term"
        elif start_status == "c-term range":
            feature_start = "c-term"
        # End position.
        feature_end = "undetermined"
        if end_status in self.accepted_range_types:
            try:
                feature_end = feature_range.find('end',
                    self.namespace_map).get("position")
            except:
                feature_start = feature_range.find('endInterval',
                    self.namespace_map).get("end")
        elif end_status == "n-term range":
            feature_end = "n-term"
        elif end_status == "c-term range":
            feature_end = "c-term"
        return [feature_start, feature_end]

# --------------------- End of reading section -------------------------------


# +++++++++++++++++++++ Interaction sorting section ++++++++++++++++++++++++++

    def prefilter_interactions(self):
        """
        Sort interactions to select the ones we can represent in KAMI.
        """
        # General reactions are any interaction with the string 
        # "ation reaction" in its type. They are all KAMI modifications and
        # include:
        # phosphorylation reaction
        # dephosphorylation reaction
        # methylation reaction
        # demethylation reaction
        # acetylation reaction
        # deacetylation reaction
        # ubiquitination reaction
        # deubiquitination reaction
        # palmitoylation reaction
        # depalmitoylation reaction
        # demyristoylation reaction
        # deamination reaction
        # deamidation reaction
        # glycosylation reaction
        # hydroxylation reaction
        # sumoylation reaction
        # neddylation reaction
        # ampylation reaction 
        self.general_reactions = []
        # Bindings are interactions that has any of the following types:
        # (I do not support "self interaction" and
        # "putative self interaction" for now)
        binding_types = ["direct interaction", "covalent binding",
                         "disulfide bond"]
        self.bindings = []
        self.ignored_interactions = []
        two_or_less = self.two_or_less_participants
        for raw_inter in self.raw_interactions:
            # I include only interactions that have 1 or 2 participants.
            # For the human dataset, that includes 94% of all interactions.
            n_part = self._count_participants(raw_inter)
            #if two_or_less == False or (two_or_less == True and n_part <= 2):
            if n_part == 2:
                ok_participants = True
            else:
                ok_participants = False
                self.ignored_interactions.append(raw_inter)
            # Classify every interactions.
            if ok_participants == True:
                # General reactions.
                if "ation reaction" in raw_inter["type"]:
                    # Need to know which is enzyme and which is target.
                    cond1 = True
                    cond2 = True
                    for participant in raw_inter["participants"]:
                        if participant["biological_role"] == "unspecified role":
                            cond1 = False
                        if "self" in participant["biological_role"]:
                            cond2 = False
                    if cond1 == True and cond2 == True:
                        self.general_reactions.append(raw_inter)
                    else:
                        self.ignored_interactions.append(raw_inter)
                # Bindings.
                elif raw_inter["type"] in binding_types:
                    self.bindings.append(raw_inter)
                # Ignored interactions.
                else:
                    self.ignored_interactions.append(raw_inter)

# +++++++++++++++++++++ End of interaction sorting section +++++++++++++++++++


# ===================== KAMI interactions section ============================

    def get_binding(self, data):
        """General import method for KAMI Bindings."""
        description = "binding {}".format(data["desc"])
        note="IntAct {}".format(data["type"])
        state_key = "binding"
        left_side = data["participants"][0]
        right_side = data["participants"][1]
        left_part = self.participant_details(left_side, state_key)
        right_part = self.participant_details(right_side, state_key)
        kami_binding = self.build_binding(
            left_part, right_part, description, note
        )
        return kami_binding

    def get_general_reaction(self, data):
        """
        General import method for any IntAct interaction that has the string
        'ation reaction' in its interactions type. They are all KAMI 
        Modifications. The state is set to False if the interaction type
        starts with 'de'.
        """
        #print(data)
        kami_inters = []
        description = data["desc"]
        note="IntAct {}".format(data["type"])
        state_tokens = data["type"].split()
        state_string = state_tokens[0]
        if state_string[:2] == "de":
            state_key = state_string[2:]
            mod_value = False
            init_value = True
        else:
            state_key = state_string
            mod_value = True
            init_value = False
        kami_state = State(state_key, init_value)
        # Gather the information about the identity and the features of 
        # each participant.
        for participant in data["participants"]:
            if participant["biological_role"] == "enzyme":
                enzyme_part = self.participant_details(participant,
                                                       state_key)
            if participant["biological_role"] == "enzyme target":
                substrate_part = self.participant_details(participant,
                                                          state_key)
        # Check if there is any binding region in the interaction.
        feature_types = []
        for ft in enzyme_part["features"]:
            feature_types.append(ft["kind"])
        for ft in substrate_part["features"]:
            feature_types.append(ft["kind"])
        # If there is at least one binding region, I need to create a
        # Binding and a LigandModification instead of just a Modification.
        if "region" in feature_types:
            desc = "bnd of {}".format(description)
            kami_binding = self.build_binding(
                enzyme_part, substrate_part, desc, note
            )
            kami_inters += kami_binding
        # Method self.build_mods automatically creates a
        # LigandModification if binding regions are present.
        kami_mods = self.build_mods(
            enzyme_part, substrate_part, kami_state, mod_value, 
            description, state_key, note
        )
        kami_inters += kami_mods
        return kami_inters

    def participant_details(self, participant, rxn_type):
        """Obtain details about a given the participant."""
        gene = {}
        gene["uniprot_id"] = participant["id"]
        gene["uniprot_ac"] = None
        gene["hgnc_symbol"] = None
        gene["hgnc_id"] = None
        gene["synonyms"] = None
        gene["domains"] = None
        if self.identify == True:
            gene = self.identify_protein(participant)
            unip = gene["uniprot_id"]
            if unip != None and unip != "Unknown":
                pass
            else:
                gene["uniprot_id"] = participant["id"]
        # Get the list of features. ft_list also contains information
        # on the type and role of the features.
        ft_list = self.process_features(participant["features"], gene,
                                        participant["biological_role"],
                                        rxn_type)
        return {"gene":gene, "features":ft_list}

    def build_binding(self, left_part, right_part, descript, annotate):
        """
        Build a KAMI Binding for the association of an enzyme to its
        substrate prior to catalysis.
        """
        left_participant = self.binding_actor(left_part)
        right_participant = self.binding_actor(right_part)
        kami_binding = Binding(
            left_participant,
            right_participant,
            desc=descript,
            annotation=annotate
        )
        return [kami_binding]

    def binding_actor(self, participant):
        """Build the binding actor of a given participant."""
        protein = Gene(
            uniprotid=participant["gene"]["uniprot_id"],
            hgnc_symbol=participant["gene"]["hgnc_symbol"],
            synonyms=participant["gene"]["synonyms"]
        )
        # Gather all binding regions of the participant.
        ft_regions = []
        for ft in participant["features"]:
            if ft["kind"] == "region":
                ft_regions.append(ft["entity"])
        # Build actor accordingly to number of binding regions.
        if len(ft_regions) == 0:
            actor = protein
        if len(ft_regions) == 1:
            actor = RegionActor(
                gene=protein,
                region=ft_regions[0]
            )
        if len(ft_regions) > 1:
            actor = SiteActor(
                gene=protein,
                site=Site(name="multisite"),
                region=ft_regions
            )
        return actor

    def build_mods(self, enz_part, sub_part, kami_state, mod_val,
                   desc, state_str, annotate):
        """Build a KAMI Modification or LigandModification."""
        # Automatically creates a LigandModification if binding regions are
        # present and a normal Modification if no binding region is given.
        # I do not know how to deal with many binding regions on a same
        # protein in LigandModifications. So I always take only the first
        # listed binding region.
        mod_inters = []
        enzyme_protein = Gene(
            uniprotid=enz_part["gene"]["uniprot_id"],
            hgnc_symbol=enz_part["gene"]["hgnc_symbol"],
            synonyms=enz_part["gene"]["synonyms"]
        )
        substrate_protein = Gene(
            uniprotid=sub_part["gene"]["uniprot_id"],
            hgnc_symbol=sub_part["gene"]["hgnc_symbol"],
            synonyms=sub_part["gene"]["synonyms"]
        )
        # Find all the prerequisite states and residues (containing a state).
        enz_residues, enz_states = self._find_prerequisites(enz_part)
        sub_residues, sub_states = self._find_prerequisites(sub_part)
        if len(enz_residues) > 0:
            enzyme_protein.residues = enz_residues
        if len(enz_states) > 0:
            enzyme_protein.states = enz_states
        if len(sub_residues) > 0:
            substrate_protein.residues = sub_residues
        if len(sub_states) > 0:
            substrate_protein.states = sub_states
        # Find the binding regions on enzyme and substrate. I do not know how
        # to deal with many binding regions on a same protein in 
        # LigandModifications. So I always just take the first listed binding
        # region.
        enzyme_region = None
        substrate_region = None
        for ft in enz_part["features"]:
            if ft["kind"] == "region":
                enzyme_region = ft["entity"]
                break
        for ft in sub_part["features"]:
            if ft["kind"] == "region":
                substrate_region = ft["entity"]
                break
        # Check how many resulting features there are on the substrate.
        resulting_feature_ents = []
        for ft in sub_part["features"]:
            if ft["role"] == "resulting":
                resulting_feature_ents.append(ft["entity"])
        if len(resulting_feature_ents) == 0:
            resulting_feature_ents.append(kami_state)
        # Create one LigandModification per resulting feature on substrate.
        n_desc = 0
        descript = desc
        for ft_ent in resulting_feature_ents:
            if len(resulting_feature_ents) > 1:
                n_desc += 1
                descript = "{}-{}".format(desc, n_desc)
            target_on_substrate = ft_ent
            if isinstance(ft_ent, Residue):
                ft_state = target_on_substrate.state.name
                target_on_substrate.state = kami_state
            if isinstance(ft_ent, State):
                ft_state = target_on_substrate.name
                target_on_substrate = kami_state
            if ft_state != state_str:
                warnings.warn("Resulting modification does not match "
                              "reaction type in interaction "
                              "{}".format(desc))
            if enzyme_region == None and substrate_region == None:
                mod_inter = Modification(
                    enzyme=enzyme_protein,
                    substrate=substrate_protein,
                    target=target_on_substrate,
                    value=mod_val,
                    desc=descript,
                    annotation=annotate
                )
                mod_inters.append(mod_inter)
            else:
                ligandmod_inter = LigandModification(
                    enzyme=enzyme_protein,
                    substrate=substrate_protein,
                    target=target_on_substrate,
                    value=mod_val,
                    desc=descript,
                    annotation=annotate
                )
                if enzyme_region != None:
                    ligandmod_inter.enzyme_bnd_region = enzyme_region
                if substrate_region != None:
                    ligandmod_inter.substrate_bnd_region = substrate_region
                mod_inters.append(ligandmod_inter)
        return mod_inters

    def process_features(self, features, gene, participant_role, rxn_type):
        """
        Process a list of features. Use gene information to try complement
        feature information, like InterPro short name. Also use participant
        role to know if a given feature should be a prerequisite feature or a 
        resulting feature. Finally, decide if a feature should be a region,
        residue or state."""
        accepted_features = []
        for feature in features:
            accept_feature = True
            for ignored_ft in self.ignore_features:
                if ignored_ft in feature["type"]:
                    accept_feature = False
                    break
            if accept_feature == True:
                accepted_features.append(feature)
        # Count the number of residue features that are resulting-ptms if
        # protein is a substrate (enzyme target). This is necessary later on
        # to decide feature roles when they are not explicitly given.
        residue_features = ["phosres", "optyr", "opser", "opthr",
                            "n6me2lys" ,"xlnk-n6lys-1gly",
                            "n6me3+lys", "sgergercys", "farnres",
                            "se(s)met", "gpires"]
        if participant_role == "enzyme target":
            n_residues = 0
            n_expl_resulting = 0
            for accepted_ft in accepted_features:
                if accepted_ft["type"] in residue_features:
                    n_residues += 1
                    try:
                        ftr = accepted_ft["role"]
                        if ftr == "resulting_ptm":
                            n_expl_resulting += 1
                    except:
                        pass
        # Loop on all features.
        ft_list = []
        for accepted_ft in accepted_features:
            # Regions. Regions are always a prerequisite,
            # they cannot be a resulting feature.
            if "bind" in feature["type"]:
                ft_name = feature["name"]
                ft_start = self._range_to_int(feature["start"])
                ft_end = self._range_to_int(feature["end"])
                interpro = feature["interpro"]
                # I try to assign InterPro regions in a very simplistic way.
                if interpro != None:
                   for dom in gene["domains"]:
                       if interpro in dom.ipr_ids:
                           ft_name = dom.short_names[0]
                           break
                else:
                   if ft_start != "undetermined" and ft_end != "undetermined":
                       for dom in gene["domains"]:
                           overlap_ratio = self._calc_overlap(
                               [ft_start, ft_end], [dom.start, dom.end])
                           if overlap_ratio > 0.9:
                               interpro = dom.ipr_ids[0]
                               ft_name = dom.short_names[0]
                ft_dict = {"entity":Region(
                               name=ft_name,
                               interproid=interpro),
                           "role":"prerequisite",
                           "kind":"region"}
                if ft_start != "undetermined":
                    ft_dict["entity"].start = ft_start
                if ft_end != "undetermined":
                    ft_dict["entity"].end = ft_end
                ft_list.append(ft_dict)
            # Residues.
            # If there is no location, just give a state.
            # List of feature types accounted for:
            # phosres, phosphorylated residue               (S,T,Y)
            # optyr, O4'-phospho-L-tyrosine                 (Y)
            # opser, O-phospho-L-serine                     (S)
            # opthr, O-phospho-L-threonine                  (T)
            # n6me2lys, N6,N6-dimethyl-L-lysine             (K) 
            # xlnk-n6lys-1gly, N6-glycyl-L-lysine           (K)
            # n6me3+lys, N6,N6,N6-trimethyl-L-lysine        (K)
            # sgergercys, S-geranylgeranyl-L-cysteine       (C)
            # farnres, farnesylated residue                 (C)
            # se(s)met, L-selenomethionine                  (M)
            # gpires, glycosylphosphatidylinositolated res  (A,N,D,C,G,S)
            # -- gpi residues taken from Essentials of Glycobiology,
            #    chapter 12, Glycosylphosphatidylinositol Anchors,
            #    by Michael A.J. Ferguson. --
            if feature["type"] in residue_features:
                if feature["type"] == "phosres":
                    amino_acid = set(["S", "T", "Y"])
                    state_key = "phosphorylation"
                if feature["type"] == "optyr":
                    amino_acid = "Y"
                    state_key = "phosphorylation"
                if feature["type"] == "opser":
                    amino_acid = "S"
                    state_key = "phosphorylation"
                if feature["type"] == "opthr":
                    amino_acid = "T"
                    state_key = "phosphorylation"
                if feature["type"] == "n6me2lys":
                    amino_acid = "K"
                    state_key = "dimethylation"
                if feature["type"] == "xlnk-n6lys-1gly":
                    amino_acid = "K"
                    state_key = "glycylation"
                if feature["type"] == "n6me3+lys":
                    amino_acid = "K"
                    state_key = "trimethylation"
                if feature["type"] == "sgergercys":
                    amino_acid = "C"
                    state_key = "geranylgeranylation"
                if feature["type"] == "farnres":
                    amino_acid = "C"
                    state_key = "farnesylation"
                if feature["type"] == "se(s)met":
                    amino_acid = "M"
                    state_key = "selenomethionine"
                if feature["type"] == "gpires":
                    amino_acid = set(["A", "N", "D", "C", "G", "S"])
                    state_key = "GPI"
                state_obj = State(state_key, True)
                # Determine feature role (prerequisite or resulting).
                # Features on a enzyme are always prerequisites.
                # On an enzyme target, if there is at least one explicit
                # resulting-ptm, any feature that has no explicit role is
                # considered prerequisite. If there is no explicit
                # resulting-ptm, I suppose that every feature that matches
                # with interaction type (i.e. phosphorylated residue in a
                # phosphorylation reaction) should be resulting, and any
                # feature that does not match should be a prerequisite.
                try:
                    ft_role = feature["role"]
                except:
                    if participant_role == "enzyme":
                        ft_role = "prerequisite"
                    if participant_role == "enzyme target":
                        if n_expl_resulting > 0:
                            ft_role = "prerequisite"
                        else:
                            if state_key == rxn_type:
                                ft_role = "resulting"
                            else:
                                ft_role = "prerequisite"
                    if participant_role == "unspecified role":
                        if state_key == rxn_type:
                            ft_role = "resulting"
                        else:
                            ft_role = "prerequisite"
                # Determine location and write feature output.
                ft_start = feature["start"]
                ft_end = feature["end"]
                if ft_start != "undetermined" and ft_start == ft_end:
                    residue_location = int(feature["start"])
                    ft_dict = {"entity":Residue(
                                   aa=amino_acid,
                                   loc=residue_location,
                                   state=state_obj),
                               "role":ft_role,
                               "kind":"residue"}
                else:
                    ft_dict = {"entity":state_obj,
                               "role":ft_role,
                               "kind":"state"}
                ft_list.append(ft_dict)      
        return ft_list

    def _find_prerequisites(self, participant):
        prerequisite_residues = []
        prerequisite_states = []
        for ft in participant["features"]:
            if ft["kind"] == "residue" and ft["role"] == "prerequisite":
                prerequisite_residues.append(ft["entity"])
            if ft["kind"] == "state" and ft["role"] == "prerequisite":
                prerequisite_states.append(ft["entity"])
        return [prerequisite_residues, prerequisite_states]

    def _calc_overlap(self, f1, f2):
        """    
        Simple overlap ratio: number of overlapping residues / 
                              total span of the two features

                    -----------               -----------
        overlap     |||||||||        span  ||||||||||||||
                 ------------              ------------
        """
        starts = [ f1[0], f2[0] ]
        ends = [ f1[1], f2[1] ]
        ratio = 0
        # First, check if there is an overlap at all.
        highstart = max(starts)
        lowend = min(ends)
        if highstart < lowend:
            # Compute number of overlapping residues
            overlap = lowend - highstart
            # Compute the total span
            lowstart = min(starts)
            highend = max(ends)
            span = highend - lowstart
            # Compute ratio
            ratio = float(overlap) / float(span)
        return ratio

    def _range_to_int(self, value):
        """
        Convert start and end values to integers so that KAMI can read them.
        """
        # An undetermined position remains string "undetermined" and will be
        # ignored.
        if value == "undetermined":
            position = "undetermined"
        elif value == "n-term":
            position = 1
        elif value == "c-term":
            position = 99999
        else:
            position = int(value)
        return position

# ===================== End of KAMI interactions section =====================

# //////////////////// Biological grounding section //////////////////////////

    def identify_protein(self, participant):
        """
        Try to identify participant using the Anatomizer and InterPro data.
        """
        anatomy = anatomizer.GeneAnatomy(
            participant["id"],
            merge_overlap=0.8,
            nest_overlap=0.8,
            nest_level=0,
            offline=True
        )
        kami_gene_dict = {"uniprot_id":anatomy.uniprot_id,
                          "uniprot_ac":anatomy.uniprot_ac,
                          "hgnc_symbol":anatomy.hgnc_symbol,
                          "hgnc_id":anatomy.hgnc_id,
                          "synonyms":anatomy.synonyms,
                          "domains":anatomy.domains}
        return kami_gene_dict

# //////////////////// End of biological grounding section ///////////////////

# ~~~~~~~~~~~~~~~~~~~~~ Statistics section ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def compute_statistics(self):
        """
        Compute some statistics on the raw interactions.
        """
        # Compute data.
        n_raw = len(self.raw_interactions)
        n_types = {}
        n_tot = [0, 0, 0, 0]
        for interaction in self.raw_interactions:
            inter_type = interaction["type"]
            part_bin = self._count_participants(interaction)
            if part_bin > 2:
                part_bin = 3
            if inter_type in n_types.keys():
                n_types[inter_type][0] = n_types[inter_type][0] + 1
            else:
                n_types[inter_type] = [1, 0, 0, 0]
            n_types[inter_type][part_bin] = n_types[inter_type][part_bin] + 1
            n_tot[0] = n_tot[0] + 1
            n_tot[part_bin] = n_tot[part_bin] + 1
        # Write data to string.
        stat_str = ""
        stat_str += "\nStatistics on imported IntAct interactions.\n"
        stat_str += ("*Percentages are over the total number of interactions"
                     " ({:d}).\n\n".format(n_raw))
        stat_str += ("Interaction Type                             All     "
                     "           1 participant       2 participants      "
                     ">2 participants\n\n")
        for key in n_types.keys():
            stat_str += "{:35}".format(key)
            for i in range(4):
                n_inters = n_types[key][i]
                percent = n_inters/float(n_tot[0])*100
                stat_str += "  {:8d}  ({:6.3f}%)".format(n_inters, percent)
            stat_str += "\n"
        # Write totals.
        stat_str += "{:35}".format("Total")
        stat_str += "  {:8d} ({:6.3f}%)".format(n_tot[0],
            n_tot[0]/float(n_raw)*100)
        for i in range(1, 4):
            stat_str += "  {:8d}  ({:6.3f}%)".format(n_tot[i],
                n_tot[i]/float(n_tot[0])*100)        
        self.statistics = stat_str
        return self.statistics

    def _count_participants(self, single_interaction):
        """Count the number of participants in a given interaction."""
        n_participants = len(single_interaction["participants"])
        return n_participants

# ~~~~~~~~~~~~~~~~~~~~~ End of statistics section ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def generate_interactions(self):
        """Generate interactions from loaded IntAct file."""
        interactions = []
        for gen_react in self.general_reactions:
            interactions += self.get_general_reaction(gen_react)
        for bnd in self.bindings:
            interactions += self.get_binding(bnd)
        return interactions

    def import_model(self, file_list):
        """Collect the data from IntAct and generate KAMI interactions."""
        self.read_interactions(file_list)
        self.prefilter_interactions()
        interactions = self.generate_interactions()
        return interactions

