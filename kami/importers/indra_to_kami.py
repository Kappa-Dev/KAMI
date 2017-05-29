"""Importers from INDRA."""
import copy
import warnings

import indra.statements

from kami.data_structures.entities import (Agent, Residue, State,
                                           NuggetAnnotation,
                                           PhysicalAgent)
from kami.exceptions import IndraImportError, IndraImportWarning
from kami.data_structures.interactions import (Modification,
                                               AutoModification,
                                               TransModification,
                                               BinaryBinding,
                                               AnonymousModification,
                                               Complex)
from kami.utils.xrefs import (uniprot_from_xrefs,
                              names_from_uniprot,
                              uniprot_from_names
                              )


class IndraImporter(object):
    """Class implementing import from INDRA."""

    def __init__(self):
        """Initialize INDRA importer object."""
        pass

    def _agent_to_kami(self, agent):

        uniprotid = None
        names = None
        xrefs = None
        location = None

        if agent.db_refs:
            new_db_refs = dict()
            for db, agent_id in agent.db_refs.items():
                new_db_refs[db.lower()] = agent_id
            if "uniprot" in new_db_refs.keys():
                uniprotid = new_db_refs["uniprot"]
                del new_db_refs["uniprot"]
            xrefs = new_db_refs

        # no UniProt id in db_refs of indra Agent
        if uniprotid is None:
            uniprotid = uniprot_from_xrefs(xrefs)

        if agent.name:
            names = [agent.name]
            if uniprotid is None:
                uniprotid = uniprot_from_names(uniprotid)
        else:
            if uniprotid is not None:
                names = names_from_uniprot(uniprotid)
            # here resolve name using xrefs
            pass

        if agent.location:
            location = agent.location

        kami_agent = Agent(
            uniprotid,
            names,
            xrefs,
            location
        )
        return kami_agent

    def _residue_to_kami(self, mod):
        state = State(mod.mod_type, mod.is_modified)
        res = Residue(mod.residue, mod.position, state=state)
        return res

    def _state_to_kami(self, mod):
        state = State(mod.mod_type, mod.is_modified)
        return state

    def _activity_to_kami(self, act):
        state = State(act.activity_type, act.is_active)
        return state

    def _mutation_to_kami(self, mut):
        mut_residue = Residue(mut.residue_to, mut.position)
        return mut_residue

    def _physical_agent_to_kami(self, agent):
        kami_agent = self._agent_to_kami(agent)

        residues = []
        states = []
        bounds = []

        for m in agent.mods:
            if m.residue:
                residues.append(self._residue_to_kami(m))
            else:
                states.append(self._state_to_kami(m))

        if agent.activity:
            states.append(self._activity_to_kami(agent.activity))

        for mut in agent.mutations:
            residues.append(self._mutation_to_kami(mut))

        for bnd in agent.bound_conditions:
            if bnd.is_bound:
                bounds.append(self._physical_agent_to_kami(bnd.agent))

        physical_agent = PhysicalAgent(
            kami_agent,
            residues=residues,
            states=states,
            bounds=bounds
        )
        return physical_agent

    def _modification_to_state(self, statement):
        state_name = None
        state_value = None
        if isinstance(statement, indra.statements.Phosphorylation):
            state_name = "phosphorylation"
            state_value = True
        elif isinstance(statement, indra.statements.Dephosphorylation):
            state_name = "phosphorylation"
            state_value = False
        elif isinstance(statement, indra.statements.Ubiquitination):
            state_name = "ubiquitination"
            state_value = True
        elif isinstance(statement, indra.statements.Deubiquitination):
            state_name = "ubiquitination"
            state_value = False
        elif isinstance(statement, indra.statements.Sumoylation):
            state_name = "sumoylation"
            state_value = True
        elif isinstance(statement, indra.statements.Desumoylation):
            state_name = "sumoylation"
            state_value = False
        elif isinstance(statement, indra.statements.Hydroxylation):
            state_name = "hydroxylation"
            state_value = True
        elif isinstance(statement, indra.statements.Dehydroxylation):
            state_name = "hydroxylation"
            state_value = False
        elif isinstance(statement, indra.statements.Acetylation):
            state_name = "acetylation"
            state_value = True
        elif isinstance(statement, indra.statements.Deacetylation):
            state_name = "acetylation"
            state_value = False
        elif isinstance(statement, indra.statements.Glycosylation):
            state_name = "glycosylation"
            state_value = True
        elif isinstance(statement, indra.statements.Deglycosylation):
            state_name = "glycosylation"
            state_value = False
        elif isinstance(statement, indra.statements.Farnesylation):
            state_name = "farnesylation"
            state_value = True
        elif isinstance(statement, indra.statements.Defarnesylation):
            state_name = "farnesylation"
            state_value = False
        elif isinstance(statement, indra.statements.Geranylgeranylation):
            state_name = "geranylgeranylation"
            state_value = True
        elif isinstance(statement, indra.statements.Degeranylgeranylation):
            state_name = "geranylgeranylation"
            state_value = False
        elif isinstance(statement, indra.statements.Palmitoylation):
            state_name = "palmitoylation"
            state_value = True
        elif isinstance(statement, indra.statements.Depalmitoylation):
            state_name = "palmitoylation"
            state_value = False
        elif isinstance(statement, indra.statements.Myristoylation):
            state_name = "myristoylation"
            state_value = True
        elif isinstance(statement, indra.statements.Demyristoylation):
            state_name = "myristoylation"
            state_value = False
        elif isinstance(statement, indra.statements.Ribosylation):
            state_name = "ribosylation"
            state_value = True
        elif isinstance(statement, indra.statements.Deribosylation):
            state_name = "ribosylation"
            state_value = False
        elif isinstance(statement, indra.statements.Methylation):
            state_name = "methylation"
            state_value = True
        elif isinstance(statement, indra.statements.Demethylation):
            state_name = "methylation"
            state_value = False
        else:
            raise IndraImportError(
                "Unknown type of modification: %s!" % str(statement)
            )
        return (state_name, state_value)

    def _annotation_to_kami(self, statement):
        statement.supports
        statement.supported_by
        # statement.belief
        statement.evidence

        text = "Supports: %s, supported by: %s, evidence: %s" %\
            (
                statement.supports,
                statement.supported_by,
                statement.evidence
            )

        annotation = NuggetAnnotation(text=text)

        return annotation

    def _handle_modification(self, statement):
        """Handle INDRA modification classes."""
        # convert indra agents to kami agents

        enz_physical_agent = self._physical_agent_to_kami(statement.enz)
        sub_physical_agent = self._physical_agent_to_kami(statement.sub)

        # extract modification type and value
        try:
            state, value = self._modification_to_state(statement)
        except IndraImportError as e:
            warnings.warn(
                "Statement import failed, reason %s: " % e, IndraImportWarning
            )
            return

        state_obj = State(state, not value)
        mod_residue = None
        if statement.residue:
            if statement.position:
                mod_residue = Residue(statement.residue, statement.position, state_obj)
            else:
                mod_residue = Residue(statement.residue, state=state_obj)

        # Extract annotation from indra statement
        annotation = self._annotation_to_kami(statement)

        if mod_residue:
            nugget_gen = Modification(
                enz_physical_agent, sub_physical_agent,
                mod_residue, value, annotation=annotation,
                direct=True
            )
        else:
            nugget_gen = Modification(
                enz_physical_agent, sub_physical_agent,
                state_obj, value, annotation=annotation,
                direct=True
            )

        return nugget_gen

    def _handle_self_modification(self, statement):
        """Handle INDRA self-modification classes."""
        if isinstance(statement, indra.statements.Autophosphorylation):
            enz_physical_agent = self._physical_agent_to_kami(statement.enz)

            state = "phosphorylation"
            value = True

            state_obj = State(state, not value)
            mod_residue = None
            if statement.residue:
                if statement.position:
                    mod_residue = Residue(statement.residue, statement.position, state_obj)
                else:
                    mod_residue = Residue(statement.residue, state=state_obj)

            # Extract annotation from indra statement
            annotation = self._annotation_to_kami(statement)

            if mod_residue:
                nugget_gen = AutoModification(
                    enz_physical_agent, mod_residue, value, annotation=annotation,
                    direct=True
                )
            else:
                nugget_gen = AutoModification(
                    enz_physical_agent, state_obj, value, annotation=annotation,
                    direct=True
                )

            return nugget_gen
        elif isinstance(statement, indra.statements.Transphosphorylation):
            no_bound_enzyme = copy.deepcopy(statement.enz)
            no_bound_enzyme.bound_conditions = None
            enzyme_agent = self._physical_agent_to_kami(no_bound_enzyme)
            substrate_agent = self._physical_agent_to_kami(
                statement.enz.bound_conditions[0]
            )

            mod_state = State("phosphorylation", False)

            mod_residue = None
            if statement.residue:
                mod_residue = Residue(
                    statement.residue,
                    position=statement.position,
                    state=mod_state
                )
            value = True
            annotation = self._annotation_to_kami(statement)

            if mod_residue:
                nugget_gen = TransModification(
                    enzyme_agent, substrate_agent, mod_state, value,
                    annotation=annotation, direct=True
                )
            else:
                nugget_gen = TransModification(
                    enzyme_agent, substrate_agent, mod_residue, value,
                    annotation=annotation, direct=True
                )
            return nugget_gen
        else:
            raise IndraImportError(
                "Unknown type of self-modification: '%s'!" % str(statement)
            )

    def _handle_complex(self, statement):
        """Handle INDRA complex classes."""
        physical_agents = []
        for member in statement.members:
            physical_agents.append(self._physical_agent_to_kami(member))

        annotation = self._annotation_to_kami(statement)
        nugget_gen = Complex(physical_agents, annotation=annotation)

        return nugget_gen

    def _handle_regulate_activity(self, statement):

        if isinstance(statement, indra.statements.Activation):
            mod_value = True
        elif isinstance(statement, indra.statements.Inhibition):
            mod_value = False
        else:
            raise IndraImportError(
                "Unknown type of activity regulations: %s!" % str(statement)
            )

        enz_physical_agent = self._physical_agent_to_kami(statement.subj)
        sub_physical_agent = self._physical_agent_to_kami(statement.obj)

        # extract modification type and value
        state_name = statement.obj_activity

        state_obj = State(state_name, False)

        # Extract annotation from indra statement
        annotation = self._annotation_to_kami(statement)

        nugget_gen = Modification(
            enz_physical_agent, sub_physical_agent,
            state_obj, mod_value, annotation=annotation,
            direct=False
        )

        return nugget_gen

    def _handle_active_form(self, statement):
        """Handle INDRA active form classes."""
        agent = self._physical_agent_to_kami(statement.agent)
        mod_state = State(statement.activity, not statement.is_active)
        mod_value = statement.is_active

        annotation = self._annotation_to_kami(statement)

        nugget_gen = AnonymousModification(
            agent, mod_state, mod_value,
            annotation=annotation, direct=True
        )
        return nugget_gen

    def process_statement(self, statement):
        """Process individual INDRA statement."""
        nugget = None

        if isinstance(statement, indra.statements.Modification):
            nugget = self._handle_modification(statement)
        elif isinstance(statement, indra.statements.SelfModification):
            nugget = self._handle_self_modification(statement)
        elif isinstance(statement, indra.statements.Complex):
            nugget = self._handle_complex(statement)
        elif isinstance(statement, indra.statements.RegulateActivity):
            nugget = self._handle_regulate_activity(statement)
        elif isinstance(statement, indra.statements.ActiveForm):
            nugget = self._handle_active_form(statement)
        else:
            raise IndraImportError(
                "Import is not implemented for the given type of "
                "INDRA statement: '%s'" % str(statement)
            )
        return nugget

    def from_statements(self, statement_list):
        """Read out a list of INDRA statements into a list of interactions."""
        interactions = []
        for s in statement_list:
            try:
                nugget = self.process_statement(s)
                if nugget:
                    interactions.append(nugget)
            except IndraImportError as e:
                warnings.warn(
                    "Statement processing failed, reason: %s" %
                    str(e),
                    IndraImportWarning
                )
        return interactions
