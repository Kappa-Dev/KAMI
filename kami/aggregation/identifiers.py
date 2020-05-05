"""Collection of untils for identification of entities in a KAMI."""
import networkx as nx
import numpy as np
import warnings

from regraph import Rule

from kami.data_structures.entities import Region, Site, Residue, State
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


def get_uniprot(data):
    """Get UniProt AC from data."""
    uniprotid = None
    if "uniprotid" in data.keys():
        uniprotid = list(data["uniprotid"])[0]
    return uniprotid


class EntityIdentifier:
    """Class for identification of entities in the wrapped graph.

    An object of the EntityIdentifier class represents a wrapper
    around a graph object (corresponding to, for example, an
    action graph or a nugget), where the identification of entities
    is performed. Typically, an identifier takes as an input some
    data or an instance of a class from the `kami.entities` module
    and tries to identify the corresponding nodes in the wrapped graph.

    Attributes
    ----------
    graph : regraph.Graph
        Graph where the identification of entities is performed
    meta_typing : dict
        Typing of the nodes in the wrapped graph by KAMI's meta-model
    immediate : bool, optional
        Flag indicating if the entities in the identification
        are immediately adjacent to the reference node. For example,
        if True `get_attached_regions` returns all the regions
        immediately attached to the provided node.
    hierarchy : regraph.Hierarchy, optional
        Hierarchy where the wrapped graph object is situated. If specified,
        rewriting of the graph is performed through the hierarchy interface
    graph_id : hashable, optional
        Id of the wrapped graph in the hierarchy
    meta_model_id : hashable, optional
        Id of the meta-model in the hierarchy
    """

    def __init__(self, graph, meta_typing, immediate=True,
                 hierarchy=None, graph_id=None, meta_model_id=None):
        """Initialize entity identifier."""
        self.graph = graph
        self.meta_typing = meta_typing
        self.immediate = immediate
        self.hierarchy = hierarchy
        self.graph_id = graph_id
        self.meta_model_id = meta_model_id

    def find_matching_in_graph(self, pattern, lhs_typing=None,
                               nodes=None):
        """Find matching of the pattern in the wrapped graph."""
        if self.hierarchy is not None:
            if lhs_typing is not None:
                lhs_typing = {
                    self.meta_model_id: lhs_typing
                }
            instances = self.hierarchy.find_matching(
                self.graph_id, pattern,
                pattern_typing=lhs_typing, nodes=nodes)
        else:
            untyped_instances = self.graph.find_matching(pattern, nodes=nodes)
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

    def rewrite_graph(self, rule, instance=None,
                      message="", update_type=None):
        """Rewrite the wrapped graph."""
        if self.hierarchy is not None:
            rhs_instance = self.hierarchy.rewrite(
                self.graph_id, rule, instance, message=message,
                update_type=update_type)
        else:
            rhs_instance = self.graph.rewrite(rule, instance)
        return rhs_instance

    def nodes_of_type(self, type_name):
        """Get action graph nodes of a specified type."""
        nodes = []
        for node in self.graph.nodes():
            if node in self.meta_typing:
                if self.meta_typing[node] == type_name:
                    nodes.append(node)
        return nodes

    def get_protoforms(self):
        """Get all the protoform nodes."""
        return self.nodes_of_type("protoform")

    def get_regions(self):
        """Get all the region nodes."""
        return self.nodes_of_type("region")

    def predecessors_of_type(self, node_id, meta_type):
        """Get all the predecessors of the node with the specified type."""
        preds = []
        for pred in self.graph.predecessors(node_id):
            if self.meta_typing[pred] == meta_type:
                preds.append(pred)
        return preds

    def successors_of_type(self, node_id, meta_type):
        """Get all the successors of the node with the specified type."""
        sucs = []
        for suc in self.graph.successors(node_id):
            if self.meta_typing[suc] == meta_type:
                sucs.append(suc)
        return sucs

    def ancestors_of_type(self, node_id, meta_type):
        """Get all the ancestors of the node with the specified type."""
        ancestors = self.predecessors_of_type(node_id, meta_type)
        visited = set()
        next_level_to_visit = set([
            p for p in self.graph.predecessors(node_id)
            if meta_type == "mod" or meta_type == "bnd" or (
                self.meta_typing[p] != "mod" and self.meta_typing[p] != "bnd")
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
                        if meta_type == "mod" or meta_type == "bnd" or (
                            self.meta_typing[p] != "mod" and
                            self.meta_typing[p] != "bnd")
                    ]))
            next_level_to_visit = new_level_to_visit
        return ancestors

    def descendants_of_type(self, node_id, meta_type):
        """Get all the descendants of the node with the specified type."""
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

    def get_protoform_of(self, node_id):
        """Get protoform of the node id."""
        if self.meta_typing[node_id] == "protoform":
            return node_id
        else:
            # bfs to find a protoform
            visited = set()
            next_level_to_visit = set(self.graph.successors(node_id))
            while len(next_level_to_visit) > 0:
                new_level_to_visit = set()
                for n in next_level_to_visit:
                    if n not in visited:
                        visited.add(n)
                        if self.meta_typing[n] == "protoform":
                            return n
                    new_level_to_visit.update(
                        set(self.graph.successors(n)))
                next_level_to_visit = new_level_to_visit
        raise ValueError(
            "No protoform node is associated with an element '{}'".fromat(
                node_id))
        return None

    def get_attached_regions(self, node_id):
        """Get a list of regions belonging to the specified component."""
        if self.immediate:
            return self.predecessors_of_type(node_id, "region")
        else:
            return self.ancestors_of_type(node_id, "region")

    def get_attached_sites(self, node_id):
        """Get a list of sites belonging to the specified component."""
        if self.immediate:
            return self.predecessors_of_type(node_id, "site")
        else:
            return self.ancestors_of_type(node_id, "site")

    def get_attached_residues(self, node_id):
        """Get a list of residues belonging to the specified component."""
        if self.immediate:
            return self.predecessors_of_type(node_id, "residue")
        else:
            return self.ancestors_of_type(node_id, "residue")

    def get_attached_states(self, node_id):
        """Get a list of states belonging to the specified component."""
        if self.immediate:
            return self.predecessors_of_type(node_id, "state")
        else:
            return self.ancestors_of_type(node_id, "state")

    def identify_protoform(self, protoform):
        """Find protoform using the input entity."""
        for node in self.get_protoforms():
            gene_attrs = self.graph.get_node(node)
            if "uniprotid" in gene_attrs.keys() and\
               protoform.uniprotid in gene_attrs["uniprotid"]:
                return node
        return None

    def identify_protein(self, protein):
        """Find protein using the input entity."""
        for node in self.get_protoforms():
            gene_attrs = self.graph.get_node(node)
            if "uniprotid" in gene_attrs.keys() and\
               protein.protoform.uniprotid in gene_attrs["uniprotid"]:
                if protein.name:
                    if "variant_name" in gene_attrs.keys() and\
                            protein.name in gene_attrs["variant_name"]:
                        return node
                else:
                    return node
        return None

    def _identify_fragment(self, fragment,
                           ref_agent, fragment_type, name=True):
        """Identify fragment (region or site) using the entity."""
        if self.immediate:
            fragment_candidates = self.predecessors_of_type(
                ref_agent, fragment_type)
            return find_fragment(
                fragment.meta_data(), fragment.location(),
                {
                    f: (
                        self.graph.get_node(f),
                        self.graph.get_edge(f, ref_agent)
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
                node_data = self.graph.get_node(f)
                for s in self.graph.successors(f):
                    location_data = self.graph.get_edge(f, s)
                    candidates_data[f] = (node_data, location_data)

            return find_fragment(
                fragment.meta_data(), fragment.location(),
                {
                    f: (
                        self.graph.get_node(f),
                        self.graph.get_edge(f, ref_agent)
                    )
                    for f in fragment_candidates
                },
                name
            )

    def identify_region(self, region, ref_agent):
        """Find corresponding region in the graph."""
        if ref_agent not in self.get_protoforms():
            raise KamiHierarchyError(
                "Agent with UniProtID '%s' is not found in the graph" %
                ref_agent
            )
        else:
            return self._identify_fragment(
                region, ref_agent, "region")

    def identify_site(self, site, ref_agent):
        """Find corresponding site in the graph."""
        if ref_agent not in self.get_protoforms() and\
           ref_agent not in self.get_regions():
            raise KamiHierarchyError(
                "Protoform with the UniProtAC '%s' is not found in the graph" %
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
            can reference either to a protoform, a region or a site
            of the action graph
        add_aa : bool
            Add aa value if location is found but aa is not
        rewriting : bool
            If True, add aa value using SqPO rewriting, otherwise
            using primitives (used if `add_aa` is True)
        """
        ref_gene = self.get_protoform_of(ref_agent)
        residue_candidates = self.get_attached_residues(ref_gene)

        if residue.loc is not None:
            for res in residue_candidates:
                if (self.immediate):
                    res_agent_edges = [
                        self.graph.get_edge(res, ref_agent)]
                else:
                    res_agent_edges = [
                        self.graph.get_edge(res, s)
                        for s in self.graph.successors(res)]
                for res_agent_edge in res_agent_edges:
                    if "loc" in res_agent_edge.keys():
                        if residue.loc == int(list(res_agent_edge["loc"])[0]):
                            res_node = self.graph.get_node(res)
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
                                    self.graph.add_node_attrs(
                                        res,
                                        {"aa": res_node["aa"].union(residue.aa)})
                            return res
        else:
            for res in residue_candidates:
                if (self.immediate):
                    res_agent_edges = [self.graph.get_edge(res, ref_agent)]
                else:
                    res_agent_edges = [
                        self.graph.get_edge(res, s)
                        for s in self.graph.successors(res)]
                for res_agent_edge in res_agent_edges:
                    if "loc" not in res_agent_edge.keys() or\
                       res_agent_edge["loc"].is_empty():
                        res_node = self.graph.get_node(res)
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
                                self.graph.add_node_attrs(
                                    res,
                                    {"aa": res_node["aa"].union(residue.aa)})
                            return res
        return None

    def identify_state(self, state, ref_agent):
        """Find the state of the reference agent by entity."""
        state_candidates = self.get_attached_states(ref_agent)
        for s in state_candidates:
            name = list(self.graph.get_node(s)["name"])[0]
            if state.name == name:
                return s
        return None

    def identify_component(self, entity, ref_agent):
        """Find a component of the reference agent by the input entity."""
        if isinstance(entity, Region):
            # Here smth doesnt work
            return self.identify_region(entity, ref_agent)
        elif isinstance(entity, Site):
            return self.identify_site(entity, ref_agent)
        elif isinstance(entity, Residue):
            return self.identify_residue(entity, ref_agent)
        elif isinstance(entity, State):
            return self.identify_state(entity, ref_agent)

    def subcomponents(self, node_id):
        """Get all the subcomponent nodes.

        For example, if the input node_id is a protoform, returns all the
        regions, sites, residues and states attached to the protoform.
        """
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
                        if self.meta_typing[p] != "mod" and
                        self.meta_typing[p] != "bnd"
                    ])
                    subcomponents.update(new_anc)
                    new_level_to_visit.update(new_anc)
            next_level_to_visit = new_level_to_visit
        return subcomponents

    def get_attached_bnd(self, node):
        """Get BND nodes attached to the specified node."""
        result = self.successors_of_type(node, "bnd")
        if not self.immediate:
            for r in self.get_attached_regions(node):
                result += self.successors_of_type(r, "bnd")
            for s in self.get_attached_sites(node):
                result += self.successors_of_type(s, "bnd")
        return list(set(result))

    def identify_bnd_template(self, bnd_node):
        """Get binding template given a bnd node.

        Given the id of a binding node in the graph,
        identify the left and the right partners of the
        binding together with their acting components
        (regions or/and sites they use to perform
        the binding).
        """
        def _fill_partner_components(pred, role):
            if self.meta_typing[pred] == "site":
                template[role + "_partner_site"].add(pred)
                template[role + "_partner"].add(self.get_protoform_of(pred))

                edge_found = False
                for partner in template[role + "_partner"]:
                    if self.graph.exists_edge(pred, partner):
                        edge_found = True
                        break
                if not edge_found:
                    # find left partner region
                    regions = set()
                    for partner in template[role + "_partner"]:
                        regions.update(self.get_attached_regions(partner))

                    for r in regions:
                        if self.graph.exists_edge(pred, r):
                            if role + "_partner_region" in template:
                                template[role + "_partner_region"].add(r)
                            else:
                                template[role + "_partner_region"] = {r}
            elif self.meta_typing[pred] == "region":
                template[role + "_partner_region"].add(pred)
                template[role + "_partner"].add(self.get_protoform_of(pred))
            else:
                template[role + "_partner"].add(pred)

        template = {
            "left_partner": set(),
            "left_partner_region": set(),
            "left_partner_site": set(),
            "right_partner": set(),
            "right_partner_region": set(),
            "right_partner_site": set()
        }
        preds = list(self.graph.predecessors(bnd_node))
        if len(preds) != 2:
            # Merge by the uniprot id
            uniprots = set([
                list(
                    self.graph.get_node(
                        (self.get_protoform_of(p)))["uniprotid"])[0] for p in preds
            ])
            if len(uniprots) != 2:
                warnings.warn(
                    "More than two bnd partners found" +
                    "cannot identify bnd template!"
                )
                return template
            else:
                uniprot1 = list(uniprots)[0]
                uniprot2 = list(uniprots)[1]
                for p in preds:
                    p_uniprot = list(self.graph.get_node(
                        (self.get_protoform_of(p)))["uniprotid"])[0]
                    if p_uniprot == uniprot1:
                        _fill_partner_components(p, "left")
                    if p_uniprot == uniprot2:
                        _fill_partner_components(p, "right")
        else:
            _fill_partner_components(preds[0], "left")
            _fill_partner_components(preds[1], "right")

        return template

    def _get_acting_components(self, node):
        agent = None
        region = None
        site = None
        if self.meta_typing[node] == "site":
            site = node
            agent = self.get_protoform_of(node)

            edge_found = False
            if self.graph.exists_edge(node, agent):
                edge_found = True
            if not edge_found:
                # find left partner region
                regions = set()
                regions.update(self.get_attached_regions(agent))

                for r in regions:
                    if self.graph.exists_edge(node, r):
                        region = r
                        break

        elif self.meta_typing[node] == "region":
            region = node
            agent = self.get_protoform_of(node)
        else:
            agent = node
        return agent, region, site

    def identify_mod_template(self, mod_node):
        """Get modification template given a mod node.

        Given the id of a modification node in the graph,
        identify the enzyme and the substrate of the
        modification together with their acting components
        (regions or/and sites they use to perform
        the modification).
        """
        template = {
            "enzyme": set(),
            "enzyme_region": set(),
            "enzyme_site": set(),
            "substrate": set(),
            "substrate_region": set(),
            "substrate_site": set(),
            "substrate_residue": set(),
            "mod_state": set(),
            "mod": set()
        }
        preds = list(self.graph.predecessors(mod_node))
        for pred in preds:
            agent, region, site = self._get_acting_components(
                pred)
            template["enzyme"].add(agent)
            if region:
                template["enzyme_region"].add(region)
            if site:
                template["enzyme_site"].add(region)
        return template

    def get_attached_mod(self, node, all_directions=False):
        """Get MOD nodes attached to the specified node."""
        result = self.successors_of_type(node, "mod")

        if not self.immediate:
            for r in self.get_attached_regions(node):
                result += self.successors_of_type(r, "mod")
            for s in self.get_attached_sites(node):
                result += self.successors_of_type(s, "mod")

        if all_directions:
            result += self.ancestors_of_type(node, "mod")

        return result

    def get_protoform_by_uniprot(self, uniprotid):
        """Get a protoform by the UniProt AC."""
        for protoform in self.get_protoforms():
            attrs = self.graph.get_node(protoform)
            u = list(attrs["uniprotid"])[0]
            if u == uniprotid:
                return protoform
        return None

    def get_modifications(self, enzyme_ac, substrate_ac):
        """Get modification interactions."""
        mods = set()
        enzyme_node = self.get_protoform_by_uniprot(enzyme_ac)
        for mod in self.get_attached_mod(enzyme_node):
            for s in self.graph.successors(mod):
                substrate_node = self.get_protoform_of(s)
                up = get_uniprot(self.graph.get_node(substrate_node))
                if up == substrate_ac:
                    # the right partner of binding matches
                    mods.add(mod)
        return mods

    def get_bindings(self, left_ac, right_ac):
        """Get binding interactions."""
        left_node = self.get_protoform_by_uniprot(left_ac)

        # Find all the bnd nodes connecting the left with the right
        bnds = set()
        for bnd in self.get_attached_bnd(left_node):
            preds = self.graph.predecessors(bnd)
            if left_ac != right_ac:
                for p in preds:
                    right_node = self.get_protoform_of(p)
                    up = get_uniprot(self.graph.get_node(right_node))
                    if up == right_ac:
                        # the right partner of binding matches
                        bnds.add(bnd)
            else:
                if len(preds) == 1:
                    bnds.add(bnd)

        return bnds
