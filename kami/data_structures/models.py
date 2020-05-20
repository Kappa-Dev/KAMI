"""Collection of data structures for instantiated KAMI models."""
import copy
import datetime
import json
import os

from regraph import (Rule, NXGraph, NXHierarchy, Neo4jHierarchy,
                     keys_by_value)
from regraph.category_utils import compose
from regraph.audit import VersionedHierarchy
from regraph.utils import relation_to_json, attrs_to_json

from kami.aggregation.identifiers import EntityIdentifier
from kami.data_structures.definitions import Definition
from kami.data_structures.annotations import (ModelAnnotation, CorpusAnnotation,
                                              ContextAnnotation)
from kami.resources import default_components
from kami.utils.generic import (nodes_of_type, _init_from_data)


from kami.exceptions import KamiHierarchyError, KamiException


def _empty_aa_found(identifier, node):
    """Test if an empty aa is found."""
    protoform = identifier.get_protoform_of(node)
    residues = identifier.get_attached_residues(
        protoform)
    deattach = False
    for residue in residues:
        residue_attrs = identifier.graph.get_node(residue)
        if "aa" not in residue_attrs or\
                len(residue_attrs["aa"]) == 0:
            test = list(residue_attrs["test"])[0]
            if test is True:
                deattach = True
                break
    return deattach


class KamiContext(object):
    """Class for KAMI contexts."""

    def __init__(self, seed_protoforms, definitions, annotation=None):
        """Initialize KAMI context."""
        self.seed_protoforms = seed_protoforms
        self.definitions = definitions
        if annotation is None:
            annotation = ContextAnnotation()
        self.annotation = annotation

    def to_json(self):
        """Generate JSON repr of the context."""
        definitions = []
        for d in self.definitions:
            definitions.append(d.to_json())
        json_data = {
            "seed_protoforms": self.seed_protoforms,
            "definitions": definitions,
            "annotation": self.annotation.to_json()
        }
        return json_data

    @classmethod
    def from_json(cls, json_data):
        """Create a context from json."""
        definitions = []
        for d in json_data["definitions"]:
            definitions.append(Definition.from_json(d))
        annotation = None
        if "annotation" in json_data:
            annotation = ContextAnnotation.from_json(json_data["annotation"])
        return cls(
            seed_protoforms=json_data["seed_protoforms"],
            definitions=definitions,
            annotation=annotation)


class NewKamiModel(object):
    """Class for KAMI contextualized models."""

    def __init__(self, model_id, corpus, context, annotation=None,
                 creation_time=None, last_modified=None, default_bnd_rate=None,
                 default_brk_rate=None, default_mod_rate=None,
                 generate_instantiation_rules=False):
        """Initialize KAMI model."""
        self.corpus = corpus
        self.context = context
        self.default_bnd_rate = default_bnd_rate
        self.default_brk_rate = default_brk_rate
        self.default_mod_rate = default_mod_rate
        if creation_time is None:
            creation_time = str(datetime.datetime.now())
        self.creation_time = creation_time
        if annotation is None:
            annotation = ModelAnnotation()
        self.annotation = annotation
        if last_modified is None:
            last_modified = self.creation_time
        self.last_modified = last_modified
        self._instantiation_rules = None
        if generate_instantiation_rules:
            self.generate_instantiation_rules()

    def to_json(self):
        """Generate JSON repr of the context."""
        definitions = []
        for d in self.definitions:
            definitions.append(d.to_json())
        json_data = {
            "seed_protoforms": self.seed_protoforms,
            "definitions": definitions,
            "annotation": self.annotation.to_json()
        }
        return json_data

    @classmethod
    def from_json(cls, model_id, corpus, json_data,
                  generate_instantiation_rules=False):
        """Create a model from json."""
        context = None
        if "context" in json_data:
            context = KamiContext.from_json(json_data["context"])
        annotation = None
        if "annotation" in json_data:
            annotation = ModelAnnotation.from_json(json_data["annotation"])
        creation_time = None
        last_modified = None
        default_bnd_rate = None
        default_brk_rate = None
        default_mod_rate = None
        if "default_bnd_rate" in json_data.keys():
            default_bnd_rate = json_data["default_bnd_rate"]
        if "default_brk_rate" in json_data.keys():
            default_brk_rate = json_data["default_brk_rate"]
        if "default_mod_rate" in json_data.keys():
            default_mod_rate = json_data["default_mod_rate"]
        if "creation_time" in json_data.keys():
            creation_time = json_data["creation_time"]
        if "last_modified" in json_data.keys():
            last_modified = json_data["last_modified"]
        return cls(
            model_id, corpus=corpus, context=context,
            annotation=annotation,
            creation_time=creation_time,
            last_modified=last_modified,
            default_bnd_rate=default_bnd_rate,
            default_brk_rate=default_brk_rate,
            default_mod_rate=default_mod_rate,
            generate_instantiation_rules=generate_instantiation_rules)

    def generate_instantiation_rules(self):
        """Generate instantiation rule hierarchy."""
        self._instantiation_rules = []
        for d in self.context.definitions:
            self._instantiation_rules.append(
                d.generate_rule(
                    self.corpus.action_graph,
                    self.corpus.get_action_graph_typing()))

    def _generate_instantiation_rules_from_refs(self, json_context):
        """Generate instantiation rules from node references."""
        self._instantiation_rules = []
        for definition in json_context["definitions"]:
            protoform_up = definition["protoform"]
            protoform_node_id = self.corpus.get_protoform_by_uniprot(
                protoform_up)
            protoform_subcomponents = self.corpus.subcomponent_nodes(
                protoform_node_id)
            lhs = NXGraph.generate_subgraph(
                self.corpus.action_graph, nodes=protoform_subcomponents)
            instance = {
                c: c for c in protoform_subcomponents
            }
            p = NXGraph()
            rhs = NXGraph()
            p_lhs = dict()
            for i, (name, product_data) in enumerate(
                    definition["products"].items()):
                all_removed_components = set(
                    product_data["removed_components"]["regions"] +
                    product_data["removed_components"]["sites"] +
                    product_data["removed_components"]["residues"] +
                    product_data["removed_components"]["states"]
                )
                # find subcomponents of all removed nodes
                visited = set()
                subcomponents = set()
                for n in all_removed_components:
                    if n not in visited:
                        n_subcomponents = self.corpus.subcomponent_nodes(n)
                        visited.add(n)
                        subcomponents.update(n_subcomponents)
                all_removed_components.update(subcomponents)

                # add nodes and edges to P
                for n, attrs in lhs.nodes(data=True):
                    if n not in all_removed_components:
                        new_node_id = "{}_{}".format(n, i + 1)
                        p.add_node(new_node_id, attrs)
                        rhs.add_node(new_node_id, attrs)
                        p_lhs[new_node_id] = n
                        if n == protoform_node_id:
                            rhs.add_node_attrs(new_node_id, {
                                "variant_name": name,
                                "variant_desc": product_data["desc"],
                                "wild_type": product_data["wild_type"]
                            })
                        elif n in product_data["residues"]:
                            aa = product_data["residues"][n]
                            p.set_node_attrs(new_node_id, {"aa": aa})
                            rhs.set_node_attrs(new_node_id, {"aa": aa})

                for s, t, attrs in lhs.edges(data=True):
                    new_s_name = "{}_{}".format(s, i + 1)
                    new_t_name = "{}_{}".format(t, i + 1)
                    if new_s_name in p.nodes() and new_t_name in p.nodes():
                        p.add_edge(new_s_name, new_t_name, attrs)
                        rhs.add_edge(new_s_name, new_t_name, attrs)

            self._instantiation_rules.append(
                (Rule(p=p, lhs=lhs, rhs=rhs, p_lhs=p_lhs), instance))

    def action_graph_instantiation_rule(self):
        """Create a composed rule performing instantiation."""
        if not self._instantiation_rules:
            self.generate_instantiation_rules()

        global_instance = {}
        global_lhs = NXGraph()
        global_p = NXGraph()
        global_rhs = NXGraph()
        p_lhs = {}
        p_rhs = {}
        for rule, instance in self._instantiation_rules:
            global_instance.update(instance)
            global_lhs.add_nodes_from(rule.lhs.nodes(data=True))
            global_lhs.add_edges_from(rule.lhs.edges(data=True))
            global_p.add_nodes_from(rule.p.nodes(data=True))
            global_p.add_edges_from(rule.p.edges(data=True))
            global_rhs.add_nodes_from(rule.rhs.nodes(data=True))
            global_rhs.add_edges_from(rule.rhs.edges(data=True))
            p_lhs.update(rule.p_lhs)
            p_rhs.update(rule.p_rhs)
        return (
            Rule(
                p=global_p, lhs=global_lhs, rhs=global_rhs,
                p_lhs=p_lhs, p_rhs=p_rhs),
            global_instance
        )

    def _nugget_clean_up(self, nugget_id, instantiation_rule,
                         instantiation_instance):

        nugget_typing = self.corpus._hierarchy.get_typing(
            nugget_id, self.corpus._action_graph_id)
        ag_typing = self.corpus.get_action_graph_typing()
        n_meta_typing = {
            k: ag_typing[v] for k, v in nugget_typing.items()
        }
        nugget_graph = self.corpus.get_nugget(nugget_id)

        p_identifier = EntityIdentifier(
            instantiation_rule.p,
            compose(
                compose(instantiation_rule.p_lhs, instantiation_instance),
                n_meta_typing),
            immediate=False)
        n = instantiation_rule.p.nodes()
        t = compose(
            compose(instantiation_rule.p_lhs, instantiation_instance),
            n_meta_typing
        )

        already_detached = []

        new_lhs = NXGraph.copy(instantiation_rule.lhs)
        new_p = NXGraph.copy(instantiation_rule.p)
        new_p_lhs = copy.deepcopy(instantiation_rule.p_lhs)

        def _detach_neighbour(p, action, predecessor=True, partner_to_ignore=None):
            if p != partner_to_ignore:
                # get nodes from the instantiation p
                if p in instantiation_instance.values():
                    inst_p = keys_by_value(
                        instantiation_rule.p_lhs,
                        keys_by_value(instantiation_instance, p)[0])
                    if action not in new_lhs.nodes():
                        new_lhs.add_node(action)
                        instantiation_instance[action] = action
                    if action not in new_p.nodes():
                        new_p.add_node(action)
                        new_p_lhs[action] = action
                    for ip in inst_p:
                        deattach = _empty_aa_found(p_identifier, ip)
                        if not deattach:
                            if predecessor:
                                lhs_edge = (instantiation_rule.p_lhs[ip], action)
                                p_edge = (ip, action)
                            else:
                                lhs_edge = (action, instantiation_rule.p_lhs[ip])
                                p_edge = (action, ip)
                            if lhs_edge not in new_lhs.edges():
                                s, t = lhs_edge
                                new_lhs.add_edge(s, t)
                            if p_edge not in new_p.edges():
                                s, t = p_edge
                                new_p.add_edge(s, t)
                            # Find other bonds
                            nugget_identifier = EntityIdentifier(
                                nugget_graph,
                                n_meta_typing,
                                immediate=False)
                            other_bnds = [
                                bnd
                                for bnd in nugget_identifier.get_attached_bnd(p)
                                if bnd != bnd_action
                            ]
                            for bnd in other_bnds:
                                if bnd not in already_detached:
                                    already_detached.append(bnd)
                                    _detach_edge_to_bnds(bnd, p)
                        else:
                            if predecessor:
                                lhs_edge = (instantiation_rule.p_lhs[ip], action)
                            else:
                                lhs_edge = (action, instantiation_rule.p_lhs[ip])
                            if lhs_edge not in new_lhs.edges():
                                s, t = lhs_edge
                                new_lhs.add_edge(s, t)

        def _detach_edges_incident_to_mod(mod_action):
            preds = nugget_graph.predecessors(mod_action)
            sucs = nugget_graph.predecessors(mod_action)
            for p in preds:
                _detach_neighbour(p, mod_action, predecessor=True)
            for s in sucs:
                _detach_neighbour(s, mod_action, predecessor=False)

        def _detach_edge_to_bnds(bnd_action, partner_to_ignore=None):
            preds = nugget_graph.predecessors(bnd_action)
            for p in preds:
                _detach_neighbour(
                    p, bnd_action, partner_to_ignore=partner_to_ignore)

        if "mod_template" in self.corpus._hierarchy.adjacent_relations(nugget_id):
            mod_template = self.corpus._hierarchy.get_relation(
                "mod_template", nugget_id)
            action = list(mod_template["mod"])[0]

            # Deattach preds or sucs of action if residue aa is empty
            _detach_edges_incident_to_mod(action)

        elif "bnd_template" in self.corpus._hierarchy.adjacent_relations(nugget_id):
            # Remove edge to a mod/bnd from/to the actor that contains
            # a residue with the empty aa
            bnd_template = self.corpus._hierarchy.get_relation(
                "bnd_template", nugget_id)
            bnd_actions = bnd_template["bnd"]
            # Find a BND node with type == do
            action = None
            for bnd_action in bnd_actions:
                attrs = nugget_graph.get_node(bnd_action)
                if list(attrs["type"])[0] == "do":
                    action = bnd_action
                    break

            # Deattach preds of action if residue aa is empty
            _detach_edge_to_bnds(action)

        # Remove all the graph nodes disconected from
        # the action node
        nodes_to_remove = new_p.nodes_disconnected_from(action)

        # Remove empty residue conditions
        for protoform in p_identifier.get_protoforms():
            residues = p_identifier.get_attached_residues(protoform)
            for res in residues:
                residues_attrs = new_p.get_node(res)
                if "aa" not in residues_attrs or\
                        len(residues_attrs["aa"]) == 0:
                    nodes_to_remove.add(res)

        for n in nodes_to_remove:
            new_p.remove_node(n)
            del new_p_lhs[n]
        return Rule(p=new_p, lhs=new_lhs, p_lhs=new_p_lhs), instantiation_instance

    def nugget_instantiation_rule(self, nugget_id):
        """Generate the instantiation rule for the nugget."""
        # generate instantiation rule for the action graph
        ag_rule, ag_instance = self.action_graph_instantiation_rule()
        # generate instantiation rule for the nugget
        (
            nugget_rule,
            nugget_instance,
            l_g_l,
            p_g_p
        ) = self.corpus._hierarchy._get_backward_propagation_rule(
            self.corpus._action_graph_id, nugget_id,
            ag_rule, ag_instance)
        # apply clean-up transforms
        nugget_rule, nugget_instance = self._nugget_clean_up(
            nugget_id, nugget_rule,
            nugget_instance)
        return nugget_rule, nugget_instance

    def get_instantiated_nugget(self, nugget_id):
        """Generate instantiated nugget object."""
        if self._instantiation_rules is not None:
            # Get a rule and apply it to the copy of the
            # nugget
            pass
        else:
            # Generate instantiation rule for the nugget
            pass

    def get_instantiated_action_graph(self):
        """Generate instantiated action graph object."""
        rule, instance = self.action_graph_instantiation_rule()
        action_graph = NXGraph.copy(self.corpus.action_graph)
        rhs_instance = action_graph.rewrite(rule, instance=instance)

        component_equivalence = {}
        for lhs_node, p_nodes in rule.cloned_nodes().items():
            for p_node in p_nodes:
                component_equivalence[rhs_instance[rule.p_rhs[p_node]]] =\
                    instance[lhs_node]

        return action_graph, component_equivalence

    def instantiated_action_graph_d3_json(self):
        """Generate instantiated action graph JSON."""
        pass

    def empty(self):
        """Test if model is empty."""
        return (len(self.corpus.nuggets()) == 0) and\
               ((self.corpus.action_graph is None) or
                (len(self.corpus.action_graph.nodes()) == 0))

    def proteins(self):
        """Get a list of agent nodes in the action graph."""
        protoforms = nodes_of_type(
            self.corpus.action_graph,
            self.corpus.get_action_graph_typing(), "protoform")
        # TODO: unfold proteins to protoforms
        pass


class KamiModel(object):
    """Class for instantiated KAMI models.

    Attributes
    ----------
    _id : str,
        Identifier of the model
    _backend : str, "networkx" or "neo4j"
    _hierarchy : NXHierarchy or Neo4jHierarchy
        Graph hierarchy object containg the model
    _corpus_id : hashable
        Identifier of the original corpus from which
        the model was instantiated
    _action_graph_id : hashable
        Id of the action graph in the graph hierarchy
    _seed_genes : iterable
        Collection of UniProt AC's of genes used to
        instantiate the model
    _definitions : iterable of kami.data_structure.definitions.Definition
        Collection of definitions used to instantiate the model
    _component_equivalence : dict
        Dictionary containing the equivalence classes of various elements
        of the action graph, i.e. defining whether proteins or their
        components where instantiated from the same structural
        component.

    annotation : kami.data_structures.annotations.CorpusAnnotation
    creation_time : str
    last_modified : str

    """

    nugget_dict_factory = dict

    def __init__(self, model_id, annotation=None,
                 creation_time=None, last_modified=None,
                 corpus_id=None, seed_genes=None, definitions=None,
                 component_equivalence=None, backend="networkx",
                 uri=None, user=None, password=None, driver=None, data=None,
                 default_bnd_rate=None,
                 default_brk_rate=None,
                 default_mod_rate=None):
        """Initialize a KAMI model."""
        self._id = model_id
        self._action_graph_id = self._id + "_action_graph"
        self._corpus_id = corpus_id
        self._backend = backend
        self._seed_genes = seed_genes
        self._definitions = definitions
        self._component_equivalence = component_equivalence
        self.default_bnd_rate = default_bnd_rate
        self.default_brk_rate = default_brk_rate
        self.default_mod_rate = default_mod_rate

        if backend == "networkx":
            self._hierarchy = NXHierarchy()
        elif backend == "neo4j":
            if driver is not None:
                self._hierarchy = Neo4jHierarchy(driver=driver)
            else:
                self._hierarchy = Neo4jHierarchy(uri, user, password)
        self._versioning = VersionedHierarchy(self._hierarchy)
        if creation_time is None:
            creation_time = str(datetime.datetime.now())
        self.creation_time = creation_time
        if annotation is None:
            annotation = CorpusAnnotation()
        self.annotation = annotation
        if last_modified is None:
            last_modified = self.creation_time
        self.last_modified = last_modified

        # Add KAMI-specific invariant components of the hierarchy
        for graph_id, graph, attrs in default_components.MODEL_GRAPHS:
            if graph_id not in self._hierarchy.graphs():
                self._hierarchy.add_empty_graph(graph_id, attrs)
                g = self._hierarchy.get_graph(graph_id)
                g.add_nodes_from(graph["nodes"])
                g.add_edges_from(graph["edges"])

        for s, t, mapping, attrs in default_components.MODEL_TYPING:
            if (s, t) not in self._hierarchy.typings():
                self._hierarchy.add_typing(s, t, mapping, attrs=attrs)
        for rule_id, rule, attrs in default_components.RULES:
            self._hierarchy.add_rule(rule_id, rule, attrs)
        for s, t, (
                lhs_mapping,
                rhs_mapping), attrs in default_components.MODEL_RULE_TYPING:
            self._hierarchy.add_rule_typing(
                s, t, lhs_mapping, rhs_mapping,
                lhs_total=True, rhs_total=True, attrs=attrs)
        for u, v, rel, attrs in default_components.RELATIONS:
            if (u, v) not in self._hierarchy.relations():
                self._hierarchy.add_relation(u, v, rel, attrs)

        _init_from_data(self, data, True)

        self._init_shortcuts()
        return

    def _copy_knowledge_from_corpus(self, corpus):
        """Copy the AG and nuggets from the corpus."""
        if self._backend != "networkx":
            raise KamiHierarchyError(
                "Method '_copy_knowledge_from_corpus' is available only " +
                "for networkx-based corpora, for neo4j corpora refer to " +
                "the 'duplicate_subgraph' methond of Neo4jHierarchy")

        # Copy the action graph
        ag_obj = NXGraph.copy(corpus.action_graph)
        self._hierarchy._update_graph(self._action_graph_id, ag_obj)
        # Update a short-cup
        self.action_graph =\
            self._hierarchy.get_graph(self._action_graph_id)
        self._hierarchy._update_mapping(
            self._action_graph_id,
            "meta_model",
            corpus.get_action_graph_typing())

        # Copy nuggets
        for n in corpus.nuggets():
            # Generate a nugget id
            model_nugget_id = self._id + "_" + n

            adj_relations = set([
                r
                for r in corpus._hierarchy.adjacent_relations(n)
                if r in ["mod_template", "bnd_template"]
            ])

            # Add an empty nugget graph to the model
            self._hierarchy.add_graph(
                model_nugget_id, NXGraph(),
                attrs=corpus._hierarchy.get_graph_attrs(n))
            self._hierarchy.set_graph_attrs(
                model_nugget_id,
                {"model_id": self._id})

            self._hierarchy.add_typing(
                model_nugget_id, self._action_graph_id, dict())

            for r in adj_relations:
                self._hierarchy.add_relation(
                    model_nugget_id, r, {})

            # Update nugget related objects
            nugget_obj = NXGraph.copy(corpus.get_nugget(n))
            self._hierarchy._update_graph(model_nugget_id, nugget_obj)
            self._hierarchy._update_mapping(
                model_nugget_id, self._action_graph_id,
                corpus.get_nugget_typing(n))
            for r in adj_relations:
                self._hierarchy._update_relation(
                    model_nugget_id, r,
                    corpus._hierarchy.get_relation(n, r)
                )

    def _init_shortcuts(self):
        """Initialize kami-specific shortcuts."""
        if self._action_graph_id in self._hierarchy.graphs():
            self.action_graph =\
                self._hierarchy.get_graph(self._action_graph_id)
        else:
            self.action_graph = None

        self.mod_template = self._hierarchy.get_graph(
            "mod_template")
        self.bnd_template = self._hierarchy.get_graph(
            "bnd_template")

    def get_nugget(self, nugget_id):
        """Get a nugget by ID."""
        for node_id in self._hierarchy.graphs():
            if self.is_nugget_graph(node_id):
                return self._hierarchy.get_graph(nugget_id)
        raise KamiException("Nugget '{}' is not found".format(nugget_id))

    def clear(self):
        """Clear data elements of corpus."""
        for n in self.nuggets():
            self._hierarchy.remove_graph(n)
        self._hierarchy.remove_graph(self._action_graph_id)

    def create_empty_action_graph(self):
        """Creat an empty action graph in the hierarchy."""
        if self._action_graph_id not in self._hierarchy.graphs():
            self._hierarchy.add_empty_graph(
                self._action_graph_id,
                {"type": "action_graph",
                 "model_id": self._id}
            )
            self._hierarchy.add_typing(
                self._action_graph_id,
                "meta_model",
                dict()
            )
            self.action_graph = self._hierarchy.get_graph(
                self._action_graph_id)

    def rewrite(self, graph_id, rule, instance=None,
                rhs_typing=None, strict=False,
                message="Model update", update_type="manual"):
        """Overloading of the rewrite method."""
        r_g_prime, _ = self._versioning.rewrite(
            graph_id, rule=rule, instance=instance,
            rhs_typing=rhs_typing, strict=strict,
            message=message, update_type=update_type)
        self._init_shortcuts()
        return r_g_prime

    def find_matching(self, graph_id, pattern,
                      pattern_typing=None, nodes=None):
        """Overloading of the find matching method."""
        return self._hierarchy.find_matching(
            graph_id, pattern,
            pattern_typing, nodes)

    def get_action_graph_typing(self):
        """Get typing of the action graph by meta model."""
        typing = dict()
        if (self._action_graph_id, "meta_model") in self._hierarchy.typings():
            typing =\
                self._hierarchy.get_typing(self._action_graph_id, "meta_model")
        return typing

    def get_action_graph_attrs(self):
        """Get action graph attributes."""
        return self._hierarchy.get_graph_attrs(
            self._action_graph_id)

    def get_proteins_by_uniprot(self, uniprotid):
        """Get a protein by the UniProt AC."""
        res = []
        for protein in self.proteins():
            attrs = self.action_graph.get_node(protein)
            u = list(attrs["uniprotid"])[0]
            if u == uniprotid:
                res.append(protein)
        return res

    def is_nugget_graph(self, node_id):
        """Test if node of the hierarchy is nugget."""
        graph_attrs = self._hierarchy.get_graph_attrs(node_id)
        if "type" in graph_attrs.keys():
            if "model_id" in graph_attrs.keys() and\
               "nugget" in graph_attrs["type"] and\
               self._id in graph_attrs["model_id"]:
                return True
        return False

    def get_nugget_desc(self, nugget_id):
        """Get nugget description string."""
        nugget_attrs = self._hierarchy.get_graph_attrs(nugget_id)
        if 'desc' in nugget_attrs.keys():
            if type(nugget_attrs['desc']) == str:
                nugget_desc = nugget_attrs['desc']
            else:
                nugget_desc = list(nugget_attrs['desc'])[0]
        else:
            nugget_desc = ""
        return nugget_desc

    def get_nugget_type(self, nugget_id):
        """Get type of the nugget specified by id."""
        return list(self._hierarchy.get_graph_attrs(
            nugget_id)["interaction_type"])[0]

    def get_nugget_template_rel(self, nugget_id):
        """Get relation of a nugget to a template."""
        nugget_type = self.get_nugget_type(nugget_id)
        return self._hierarchy.get_relation(
            nugget_id, nugget_type + "_template")

    def get_nugget_typing(self, nugget_id):
        """Get typing of the nugget by the action graph."""
        return self._hierarchy.get_typing(
            nugget_id, self._action_graph_id)

    def nuggets(self):
        """Get a list of nuggets in the hierarchy."""
        nuggets = []
        for node_id in self._hierarchy.predecessors(
                self._action_graph_id):
            if self.is_nugget_graph(node_id):
                nuggets.append(node_id)
        return nuggets

    def empty(self):
        """Test if model is empty."""
        return (len(self.nuggets()) == 0) and\
               ((self.action_graph is None) or
                (len(self.action_graph.nodes()) == 0))

    def proteins(self):
        """Get a list of agent nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "protoform")

    def bindings(self):
        """Get a list of bnd nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "bnd")

    def modifications(self):
        """Get a list of bnd nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "mod")

    @classmethod
    def from_hierarchy(cls, model_id, hierarchy, annotation=None,
                       creation_time=None, last_modified=None,
                       corpus_id=None, seed_genes=None, definitions=None):
        """Initialize KamiCorpus obj from a graph hierarchy."""
        model = cls(model_id, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    corpus_id=corpus_id, seed_genes=seed_genes,
                    definitions=definitions)
        model._hierarchy = hierarchy
        model._init_shortcuts()
        return model

    @classmethod
    def from_json(cls, model_id, json_data, annotation=None,
                  creation_time=None, last_modified=None,
                  corpus_id=None, seed_genes=None, definitions=None,
                  component_equivalence=None, backend="networkx",
                  uri=None, user=None, password=None, driver=None):
        """Create hierarchy from json representation."""
        model = cls(model_id, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    corpus_id=corpus_id, seed_genes=seed_genes,
                    definitions=definitions,
                    component_equivalence=component_equivalence,
                    backend=backend,
                    uri=uri, user=user, password=password, driver=driver,
                    data=json_data)
        return model

    @classmethod
    def load_json(cls, model_id, filename, annotation=None,
                  creation_time=None, last_modified=None,
                  corpus_id=None, seed_genes=None, definitions=None,
                  component_equivalence=None, backend="networkx",
                  uri=None, user=None, password=None, driver=None):
        """Load a KamiCorpus from its json representation."""
        if os.path.isfile(filename):
            with open(filename, "r+") as f:
                json_data = json.loads(f.read())
                model = cls.from_json(
                    model_id, json_data, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    corpus_id=corpus_id, seed_genes=seed_genes,
                    definitions=definitions,
                    component_equivalence=None, backend=backend,
                    uri=uri, user=user, password=password, driver=driver)
            return model
        else:
            raise KamiHierarchyError("File '%s' does not exist!" % filename)

    def export_json(self, filename):
        """Export model to json."""
        with open(filename, 'w') as f:
            j_data = self.to_json()
            json.dump(j_data, f)

    def to_json(self):
        """Return json repr of the corpus."""
        json_data = {}
        json_data["model_id"] = self._id

        json_data["origin"] = {}
        json_data["origin"]["corpus_id"] = self._corpus_id
        json_data["origin"]["seed_genes"] = self._seed_genes
        json_data["origin"]["definitions"] = self._definitions
        json_data["origin"][
            "component_equivalence"] = self._component_equivalence

        json_data["annotation"] = self.annotation.to_json()
        json_data["creation_time"] = self.creation_time
        json_data["last_modified"] = self.last_modified

        json_data["action_graph"] = graph_to_json(self.action_graph)
        json_data["action_graph_typing"] = self.get_action_graph_typing()

        json_data["nuggets"] = []
        for nugget in self.nuggets():
            template = self.get_nugget_type(nugget) + "_template"
            nugget_json = {
                "id": nugget,
                "graph": self.get_nugget(nugget).to_json(),
                "desc": self.get_nugget_desc(nugget),
                "typing": self.get_nugget_typing(nugget),
                "attrs": attrs_to_json(self._hierarchy.get_graph_attrs(nugget)),
                "template_rel": (
                    template,
                    relation_to_json(self.get_nugget_template_rel(nugget))
                ),
            }

            json_data["nuggets"].append(nugget_json)
        return json_data

    def get_gene_data(self, gene_id):
        """."""
        attrs = self.action_graph.get_node(gene_id)
        uniprotid = None
        if "uniprotid" in attrs.keys():
            uniprotid = list(attrs["uniprotid"])[0]
        hgnc_symbol = None
        if "hgnc_symbol" in attrs.keys():
            hgnc_symbol = list(attrs["hgnc_symbol"])[0]
        nuggets = self._hierarchy.graphs_typed_by_node(
            self._action_graph_id, gene_id)
        return (uniprotid, hgnc_symbol, nuggets)

    def get_modification_data(self, mod_id):
        """."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id)

        enzyme_genes = identifier.ancestors_of_type(mod_id, "protoform")
        substrate_genes = identifier.descendants_of_type(mod_id, "protoform")
        nuggets = self._hierarchy.graphs_typed_by_node(
            self._action_graph_id, mod_id)
        return (nuggets, enzyme_genes, substrate_genes)

    def get_binding_data(self, bnd_id):
        """."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id)

        all_genes = identifier.ancestors_of_type(bnd_id, "protoform")
        nuggets = self._hierarchy.graphs_typed_by_node(
            self._action_graph_id, bnd_id)
        return (nuggets, all_genes)

    def get_uniprot(self, gene_id):
        attrs = self.action_graph.get_node(gene_id)
        uniprotid = None
        if "uniprotid" in attrs.keys():
            uniprotid = list(attrs["uniprotid"])[0]
        return uniprotid

    def get_variant_name(self, gene_id):
        """Get the name of protein variant."""
        attrs = self.action_graph.get_node(gene_id)
        if "variant_name" in attrs.keys():
            return list(attrs["variant_name"])[0]

    def get_hgnc_symbol(self, gene_id):
        attrs = self.action_graph.get_node(gene_id)
        hgnc_symbol = None
        if "hgnc_symbol" in attrs.keys():
            hgnc_symbol = list(attrs["hgnc_symbol"])[0]
        return hgnc_symbol

    def set_nugget_desc(self, nugget_id, new_desc):
        """Get nugget description string."""
        self._hierarchy.set_graph_attrs(
            nugget_id, {"desc": new_desc})

    # def merge_ag_nodes(self, nodes):
    #     ag_typing = self.get_action_graph_typing()
    #     if len(set([ag_typing[n] for n in nodes])) == 1:
    #         pattern = NXGraph()
    #         pattern.add_nodes_from(nodes)
    #         r = Rule.from_transform(pattern)
    #         r.inject_merge_nodes(nodes)
    #         self.rewrite(self._action_graph_id, r)
    #     else:
    #         raise KamiException(
    #             "Cannot merge action graph nodes of different type!")

    def get_protein_pairwise_interactions(self):
        """Get pairwise interactions between protoforms."""
        interactions = {}

        def _add_to_interactions(s, t, n, n_type, n_desc):
            if s in interactions:
                if t in interactions[s]:
                    interactions[s][t].add((n, n_type, n_desc))
                else:
                    interactions[s][t] = {(n, n_type, n_desc)}
            else:
                interactions[s] = {
                    t: {(n, n_type, n_desc)}
                }

        for n in self.nuggets():
            ag_typing = self._hierarchy.get_typing(n, self._action_graph_id)
            if self.is_mod_nugget(n):
                enzyme = self.get_enzyme(n)
                substrate = self.get_substrate(n)
                if enzyme is not None and substrate is not None:
                    _add_to_interactions(
                        ag_typing[enzyme], ag_typing[substrate],
                        n, "mod", self.get_nugget_desc(n))
            elif self.is_bnd_nugget(n):
                left = self.get_left_partner(n)
                right = self.get_right_partner(n)
                if left is not None and right is not None:
                    _add_to_interactions(
                        ag_typing[left], ag_typing[right],
                        n, "bnd", self.get_nugget_desc(n))
        return interactions

    def interaction_edges(self):
        interactions = self.get_protein_pairwise_interactions()
        edges = []
        for protoform, (partners, nuggets) in interactions.items():
            for i, partner in enumerate(partners):
                if (protoform, partner) not in edges and (partner, protoform) not in edges:
                    edges.append({"source": protoform, "target": partner})
        return edges

    def remove_nugget(self, nugget_id):
        """Remove nugget from a model."""
        if nugget_id in self.nuggets():
            self._hierarchy.remove_graph(nugget_id)

    def is_mod_nugget(self, nugget_id):
        t = self.get_nugget_type(nugget_id)
        return t == "mod"

    def is_bnd_nugget(self, nugget_id):
        t = self.get_nugget_type(nugget_id)
        return t == "bnd"

    def get_enzyme(self, nugget_id):
        if self.is_mod_nugget(nugget_id):
            enzyme = None
            rel = self._hierarchy.get_relation(
                "mod_template", nugget_id)
            if "enzyme" in rel and len(rel["enzyme"]) > 0:
                enzyme = list(rel["enzyme"])[0]
            return enzyme
        else:
            raise KamiException("Nugget '{}' is not a mod nugget".format(
                nugget_id))

    def get_substrate(self, nugget_id):
        if self.is_mod_nugget(nugget_id):
            substrate = None
            rel = self._hierarchy.get_relation(
                "mod_template", nugget_id)
            try:
                substrate = list(rel["substrate"])[0]
                return substrate
            except:
                print(rel, nugget_id)
        else:
            raise KamiException("Nugget '{}' is not a mod nugget".format(
                nugget_id))

    def get_left_partner(self, nugget_id):
        if self.is_bnd_nugget(nugget_id):
            left = None
            rel = self._hierarchy.get_relation(
                "bnd_template", nugget_id)
            try:
                left = list(rel["left_partner"])[0]
                return left
            except:
                print(rel, nugget_id)
        else:
            raise KamiException("Nugget '{}' is not a bnd nugget".format(
                nugget_id))

    def get_right_partner(self, nugget_id):
        if self.is_bnd_nugget(nugget_id):
            right = None
            rel = self._hierarchy.get_relation(
                "bnd_template", nugget_id)
            try:
                right = list(rel["right_partner"])[0]
                return right
            except:
                print(rel, nugget_id)
        else:
            raise KamiException("Nugget '{}' is not a bnd nugget".format(
                nugget_id))

    def get_gene_pairwise_interactions(self):
        """Get pairwise interactions between genes."""
        interactions = {}

        def _add_to_interactions(s, t, n, n_type, n_desc):
            if s in interactions:
                if t in interactions[s]:
                    interactions[s][t].add((n, n_type, n_desc))
                else:
                    interactions[s][t] = {(n, n_type, n_desc)}
            else:
                interactions[s] = {
                    t: {(n, n_type, n_desc)}
                }

        for n in self.nuggets():
            ag_typing = self._hierarchy.get_typing(n, self._action_graph_id)
            if self.is_mod_nugget(n):
                enzyme = self.get_enzyme(n)
                substrate = self.get_substrate(n)
                if enzyme is not None and substrate is not None:
                    _add_to_interactions(
                        ag_typing[enzyme], ag_typing[substrate],
                        n, "mod", self.get_nugget_desc(n))
            elif self.is_bnd_nugget(n):
                left = self.get_left_partner(n)
                right = self.get_right_partner(n)
                if left is not None and right is not None:
                    _add_to_interactions(
                        ag_typing[left], ag_typing[right],
                        n, "bnd", self.get_nugget_desc(n))
        return interactions

    def get_mechanism_nuggets(self, mechanism_id):
        """."""
        if (self._backend == "neo4j"):
            cypher = (
                "MATCH (n:{} {{id: '{}'}}), (m)-[:typing]->(n)\n".format(
                    self._action_graph_id, mechanism_id) +
                "RETURN collect(labels(m)[0]) as nuggets"
            )
            result = self._hierarchy.execute(cypher)
            return result.single()["nuggets"]
        else:
            raise KamiException(
                "This method is not implemented for NetworkX-based hierarchies!")

    def _clean_up_nuggets(self):
        for nugget in self.nuggets():
            nugget_typing = self._hierarchy.get_typing(
                nugget, self._action_graph_id)
            ag_typing = self.get_action_graph_typing()
            n_meta_typing = {
                k: ag_typing[v] for k, v in nugget_typing.items()
            }
            nugget_graph = self.get_nugget(nugget)

            nugget_identifier = EntityIdentifier(
                nugget_graph,
                n_meta_typing,
                immediate=False)

            def _empty_aa_found(node):
                protoform = nugget_identifier.get_protoform_of(node)
                residues = nugget_identifier.get_attached_residues(
                    protoform)
                deattach = False
                for residue in residues:
                    residue_attrs = nugget_graph.get_node(residue)
                    if "aa" not in residue_attrs or\
                            len(residue_attrs["aa"]) == 0:
                        test = list(residue_attrs["test"])[0]
                        if test is True:
                            deattach = True
                            break
                return deattach

            already_detached = []

            def _detach_edge_to_bnds(bnd_action,
                                     partner_to_ignore=None):
                preds = nugget_graph.predecessors(bnd_action)

                edges_to_remove = set()
                for p in preds:
                    if p != partner_to_ignore:
                        deattach = _empty_aa_found(p)
                        if not deattach:
                            # Find other bonds
                            other_bnds = [
                                bnd
                                for bnd in nugget_identifier.get_attached_bnd(
                                    p)
                                if bnd != bnd_action
                            ]
                            for bnd in other_bnds:
                                if bnd not in already_detached:
                                    already_detached.append(bnd)
                                    _detach_edge_to_bnds(bnd, p)
                        else:
                            edges_to_remove.add((p, bnd_action))
                            # already_detached.append(bnd_action)
                for s, t in edges_to_remove:
                    nugget_graph.remove_edge(s, t)

            if "mod_template" in self._hierarchy.adjacent_relations(nugget):
                pass
            elif "bnd_template" in self._hierarchy.adjacent_relations(nugget):
                # Remove edge to a mod/bnd from/to the actor that contains
                # a residue with the empty aa
                bnd_template = self._hierarchy.get_relation(
                    "bnd_template", nugget)
                bnd_actions = bnd_template["bnd"]
                # Find a BND node with type == do
                do_bnd = None
                for bnd_action in bnd_actions:
                    attrs = nugget_graph.get_node(bnd_action)
                    if list(attrs["type"])[0] == "do":
                        do_bnd = bnd_action
                        break
                # Deattach preds of do_bnd if residue aa is empty
                _detach_edge_to_bnds(do_bnd)
                # Remove all the graph nodes disconected from
                # the action node
                nodes_to_remove = nugget_graph.nodes_disconnected_from(
                    do_bnd)

                for n in nodes_to_remove:
                    pattern = NXGraph()
                    pattern.add_node(n)
                    rule = Rule.from_transform(pattern)
                    rule.inject_remove_node(n)
                    self.rewrite(
                        nugget, rule,
                        message="Nugget clean-up: removed detached components",
                        update_type="auto")

                # Remove empty residue conditions
                for protoform in nugget_identifier.get_protoforms():
                    residues = nugget_identifier.get_attached_residues(protoform)
                    for res in residues:
                        residues_attrs = nugget_graph.get_node(res)
                        if "aa" not in residues_attrs or\
                                len(residues_attrs["aa"]) == 0:
                            pattern = NXGraph()
                            pattern.add_node(res)
                            rule = Rule.from_transform(pattern)
                            rule.inject_remove_node(res)
                            self.rewrite(
                                nugget, rule,
                                message="Nugget clean-up: removed residues with empty aa",
                                update_type="auto")

    def _add_component_equivalence(self, rule, lhs_instance, rhs_instance):
        """Add instantiation rule."""
        if self._component_equivalence is None:
            self._component_equivalence = dict()

        for lhs_node, p_nodes in rule.cloned_nodes().items():
            for p_node in p_nodes:
                self._component_equivalence[rhs_instance[rule.p_rhs[p_node]]] =\
                    lhs_instance[lhs_node]
