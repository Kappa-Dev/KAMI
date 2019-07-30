"""Collection of untils for identification of entities in a KAMI."""
import networkx as nx
import numpy as np

from regraph import Rule
from regraph.primitives import (get_node,
                                get_edge,
                                add_node_attrs,
                                find_matching)

from kami.exceptions import KamiHierarchyError


def find_fragment(a_meta_data, a_location, dict_of_b, name=True):
    """Find a protein fragment in a collection of other fragments."""
    a_start = None
    a_end = None
    a_name = None
    a_interpro = None
    a_order = None
    if "start" in a_location.keys():
        a_start = int(min(a_location["start"]))
    if "end" in a_location.keys():
        a_end = int(max(a_location["end"]))
    if "name" in a_meta_data.keys():
        a_name = list(a_meta_data["name"])[0].lower()
    if "interproid" in a_meta_data.keys():
        a_interpro = a_meta_data["interproid"]
    if "order" in a_location.keys():
        a_order = list(a_location["order"])[0]

    satisfying_fragments = []
    for b_id, (b_meta_data, b_location) in dict_of_b.items():
        b_start = None
        b_end = None
        b_name = None
        b_interpro = None
        if "start" in b_location.keys():
            b_start = int(min(b_location["start"]))
        if "end" in b_location.keys():
            b_end = int(max(b_location["end"]))
        if "name" in b_meta_data.keys():
            b_name = list(b_meta_data["name"])[0].lower()
        if "interproid" in b_meta_data.keys():
            b_interpro = b_meta_data["interproid"]

        if a_start is not None and a_end is not None and\
           b_start is not None and b_end is not None:
            if a_start >= b_start and a_end <= b_end:
                return b_id
            elif a_start <= b_start and a_end >= b_end:
                return b_id
        elif a_name is not None and b_name is not None:
            if name:
                if a_name in b_name or b_name in a_name:
                    satisfying_fragments.append(b_id)
        elif a_interpro is not None and b_interpro is not None:
            if len(a_interpro.intersection(b_interpro)) > 0:
                satisfying_fragments.append(b_id)

    if len(satisfying_fragments) == 1:
        return satisfying_fragments[0]
    elif len(satisfying_fragments) > 1:
        # Try to find if there is a unique region in the list of
        # satisfying regions with the same order number
        if a_order is not None:
            same_order_fragments = []
            for b_id in satisfying_fragments:
                if "order" in dict_of_b[b_id][1].keys():
                    if a_order in dict_of_b[b_id][1]["order"]:
                        same_order_fragments.append(b_id)
            # if not explicit order number was found
            if len(same_order_fragments) == 0:
                try:
                    start_orders = np.argsort([
                        int(min(dict_of_b[b_id][1]["start"]))
                        for b_id in satisfying_fragments
                        if "start" in dict_of_b[b_id][1].keys()
                    ])
                    return satisfying_fragments[
                        start_orders[a_order - 1]]
                except:
                    return None
            elif len(same_order_fragments) == 1:
                return same_order_fragments[0]
            else:
                return None
    else:
        return None


class EntityIdentifier:

    def __init__(self, graph, meta_typing, immediate=True,
                 hierarchy=None, graph_id=None, meta_model_id=None):
        self.graph = graph
        self.meta_typing = meta_typing
        self.immediate = immediate
        self.hierarchy = hierarchy
        self.graph_id = graph_id
        self.meta_model_id = meta_model_id

    def find_matching_in_graph(self, pattern, lhs_typing=None,
                               nodes=None):
        """."""
        if self.hierarchy is not None:
            if lhs_typing is not None:
                lhs_typing = {
                    self.meta_model_id: lhs_typing
                }
            instances = self.hierarchy.find_matching(
                self.graph_id, pattern,
                pattern_typing=lhs_typing, nodes=nodes)
        else:
            untyped_instances = find_matching(
                self.graph, pattern, nodes=nodes)
            if lhs_typing is not None:
                instances = []
                for i in untyped_instances:
                    for k, v in i.items():
                        if self.meta_typing[v] != lhs_typing[k]:
                            break
                    else:
                        instances.append(i)
            else:
                instances = untyped_instances
        return instances

    def rewrite_graph(self, rule, instance):
        """."""
        if self.hierarchy is not None:
            _, rhs_instance = self.hierarchy.rewrite(
                self.graph_id, rule, instance)
        else:
            _, rhs_instance = rule.apply_to(self.graph, instance, inplace=True)
        return rhs_instance

    def nodes_of_type(self, type_name):
        """Get action graph nodes of a specified type."""
        nodes = []
        for node in self.graph.nodes():
            if node in self.meta_typing:
                if self.meta_typing[node] == type_name:
                    nodes.append(node)
        return nodes

    def get_genes(self):
        return self.nodes_of_type("gene")

    def get_regions(self):
        return self.nodes_of_type("region")

    def predecessors_of_type(self, node_id, meta_type):
        preds = []
        for pred in self.graph.predecessors(node_id):
            if self.meta_typing[pred] == meta_type:
                preds.append(pred)
        return preds

    def successors_of_type(self, node_id, meta_type):
        sucs = []
        for suc in self.graph.successors(node_id):
            if self.meta_typing[suc] == meta_type:
                sucs.append(suc)
        return sucs

    def ancestors_of_type(self, node_id, meta_type):
        ancestors = self.predecessors_of_type(node_id, meta_type)
        visited = set()
        next_level_to_visit = set([
            p for p in self.graph.predecessors(node_id)
            if meta_type == "mod" or meta_type == "bnd" or (self.meta_typing[p] != "mod" and self.meta_typing[p] != "bnd")
        ])
        while len(next_level_to_visit) > 0:
            new_level_to_visit = set()
            for n in next_level_to_visit:
                if n not in visited:
                    visited.add(n)
                    ancestors += self.predecessors_of_type(n, meta_type)
                new_level_to_visit.update(
                    set([
                        p for p in self.graph.predecessors(n)
                        if meta_type == "mod" or meta_type == "bnd" or (self.meta_typing[p] != "mod" and self.meta_typing[p] != "bnd")
                    ]))
            next_level_to_visit = new_level_to_visit
        return ancestors

        # ag_typing = self.get_action_graph_typing()
        # all_predecessors = self.action_graph.predecessors(node_id)
        # subcomponents = set([
        #     p for p in all_predecessors
        #     if ag_typing[p] != "mod" and ag_typing[p] != "bnd"
        # ] + [node_id])
        # visited = set()
        # next_level_to_visit = set([
        #     p for p in all_predecessors
        #     if ag_typing[p] != "mod" and ag_typing[p] != "bnd"
        # ])
        # while len(next_level_to_visit) > 0:
        #     new_level_to_visit = set()
        #     for n in next_level_to_visit:
        #         if n not in visited:
        #             visited.add(n)
        #             new_anc = set([
        #                 p
        #                 for p in self.action_graph.predecessors(n)
        #                 if ag_typing[p] != "mod" and ag_typing[p] != "bnd"
        #             ])
        #             subcomponents.update(new_anc)
        #         new_level_to_visit.update(new_anc)
        #     next_level_to_visit = new_level_to_visit
        # return subcomponents

    def descendants_of_type(self, node_id, meta_type):
        ancestors = self.successors_of_type(node_id, meta_type)
        visited = set()
        next_level_to_visit = set(self.graph.successors(node_id))
        while len(next_level_to_visit) > 0:
            new_level_to_visit = set()
            for n in next_level_to_visit:
                if n not in visited:
                    visited.add(n)
                    ancestors += self.successors_of_type(n, meta_type)
                new_level_to_visit.update(
                    set(self.graph.successors(n)))
            next_level_to_visit = new_level_to_visit
        return ancestors

    def get_gene_of(self, node_id):
        if self.meta_typing[node_id] == "gene":
            return node_id
        else:
            # bfs to find a gene
            visited = set()
            next_level_to_visit = set(self.graph.successors(node_id))
            while len(next_level_to_visit) > 0:
                new_level_to_visit = set()
                for n in next_level_to_visit:
                    if n not in visited:
                        visited.add(n)
                        if self.meta_typing[n] == "gene":
                            return n
                    new_level_to_visit.update(
                        set(self.graph.successors(n)))
                next_level_to_visit = new_level_to_visit
        raise ValueError(
            "No gene node is associated with an element '{}'".fromat(
                node_id))
        return None

    def get_attached_regions(self, node_id):
        """Get a list of regions belonging to a specified agent."""
        if self.immediate:
            return self.predecessors_of_type(node_id, "region")
        else:
            return self.ancestors_of_type(node_id, "region")

    def get_attached_sites(self, node_id):
        """Get a list of sites belonging to a specified agent."""
        if self.immediate:
            return self.predecessors_of_type(node_id, "site")
        else:
            return self.ancestors_of_type(node_id, "site")

    def get_attached_residues(self, node_id):
        if self.immediate:
            return self.predecessors_of_type(node_id, "residue")
        else:
            return self.ancestors_of_type(node_id, "residue")

    def get_attached_states(self, node_id):
        if self.immediate:
            return self.predecessors_of_type(node_id, "state")
        else:
            return self.ancestors_of_type(node_id, "state")

    def identify_gene(self, gene):
        """Find corresponding gene in action graph."""
        for node in self.get_genes():
            gene_attrs = get_node(self.graph, node)
            if "uniprotid" in gene_attrs.keys() and\
               gene.uniprotid in gene_attrs["uniprotid"]:
                return node
        return None

    def _identify_fragment(self, fragment,
                           ref_agent, fragment_type, name=True):
        if self.immediate:
            fragment_candidates = self.predecessors_of_type(
                ref_agent, fragment_type)
            return find_fragment(
                fragment.meta_data(), fragment.location(),
                {
                    f: (
                        get_node(self.graph, f),
                        get_edge(self.graph, f, ref_agent)
                    )
                    for f in fragment_candidates
                },
                name
            )
        else:
            fragment_candidates = self.ancestors_of_type(
                ref_agent, fragment_type)
            candidates_data = dict()
            for f in fragment_candidates:
                node_data = get_node(self.graph, f)
                for s in self.graph.successors(f):
                    location_data = get_edge(self.graph, f, s)
                    candidates_data[f] = (node_data, location_data)

            return find_fragment(
                fragment.meta_data(), fragment.location(),
                {
                    f: (
                        get_node(self.graph, f),
                        get_edge(self.graph, f, ref_agent)
                    )
                    for f in fragment_candidates
                },
                name
            )

    def identify_region(self, region, ref_agent):
        """Find corresponding region in action graph."""
        if ref_agent not in self.get_genes():
            raise KamiHierarchyError(
                "Agent with UniProtID '%s' is not found in the action graph" %
                ref_agent
            )
        else:
            return self._identify_fragment(
                region, ref_agent, "region")

    def identify_site(self, site, ref_agent):
        """Find corresponding site in action graph."""
        if ref_agent not in self.get_genes() and\
           ref_agent not in self.get_regions():
            raise KamiHierarchyError(
                "Gene with the UniProtAC '%s' is not found in the action graph" %
                ref_agent
            )
        else:
            return self._identify_fragment(site, ref_agent, "site", name=False)

    def identify_residue(self, residue, ref_agent,
                         add_aa=False, rewriting=False):
        """Find corresponding residue.

        residue : kami.entities.residue
            Input residue entity to search for
        ref_agent
            Id of the reference agent to which residue belongs,
            can reference either to a gene, a region or a site
            of the action graph
        add_aa : bool
            Add aa value if location is found but aa is not
        rewriting : bool
            If True, add aa value using SqPO rewriting, otherwise
            using primitives (used if `add_aa` is True)
        """
        ref_gene = self.get_gene_of(ref_agent)
        residue_candidates = self.get_attached_residues(ref_gene)

        if residue.loc is not None:
            for res in residue_candidates:
                if (self.immediate):
                    res_agent_edges = [get_edge(
                        self.graph, res, ref_agent)]
                else:
                    res_agent_edges = [
                        get_edge(self.graph, res, s)
                        for s in self.graph.successors(res)]
                for res_agent_edge in res_agent_edges:
                    if "loc" in res_agent_edge.keys():
                        if residue.loc == int(list(res_agent_edge["loc"])[0]):
                            res_node = get_node(self.graph, res)
                            if not residue.aa.issubset(
                                res_node["aa"]) and\
                                    add_aa is True:
                                if rewriting:
                                    pattern = nx.DiGraph()
                                    pattern.add_node(res)
                                    rule = Rule.from_transform(pattern)
                                    rule.inject_add_node_attrs(
                                        res, {"aa": {residue.aa}})
                                    if self.hierarchy is not None:
                                        self.hierarchy.rewrite(
                                            self.graph_id, rule,
                                            instance={res: res})
                                    else:
                                        rule.apply_to(
                                            self.graph, instance={res: res},
                                            inplace=True)
                                else:
                                    add_node_attrs(
                                        self.graph,
                                        res,
                                        {"aa": res_node["aa"].union(residue.aa)})
                            return res
        else:
            for res in residue_candidates:
                if (self.immediate):
                    res_agent_edges = [get_edge(
                        self.graph, res, ref_agent)]
                else:
                    res_agent_edges = [
                        get_edge(self.graph, res, s)
                        for s in self.graph.successors(res)]
                for res_agent_edge in res_agent_edges:
                    if "loc" not in res_agent_edge.keys() or\
                       res_agent_edge["loc"].is_empty():
                        res_node = get_node(self.graph, res)
                        if residue.aa <= res_node["aa"]:
                            return res
                        elif add_aa is True:
                            if rewriting:
                                pattern = nx.DiGraph()
                                pattern.add_node(res)
                                rule = Rule.from_transform(pattern)
                                rule.inject_add_node_attrs(
                                    res, {"aa": {residue.aa}})
                                instance = {
                                    n: n for n in pattern.nodes()
                                }
                                instance[res] = res
                                if self.hierarchy is not None:
                                    self.hierarchy.rewrite(
                                        self.graph_id, rule, instance=instance)
                                else:
                                    rule.apply_to(
                                        self.graph, instance=instance,
                                        inplace=True)
                            else:
                                add_node_attrs(
                                    self.graph,
                                    res,
                                    {"aa": res_node["aa"].union(residue.aa)})
                            return res
        return None

    def identify_state(self, state, ref_agent):
        """Find corresponding state of reference agent."""
        state_candidates = self.get_attached_states(ref_agent)
        for s in state_candidates:
            name = list(get_node(self.graph, s)["name"])[0]
            # values = action_graph.node[pred][name]
            if state.name == name:
                    # if state.value not in values:
                    #     add_node_attrs(
                    #         action_graph,
                    #         pred,
                    #         {name: {state.value}})
                return s
        return None

    def subcomponents(self, node_id):
        """Get all the subcomponent nodes."""
        all_predecessors = list(self.graph.predecessors(node_id))
        subcomponents = set([
            p for p in all_predecessors
            if self.meta_typing[p] != "mod" and self.meta_typing[p] != "bnd"
        ] + [node_id])
        visited = set()
        next_level_to_visit = set([
            p for p in all_predecessors
            if self.meta_typing[p] != "mod" and self.meta_typing[p] != "bnd"
        ])
        while len(next_level_to_visit) > 0:
            new_level_to_visit = set()
            for n in next_level_to_visit:
                if n not in visited:
                    visited.add(n)
                    new_anc = set([
                        p
                        for p in self.graph.predecessors(n)
                        if self.meta_typing[p] != "mod" and self.meta_typing[p] != "bnd"
                    ])
                    subcomponents.update(new_anc)
                new_level_to_visit.update(new_anc)
            next_level_to_visit = new_level_to_visit
        return subcomponents
