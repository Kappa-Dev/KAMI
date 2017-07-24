""" represent a kappa model as python """
import regraph.tree as tree

from regraph.category_op import (pullback, pushout,
                                 compose_homomorphisms,
                                 multi_pullback_pushout,
                                 pushout_from_partial_mapping,
                                 merge_classes,
                                 subgraph,
                                 pullback_pushout)
from regraph.utils import (keys_by_value, restrict_mapping,
                           union_mappings, id_of,
                           reverse_image)

from regraph.rules import Rule
from regraph.primitives import (unique_node_id, add_node, add_edge, remove_node)
import regraph.primitives as prim
from math import sqrt
import networkx as nx
import functools 
import copy
from itertools import product, combinations
# from profilehooks import profile


class KappaModel(object):
    """A kappa model"""
    def __init__(self, agent_decls, rules, variables):
        self.agent_decls = agent_decls
        self.rules = rules
        self.variables = variables

    def __str__(self):
        return "{}\n\n{}\n\n{}\n\n{}".format(
            '%def: "newSyntax" "true"',
            "\n".join(map(str, self.agent_decls)),
            "\n".join(map(str, self.rules)),
            "\n".join(map(str, self.variables)))


class AgentDecl(object):
    """Agent delcaration"""
    def __init__(self, name, sites_decl):
        self.name = name
        self.sites_decl = sites_decl

    def __str__(self):
        return "%agent: {}({})".format(self.name, ",".join(map(str, self.sites_decl)))


class SiteDecl(object):
    """Site declaration"""
    def __init__(self, name, values=None):
        self.name = name
        if values is None:
            self.values = []
        else:
            self.values = values

    def __str__(self):
        return "".join([self.name]+["~"+v for v in self.values])


class KappaRule(object):
    """Kappa Rule"""
    def __init__(self, name, rate, agents):
        self.name = name
        self.rate = rate
        self.agents = agents

    def __str__(self):
        return "'{}' {} @ '{}'".format(
            self.name,
            ",".join(map(str, self.agents)),
            self.rate)


class Agent(object):
    """Kappa agnent"""
    def __init__(self, name, sites, prefix=""):
        self.name = name
        self.sites = sites
        self.prefix = prefix

    def __str__(self):
        return "{}{}({})".format(
            self.prefix,
            self.name,
            ",".join(map(str, self.sites)))


class BindingSite(object):
    """Kappa site"""
    def __init__(self, name, old_binding, new_binding=None):
        self.name = name
        self.old_binding = old_binding
        self.new_binding = new_binding

    def __str__(self):
        if self.new_binding is None:
            return "{}!{}".format(self.name, self.old_binding)
        else:
            return "{}!{}/!{}".format(self.name, self.old_binding,
                                      self.new_binding)


class StateSite(object):
    """Kappa site"""
    def __init__(self, name, old_state, new_state):
        self.name = name
        self.old_state = old_state
        self.new_state = new_state

    def __str__(self):
        # new and old should not both be None at the same time
        if self.old_state is None:
            return "{}/~{}".format(self.name, self.new_state)
        if self.new_state is None:
            return "{}~{}".format(self.name, self.old_state)
        else:
            return "{}~{}/~{}".format(self.name, self.old_state,
                                      self.new_state)


class Variable(object):
    """Kappa variable"""
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%var: '{}' {}".format(self.name, self.value)


def _components_of_agent(graph, mm_typing, agent):
    components = {agent}

    def _step(components):
        to_add = set()
        for target in components:
            for (source, _) in graph.in_edges(target):
                if mm_typing[source] in ["region", "locus", "state",
                                         "residue"]:
                    to_add.add(source)
        return to_add | components

    while True:
        new_components = _step(components)
        if new_components == components:
            break
        else:
            components = new_components
    return components


def _agents_of_components(graph, mm_typing, component):
    components = {component}

    def _step(components):
        to_add = set()
        for source in components:
            for (_, target) in graph.out_edges(source):
                if mm_typing[target] in ["region", "agent", "residue",
                                         "locus", "state"]:
                    to_add.add(target)
        return to_add | components

    while True:
        new_components = _step(components)
        if new_components == components:
            break
        else:
            components = new_components
    return components


def _site_names(action_graph, node, parent_components):
    """ kappa site name from locus or state of the actiongraph """
    return ["{}_{}".format(node, parent)
            for parent in action_graph[node]
            if parent in parent_components]


def _agent_decl(action_graph, typing, agent):
    components = _components_of_agent(action_graph, typing, agent)
    sites_decl = []
    for comp in components:
        if typing[comp] == "locus":
            for site_name in _site_names(action_graph, comp, components):
                sites_decl.append(SiteDecl(site_name))
        if typing[comp] == "state":
            for site_name in _site_names(action_graph, comp, components):
                sites_decl.append(SiteDecl(site_name,
                                           action_graph.node[comp]["val"]))

    return AgentDecl(agent, sites_decl)


def _agents_decl(hie, ag_id, ag_nodes, metamodel_id):
    typing = hie.edge[ag_id][metamodel_id].mapping
    agent_decls = []
    for agent in (n for n in ag_nodes if typing[n] == "agent"):
        agent_decls.append(_agent_decl(hie.node[ag_id].graph,
                                       hie.edge[ag_id][metamodel_id].mapping,
                                       agent))
    return agent_decls


def _rule_decl(ag_typing, mm_typing, nug, name, rate):

    def _binding_index(node):
        bindings = [node for node in nug.nodes()
                    if mm_typing[node] in ["bnd", "brk",
                                           "is_bnd", "is_free"]]
        return bindings.index(node)

    loci_defs = {}
    for loc in nug.nodes():
        if mm_typing[loc] == "locus":
            before = None
            after = None
            bindings = [node for (_, node) in nug.out_edges(loc)
                        if mm_typing[node] in ["bnd", "brk", "is_bnd"]]
            for binding in bindings:
                if mm_typing[binding] == "bnd":
                    if after is None or after == ".":
                        after = _binding_index(binding)
                    else:
                        raise ValueError("too many after values")
                if mm_typing[binding] == "brk":
                    if before is None:
                        before = _binding_index(binding)
                        if after is None:
                            after = "."
                    else:
                        raise ValueError("too many before values")

                if mm_typing[binding] == "is_bnd":
                    if before is None:
                        before = _binding_index(binding)
                    else:
                        raise ValueError("too many before values")
                    if after is None:
                        after = _binding_index(binding)
                    else:
                        raise ValueError("too many after values")
            if before == after:
                after = None
            if before is None:
                before = "."
            parent_components = [comp for comp in nug[loc]
                                 if mm_typing[comp] in ["region", "residue",
                                                        "agent"]]
            if len(parent_components) != 1:
                raise ValueError("locus should have one parent after unfold")
            site_name = "{}_{}".format(ag_typing[loc],
                                       ag_typing[parent_components[0]])
            loci_defs[loc] = BindingSite(site_name, before, after)

    state_defs = {}
    for state in nug.nodes():
        if mm_typing[state] == "state":
            # if len(nug.node[state]["val"]) != 1:
            #     raise ValueError("states should have exactly one value"
            #                      " before exporting to kappa")
            # before = list(nug.node[state]["val"])[0]
            before = None
            tests = [node for (node, state) in nug.in_edges(state)
                     if mm_typing[node] == "is_equal"]
            for test in tests:
                if before is None:
                    if len(nug.node[test]["val"]) != 1:
                        raise ValueError("is_equal nodes should have"
                                         "exactly one value")
                    before = list(nug.node[test]["val"])[0]
                else:
                    raise ValueError("too many tests on same state")

            after = None
            mods = [node for (node, state) in nug.in_edges(state)
                    if mm_typing[node] == "mod"]
            for mod in mods:
                if after is None:
                    if len(nug.node[mod]["val"]) != 1:
                        raise ValueError("mods should have exactly one value")
                    after = list(nug.node[mod]["val"])[0]
                else:
                    raise ValueError("too many mods on same state")

            parent_components = [comp for comp in nug[state]
                                 if mm_typing[comp] in ["region", "residue",
                                                        "agent"]]
            if len(parent_components) != 1:
                raise ValueError("states should have one parent after unfold")
            site_name = "{}_{}".format(ag_typing[state],
                                       ag_typing[parent_components[0]])
            state_defs[state] = StateSite(site_name, before, after)

    agent_defs = {}
    for agent in nug.nodes():
        if mm_typing[agent] == "agent":
            sites_defs = []
            comps = _components_of_agent(nug, mm_typing, agent)
            for comp in comps:
                if mm_typing[comp] == "locus":
                    sites_defs.append(loci_defs[comp])
                elif mm_typing[comp] == "state":
                    sites_defs.append(state_defs[comp])
            agent_defs[agent] = Agent(ag_typing[agent], sites_defs)

    for syn in nug.nodes():
        if mm_typing[syn] == "syn":
            for (_, agent) in nug.out_edges(syn):
                agent_defs[agent].prefix = "+"

    for deg in nug.nodes():
        if mm_typing[deg] == "deg":
            for (_, agent) in nug.out_edges(deg):
                if agent_defs[agent].prefix == "+":
                    raise ValueError("syn and deg on same agent")
                agent_defs[agent].prefix = "-"

    return KappaRule(name, rate, agent_defs.values())


def to_kappa(hie, ag_id, mm_id, nug_list=None):
    """export an action graph to kappa code"""
    if nug_list is None or nug_list == []:
        ag_nodes = hie.node[ag_id].graph.nodes()
        nug_list = tree.graph_children(hie, ag_id)
    else:
        ag_nodes = set()
        for nug in nug_list:
            ag_nodes |= set(hie.get_typing(nug, ag_id).values())
    agents_list = _agents_decl(hie, ag_id, ag_nodes, mm_id)

    # build rules and variables definitions
    rules_list = []
    variables = []
    for nug in nug_list:
        unfolded_nuggets = unfold_nugget(hie, nug, ag_id, mm_id)
        for i, (graph, ag_typing, mm_typing) in enumerate(unfolded_nuggets):
            # ag_typing = hie.get_typing(nug, ag_id)
            # mm_typing = hie.get_typing(nug, mm_id)
            # graph = hie.node[nug].graph

            if i > 0:
                name = "{}_{}".format(hie.node[nug].attrs["name"], i)
            else:
                name = hie.node[nug].attrs["name"]

            rules_list.append(_rule_decl(ag_typing, mm_typing, graph, name,
                                         "rate:"+name))
            if "rate" in hie.node[nug].attrs.keys():
                value = hie.node[nug].attrs["rate"]
            else:
                value = "undefined"
            variables.append(Variable("rate:"+name, value))

    return str(KappaModel(agents_list, rules_list, variables))


def subgraph_by_types(graph, types, typing):
    """return the subgraph composed of nodes of right types"""
    right_nodes = [node for node in graph.nodes() if typing[node] in types]
    new_graph = graph.subgraph(right_nodes)
    inclusion_mono = {node: node for node in new_graph.nodes()}
    return (new_graph, inclusion_mono)


def compose_splices(hie, ag_id, mm_id, splices_list, new_rule_name):
    known_agents = []
    lhs = nx.DiGraph()
    ppp = nx.DiGraph()
    p_lhs = {}
    lhs_ag = {}
    action_graph = hie.node[ag_id].graph
    for spl in splices_list:
        mm_typing = hie.get_typing(spl, mm_id)
        ag_typing = hie.get_typing(spl, ag_id)
        splg = hie.node[spl].graph
        agents = [ag_typing[node] for node in splg
                  if mm_typing[node] == "agent"]
        if len(agents) != 1:
            raise ValueError("there must be exactly one agent in a splice")

        components = _components_of_agent(action_graph,
                                          hie.edge[ag_id][mm_id].mapping,
                                          agents[0])
        new_agent = action_graph.subgraph(components)
        newagent_ag = {n: n for n in new_agent.nodes()}

        # If no locus at all is present, we add them all to the variant
        if all(mm_typing[node] != "locus" for node in splg):
            ag_mm = hie.edge[ag_id][mm_id].mapping
            new_splg = copy.deepcopy(new_agent)
            for node in new_agent:
                if (ag_mm[node] != "locus" and
                        node not in [ag_typing[n] for n in splg]):
                    remove_node(new_splg, node)
            splg = new_splg
            ag_typing = {node: node for node in new_splg}
            mm_typing = compose_homomorphisms(ag_mm, ag_typing)

        if agents[0] not in known_agents:
            known_agents.append(agents[0])
            (new_lhs, lhs_newlhs, newagent_newlhs, newlhs_ag) =\
                pullback_pushout(lhs, new_agent, action_graph, lhs_ag,
                                 newagent_ag)

            ppp_newlhs = compose_homomorphisms(lhs_newlhs, p_lhs)
        else:
            new_lhs = lhs
            newlhs_ag = lhs_ag
            ppp_newlhs = p_lhs

        splg_newlhs = {}
        for node in splg:
            imgs = keys_by_value(newlhs_ag, ag_typing[node])
            if len(imgs) != 1:
                raise ValueError("node {} should have exactly one"
                                 " image in new_agent ({})".format(node, imgs))
            splg_newlhs[node] = imgs[0]
        (tmp, tmp_ppp, tmp_splg) = pullback(ppp, splg, new_lhs, ppp_newlhs,
                                            splg_newlhs)
        loci_nodes = [node for node in tmp.nodes()
                      if (compose_homomorphisms(mm_typing, tmp_splg)[node] ==
                          "locus")]
        loci_graph = tmp.subgraph(loci_nodes)
        loci_graph_id = {node: node for node in loci_graph.nodes()}
        locigraph_splg = compose_homomorphisms(tmp_splg, loci_graph_id)
        locigraph_ppp = compose_homomorphisms(tmp_ppp, loci_graph_id)
        (new_ppp, ppp_newppp, splg_newppp) = pushout(loci_graph, ppp, splg,
                                                     locigraph_ppp,
                                                     locigraph_splg)
        newppp_newlhs = {}
        # maybe test but conflict should not happen
        for node in ppp.nodes():
            newppp_newlhs[ppp_newppp[node]] = ppp_newlhs[node]
        for node in splg.nodes():
            newppp_newlhs[splg_newppp[node]] = splg_newlhs[node]

        ppp = new_ppp
        lhs = new_lhs
        p_lhs = newppp_newlhs
        lhs_ag = newlhs_ag

    lhs_mm_typing = compose_homomorphisms(
        hie.edge[ag_id][mm_id].mapping,
        lhs_ag)
    (lhs_loci, lhsloci_lhs) = subgraph_by_types(lhs, ["locus"], lhs_mm_typing)
    (final_ppp, _, _, finalppp_lhs) = pullback_pushout(lhs_loci, ppp, lhs,
                                                       lhsloci_lhs, p_lhs)
    rule = Rule(final_ppp, lhs, final_ppp, finalppp_lhs)
    rule_id = hie.unique_graph_id(new_rule_name)
    rule_name = tree.get_valid_name(hie, ag_id, new_rule_name)
    hie.add_rule(rule_id, rule, {"name": rule_name})
    hie.add_rule_typing(rule_id, ag_id, lhs_ag,
                        compose_homomorphisms(lhs_ag, finalppp_lhs))


# must be an action graph
def link_components(hie, g_id, comp1, comp2, kami_id):
    """ link two componenst together with brk, bnd"""
    typing = hie.edge[g_id][kami_id].mapping
    graph = hie.node[g_id].graph

    bnd_name = unique_node_id(graph, "bnd")
    typing[bnd_name] = "bnd"
    add_node(graph, bnd_name)

    brk_name = unique_node_id(graph, "brk")
    add_node(graph, brk_name)
    typing[brk_name] = "brk"

    loc1 = unique_node_id(graph, "loc")
    add_node(graph, loc1)
    typing[loc1] = "locus"
    loc2 = unique_node_id(graph, "loc")
    add_node(graph, loc2)
    typing[loc2] = "locus"

    add_edge(graph, loc1, comp1)
    add_edge(graph, loc1, bnd_name)
    add_edge(graph, loc1, brk_name)
    add_edge(graph, loc2, comp2)
    add_edge(graph, loc2, bnd_name)
    add_edge(graph, loc2, brk_name)

    if "positions" in hie.node[g_id].attrs:
        positions = hie.node[g_id].attrs["positions"]
        if comp1 in positions.keys():
            xpos1 = positions[comp1].get("x", 0)
            ypos1 = positions[comp1].get("y", 0)
        else:
            (xpos1, ypos1) = (0, 0)
        if comp2 in positions.keys():
            xpos2 = positions[comp2].get("x", 0)
            ypos2 = positions[comp2].get("y", 0)
        else:
            (xpos2, ypos2) = (0, 0)
        difx = xpos2 - xpos1
        dify = ypos2 - ypos1
        if (difx, dify) != (0, 0):
            distance = sqrt(difx*difx + dify*dify)
            vect = (difx/distance, dify/distance)
            positions[loc1] = {"x": xpos1+vect[0]*distance/3,
                               "y": ypos1+vect[1]*distance/3}
            positions[loc2] = {"x": xpos1+vect[0]*distance/3*2,
                               "y": ypos1+vect[1]*distance/3*2}
            positions[bnd_name] = {"x": (xpos1+vect[0]*distance/2 +
                                         vect[1]*60),
                                   "y": (ypos1+vect[1]*distance/2 -
                                         vect[0]*60)}
            positions[brk_name] = {"x": (xpos1+vect[0]*distance/2 -
                                         vect[1]*60),
                                   "y": (ypos1+vect[1]*distance/2 +
                                         vect[0]*60)}


# Hypothesis : only one agent per region
def unfold_nugget(hie, nug_id, ag_id, mm_id, test=False):
    """unfold a nugget with conflicts to create multiple nuggets"""
    nug_gr = copy.deepcopy(hie.node[nug_id].graph)
    mm_typing = copy.deepcopy(hie.get_typing(nug_id, mm_id))
    ag_typing = copy.deepcopy(hie.get_typing(nug_id, ag_id))

    # create one new locus for each linked agent, region or residue linked to
    #  a locus
    new_ports = {}  # new_port remember the loci/state it is created from
    old_ports = []
    non_comp_neighbors = {}
    for node in nug_gr.nodes():

        # move the state test to explicit "is_equal" nodes
        if mm_typing[node] == "state" and "val" in nug_gr.node[node]:
            for val in nug_gr.node[node]["val"]:
                id_prefix = "{}_{}".format(val, node)
                test_id = unique_node_id(nug_gr, id_prefix)
                add_node(nug_gr, test_id, {"val": val})
                mm_typing[test_id] = "is_equal"
                add_edge(nug_gr, test_id, node)

                # for testing
                if test:
                    ag = hie.node[ag_id].graph
                    ag_test_id = unique_node_id(ag, id_prefix)
                    add_node(ag, ag_test_id, {"val": val})
                    add_edge(ag, ag_test_id, ag_typing[node])
                    hie.edge[ag_id][mm_id].mapping[ag_test_id] = "is_equal"

                    real_nugget = hie.node[nug_id].graph
                    old_test_id = unique_node_id(real_nugget, id_prefix)
                    add_node(real_nugget, old_test_id, {"val": val})
                    add_edge(real_nugget, old_test_id, node)
                    hie.edge[nug_id][ag_id].mapping[old_test_id] = ag_test_id

        if mm_typing[node] in ["locus", "state"]:
            comp_neighbors = [comp for comp in nug_gr.successors(node)
                              if mm_typing[comp] in ["agent", "region",
                                                     "residue"]]
            other_neighbors = [other for other in (nug_gr.successors(node) +
                                                   nug_gr.predecessors(node))
                               if other not in comp_neighbors]
            old_ports.append(node)
            for comp in comp_neighbors:
                id_prefix = "{}_{}".format(node, comp)
                port_id = unique_node_id(nug_gr, id_prefix)
                add_node(nug_gr, port_id)
                mm_typing[port_id] = mm_typing[node]
                ag_typing[port_id] = ag_typing[node]
                new_ports[port_id] = node
                add_edge(nug_gr, port_id, comp)
                for other in other_neighbors:
                    if mm_typing[other] in ["mod", "is_equal"]:
                        add_edge(nug_gr, other, port_id)
                    else:
                        add_edge(nug_gr, port_id, other)
                non_comp_neighbors[port_id] = set(other_neighbors)

    # remove the old potentially shared between agents/region/residues loci
    for port in old_ports:
        remove_node(nug_gr, port)
        del mm_typing[port]
        del ag_typing[port]

    # associate the components nodes (agent,region, residue) to the ports
    components = {}
    for port in new_ports:
        components[port] = _agents_of_components(nug_gr, mm_typing, port)

    def _nonconflicting(port1, action_node1, port2, action_node2):
        typ1 = mm_typing[action_node1]
        typ2 = mm_typing[action_node2]
        if port1 == port2:
            if typ1 == typ2:
                return False
            if mm_typing[port1] == "state":
                return True
            if {typ1, typ2} & {"is_free", "is_bnd"}:
                return False
            different_loci = set(nug_gr.predecessors(action_node1)) !=\
                set(nug_gr.predecessors(action_node2))
            return different_loci

        elif action_node1 != action_node2:
            return True
        elif typ1 in ["mod", "is_equal", "is_free"]:
            return False
        else:
            return new_ports[port1] != new_ports[port2]

    def replace(node):
        """identify is_equal and mod nodes with same values"""
        if mm_typing[node] == "is_equal":
            return ("is_equal", str(nug_gr.node[node]["val"]))
        if mm_typing[node] == "mod":
            return ("mod", str(nug_gr.node[node]["val"]))
        return node

    # def reduce_subsets(set_list):
    #     def equivalent_subsets(set1, set2):
    #         set1 = {frozenset(map(replace, s)) for s in set1}
    #         set2 = {frozenset(map(replace, s)) for s in set2}
    #         return set1 == set2
    #     new_list = []
    #     for current_set in set_list:
    #         if all(not equivalent_subsets(existing_set, current_set)
    #                for existing_set in new_list):
    #             new_list.append(current_set)
    #     return new_list

    def reduce_subsets(set_list):
        return set_list

    # def subset_up_to_equivalence(s1, s2):
    #     return False
    def subset_up_to_equivalence(set1, set2):
        set1 = {frozenset(map(replace, s)) for s in set1}
        set2 = {frozenset(map(replace, s)) for s in set2}
        return set1.issubset(set2)

    def replace2(node):
        """identify is_equal and mod nodes with same values"""
        if mm_typing[node] == "is_equal":
            return ("is_equal", str(nug_gr.node[node]["val"]), frozenset(nug_gr.successors(node)))
        if mm_typing[node] == "mod":
            return ("mod", str(nug_gr.node[node]["val"]), frozenset(nug_gr.successors(node)))
        return node

    def _equivalent_actions(act1, act2, edge_list):
        l1 = [(port, replace(node)) for (port, node) in edge_list if node == act1]
        l2 = [(port, replace(node)) for (port, node) in edge_list if node == act2]
        return l1 == l2

    def _equivalent_edge(p1, a1, p2, a2):
        return p1 == p2 and replace2(a1) == replace2(a2)

    def _valid_subsets(memo_dict, set_list):
        """build non conflicting sets of sets of nodes"""
        # print(len(memo_dict))
        # print(set_list)
        if set_list == []:
            return [[]]
        # memo_key = frozenset([(port, replace(a_node))
        #                       for (port, a_node) in set_list])
        memo_key = frozenset(set_list)
        if memo_key in memo_dict:
            return memo_dict[memo_key]
        (port, a_node) = set_list[0]
        conflicting_edges = [(port2, a_node2) for (port2, a_node2) in set_list[1:]
                             if not _nonconflicting(port, a_node, port2, a_node2)]

        nonconflicting_sets =\
            [(port2, a_node2) for (port2, a_node2) in set_list[1:]
             if _nonconflicting(port, a_node, port2, a_node2)]
        # new_set_list = [(p2, n2) for (p2, n2) in set_list[1:]
        #                 if not _equivalent_edge(port, a_node, p2, n2)]
        equivalent_edges = [(p2, n2) for (p2, n2) in set_list
                            if p2 == port and _equivalent_actions(a_node, n2, set_list)]

        new_set_list = [(p2, n2) for (p2, n2) in set_list[1:]
                        if p2 != port or not _equivalent_actions(a_node, n2, set_list)]
         
        cond1 = (len([node for (_, node) in set_list[1:] if node == a_node]) == 0 and
                 all(replace(n2) == replace(a_node) for (p2, n2) in set_list[1:] if p2 == port))

        if nonconflicting_sets == new_set_list or cond1:
            # memo_dict[memo_key] =\
            #     reduce_subsets([sub + [components[port] | {a_node}]
            #                     for sub in _valid_subsets(memo_dict,
            #                                               nonconflicting_sets)])
            memo_dict[memo_key] =\
                [sub + [(port, a_node)]
                 for sub in _valid_subsets(memo_dict, nonconflicting_sets)]
            return memo_dict[memo_key]
        else:
            # memo_dict[memo_key] =\
            #     reduce_subsets(_valid_subsets(memo_dict, new_set_list) +
            #                    [sub + [components[port] | {a_node}]
            #                     for sub in _valid_subsets(memo_dict, nonconflicting_sets)])

            without_current_edge = _valid_subsets(memo_dict, new_set_list)

            # def conflict_with_current_edge(edge_list):
            #     return any(not _nonconflicting(port, a_node, p2, a_node2)
            #                for (p2, a_node2) in edge_list)

            def conflict_with_removed_edges(edge_list):
                return all(any(not _nonconflicting(p1, a_node1, p2, a_node2)
                           for (p2, a_node2) in edge_list) for (p1, a_node1) in equivalent_edges)

            # with_conflict = list(filter(conflict_with_current_edge, without_current_edge)) 
            with_conflict = list(filter(conflict_with_removed_edges, without_current_edge)) 
            memo_dict[memo_key] =\
                with_conflict +\
                [sub + [(port, a_node)]
                 for sub in _valid_subsets(memo_dict, nonconflicting_sets)]
            return memo_dict[memo_key]

    def _complete_subsets(set_list):
        print(set_list)
        return [components[port] | {a_node} for (port, a_node) in set_list]

    def _remove_uncomplete_actions(set_list):
        """remove actions and test which are not connected to enough
         components"""
        labels = {node: 0 for node in nug_gr.nodes()}
        for nodes in set_list:
            for node in nodes:
                labels[node] += 1

        to_remove = set()
        for node in nug_gr.nodes():
            if (mm_typing[node] in ["bnd", "brk", "is_bnd"] and
                    labels[node] < 2):
                to_remove.add(node)
            if (mm_typing[node] in ["is_free", "mod", "is_equal"] and
                    labels[node] < 1):
                to_remove.add(node)

        return [nodes for nodes in set_list
                if not nodes & to_remove]

    port_action_list = [(port, a_node)
                        for (port, a_nodes) in non_comp_neighbors.items()
                        for a_node in a_nodes]

    # build globally non conflicting subsets and remove the uncomplete actions
    memo_dict = {}
    valid_ncss = {frozenset(map(frozenset,
                                _remove_uncomplete_actions(_complete_subsets(set_list))))
                  for set_list in _valid_subsets(memo_dict, port_action_list)}
    print("valid_ended")
    print(len(valid_ncss))
    # print(valid_ncss)
    # remove the nuggets that are included in another one
    # maximal_valid_ncss = {ncss for ncss in valid_ncss
    #                       if all(ncss == other_ncss or
    #                              #not ncss.issubset(other_ncss)
    #                              not subset_up_to_equivalence(ncss, other_ncss)
    #                              for other_ncss in valid_ncss)}
    maximal_valid_ncss = valid_ncss
    # add the nodes that where not considered at all
    # because they are not connected to a locus or state
    nodes_with_ports = set.union(
        set.union(*(list(non_comp_neighbors.values())+[set()])),
        set.union(*(list(components.values())+[set()])))

    nodes_without_ports = set(nug_gr.nodes()) - nodes_with_ports

    # build the nuggets and add them to the hierarchy
    # as children of the old one for testing
    def _graph_of_ncs(ncs):
        sub_graphs = [(subgraph(nug_gr, nodes), {node: node for node in nodes})
                      for nodes in ncs]
        sub_graphs.append((subgraph(nug_gr, nodes_without_ports),
                           {node: node for node in nodes_without_ports}))
        return multi_pullback_pushout(nug_gr, sub_graphs)

    valid_graphs = map(_graph_of_ncs, maximal_valid_ncss)
    new_nuggets = []
    for (new_nugget, new_typing) in valid_graphs:
        if test:
            typing_by_old_nugget = {}
            for node in new_nugget.nodes():
                if new_typing[node] in hie.node[nug_id].graph.nodes():
                    typing_by_old_nugget[node] = new_typing[node]
                else:
                    typing_by_old_nugget[node] = new_ports[new_typing[node]]
            new_nuggets.append((new_nugget, typing_by_old_nugget))
        else:
            new_ag_typing = compose_homomorphisms(ag_typing, new_typing)
            new_mm_typing = compose_homomorphisms(mm_typing, new_typing)
            new_nuggets.append((new_nugget, new_ag_typing, new_mm_typing))
    return new_nuggets


def unfold_locus(hie, ag_id, mm_id, locus, suffix=None):
    ag_gr = hie.node[ag_id].graph
    ag_mm = hie.get_typing(ag_id, mm_id)
    nuggets = [nug for nug in tree.get_children_id_by_node(hie, ag_id, locus)
               if hie.node[nug].attrs["type"] == "nugget"]

    # Do not merge nodes that are Not valid
    # As they are removed from the botom graph before the pushout
    not_valid = [locus]+[node for node in ag_gr[locus]
                         if ag_mm[node] not in ["region", "agent"]]

    def valid_pullback_node(a, b, c, d, a_b, a_c, b_d, c_d, n):
        a_d = union_mappings(compose_homomorphisms(b_d, a_b),
                             compose_homomorphisms(c_d, a_c))
        return n not in a_d or a_d[n] not in not_valid

    (pp, pp_ag) = multi_pullback_pushout(
        ag_gr,
        [(hie.node[nug].graph, hie.get_typing(nug, ag_id)) for nug in nuggets],
        valid_pullback_node)

    adj_nodes = [suc for suc in ag_gr.successors(locus)] + [locus]

    lhs = ag_gr.subgraph(adj_nodes)
    new_pp = pp.subgraph(reverse_image(pp_ag, adj_nodes))

    # add regions and agents that do not appear in any nuggets to the
    # preserved part, so we can remove edges from the locus to them
    to_add = {suc for suc in ag_gr.successors(locus)
              if ag_mm[suc] in ["region", "agent"]} - set(pp_ag.values())
    for node in to_add:
        node_id = unique_node_id(new_pp, node)
        add_node(new_pp, node_id)
        pp_ag[node_id] = node

    newpp_lhs = restrict_mapping(new_pp.nodes(), pp_ag)

    # merge loci that have a shared successor component
    def common_comp(loc1, loc2):
        comps1 = {c for c in new_pp.successors(loc1)
                  if ag_mm[pp_ag[c]] in ["region", "agent"]}
        comps2 = {c for c in new_pp.successors(loc2)
                  if ag_mm[pp_ag[c]] in ["region", "agent"]}
        return comps1 & comps2
    # compute equivalence classes of loci
    loci = [pploc for pploc in new_pp
            if pp_ag[pploc] == locus]
    classes = [{pploc} for pploc in loci]
    partial_eq = [{loc1, loc2} for (loc1, loc2) in combinations(loci, 2)
                  if loc1 != loc2 and common_comp(loc1, loc2)]
    for eq in partial_eq:
        classes = merge_classes(eq, classes)

    # compute equivalence classes of action nodes
    def equiv_acts(act1, act2):
        def equiv_loci(locs1, locs2):
            if len(locs1) != 1:
                raise ValueError("should have exactly one locus next to action")
            if len(locs2) != 1:
                raise ValueError("should have exactly one locus next to action")
            return any(set(locs1) | set(locs2) <= cl for cl in classes)
        return (pp_ag[act1] == pp_ag[act2] and
                equiv_loci(new_pp.predecessors(act1),
                           new_pp.predecessors(act2)))
    actions = [act for act in new_pp
               if ag_mm[pp_ag[act]] in ["is_bnd", "bnd", "is_free", "brk"]]
    action_classes = [{act} for act in actions]
    for (act1, act2) in combinations(actions, 2):
        if equiv_acts(act1, act2):
            action_classes = merge_classes({act1, act2}, action_classes)

    eq_gr = nx.DiGraph()
    newpp_eq = {}
    for i, cl in enumerate(classes + action_classes):
        eq_gr.add_node(i)
        for node in cl:
            newpp_eq[node] = i

    (new_pp, newpp_lhs) = pushout_from_partial_mapping(new_pp,
                                                       eq_gr,
                                                       newpp_eq,
                                                       newpp_lhs,
                                                       {})

    lhs_ag = id_of(lhs)
    rhs = copy.deepcopy(new_pp)
    rule = Rule(new_pp, lhs, rhs, newpp_lhs)
    if suffix is None:
        apply_rule_on_parent_inplace(hie, ag_id, rule, lhs_ag)
    else:
        raise ValueError("TODO? rewrite not in place")

    # rule_id = hie.unique_graph_id("tmp_rule")
    # rule_name = tree.get_valid_child_name(hie, ag_id, rule_id)
    # hie.add_rule(rule_id, rule, {"type": "rule", "name": rule_name})
    # hie.add_rule_typing(rule_id, ag_id, lhs_ag)

    # # remove old hierarchy
    # new_names = tree.rewrite_parent(hie, rule_id, ag_id, suffix)
    # ag_name = hie.node[ag_id].attrs["name"]
    # hie.delete_all_children(ag_id)
    # hie.remove_node(new_names[rule_id])
    # hie.node[new_names[ag_id]].attrs["name"] = ag_name


def remove_conflict(hie, ag_id, mm_id, locus, suffix=None):
    ag_gr = hie.node[ag_id].graph
    ag_mm = hie.get_typing(ag_id, mm_id)
    nuggets = [nug for nug in tree.get_children_id_by_node(hie, ag_id, locus)
               if hie.node[nug].attrs["type"] == "nugget"]

    # Do not merge nodes that are Not valid
    # As they are removed from the botom graph before the pushout
    not_valid = [locus]

    def valid_pullback_node(a, b, c, d, a_b, a_c, b_d, c_d, n):
        a_d = union_mappings(compose_homomorphisms(b_d, a_b),
                             compose_homomorphisms(c_d, a_c))
        return n not in a_d or a_d[n] not in not_valid

    (pp, pp_ag) = multi_pullback_pushout(
        ag_gr,
        [(hie.node[nug].graph, hie.get_typing(nug, ag_id)) for nug in nuggets],
        valid_pullback_node)

    adj_nodes = [suc for suc in ag_gr.successors(locus)] + [locus]

    lhs = ag_gr.subgraph(adj_nodes)
    new_pp = pp.subgraph(reverse_image(pp_ag, adj_nodes))

    # add regions and agents that do not appear in any nuggets to the
    # preserved part, so we can remove edges from the locus to them
    to_add = {suc for suc in ag_gr.successors(locus)
              if ag_mm[suc] in ["region", "agent"]} - set(pp_ag.values())
    for node in to_add:
        node_id = unique_node_id(new_pp, node)
        add_node(new_pp, node_id)
        pp_ag[node_id] = node

    newpp_lhs = restrict_mapping(new_pp.nodes(), pp_ag)

    # merge loci from preserved part that arr linked to the same other loci
    def linked_to(loc):
        """loc being a locus from new_pp, returns the ag loci linked to loc """
        adj_acts = {pp_ag[act] for act in new_pp.successors(loc)
                    if ag_mm[pp_ag[act]] not in ["region", "agent"]}
        return {other_loc for act in adj_acts
                for other_loc in ag_gr.predecessors(act)
                if other_loc != locus}

    # compute equivalence classes of loci
    loci = [pploc for pploc in new_pp
            if pp_ag[pploc] == locus]
    classes = [{pploc} for pploc in loci]
    partial_eq = [{loc1, loc2}
                  for loc1 in loci
                  for loc2 in loci
                  if loc1 != loc2 and linked_to(loc1) & linked_to(loc2)]
    for eq in partial_eq:
        classes = merge_classes(eq, classes)

    eq_gr = nx.DiGraph()
    newpp_eq = {}
    for i, cl in enumerate(classes):
        eq_gr.add_node(i)
        for node in cl:
            newpp_eq[node] = i

    (new_pp, newpp_lhs) = pushout_from_partial_mapping(new_pp,
                                                       eq_gr,
                                                       newpp_eq,
                                                       newpp_lhs,
                                                       {})

    lhs_ag = id_of(lhs)
    rhs = copy.deepcopy(new_pp)
    rule = Rule(new_pp, lhs, rhs, newpp_lhs)
    if suffix is None:
        apply_rule_on_parent_inplace(hie, ag_id, rule, lhs_ag)
    else:
        raise ValueError("TODO? rewrite not in place")


def apply_rule_on_parent_inplace(hie, ag_id, rule, mapping):
    rule_id = hie.unique_graph_id("tmp_rule")
    rule_name = tree.get_valid_child_name(hie, ag_id, rule_id)
    hie.add_rule(rule_id, rule, {"type": "rule", "name": rule_name})
    hie.add_rule_typing(rule_id, ag_id, mapping)

    # remove old hierarchy
    new_names = tree.rewrite_parent(hie, rule_id, ag_id, "tmp_suffix")
    ag_name = hie.node[ag_id].attrs["name"]
    hie.delete_all_children(ag_id)
    hie.remove_node(new_names[rule_id])
    hie.node[new_names[ag_id]].attrs["name"] = ag_name


# TODO? Add typing from nuggets which are not typing the action graph
# precondition: the partial typing is consistent with types
def add_nugget_to_action_graph(hie, nug_id, ag_id, partial_typing, move=True):
    nug_gr = hie.node[nug_id].graph
    ag_gr = hie.node[ag_id].graph
    shared_typings = [typing for typing in hie.successors(ag_id)
                      if typing in hie.successors(nug_id)]
    # necessary_typings = [typing for typing in hie.successors(ag_id)
    #                      if hie.edge[ag_id][typing].total]
    necessary_typings = [typing for typing in hie.successors(ag_id)]
    for typing in necessary_typings:
        for node in nug_gr:
            if node not in partial_typing:
                mapping = hie.get_typing(nug_id, typing)
                if mapping is None or node not in mapping:
                    raise ValueError("Node {} is not typed by {}"
                                     .format(node, typing))

    for node in nug_gr:
        if node not in partial_typing:
            new_node = prim.add_node_new_id(ag_gr, node, copy.deepcopy(nug_gr.node[node]))
            partial_typing[node] = new_node
            for typing in necessary_typings:
                mapping = hie.get_typing(nug_id, typing)
                hie.edge[ag_id][typing].mapping[new_node] = mapping[node]

    for (source, target) in nug_gr.edges():
        prim.add_edge(ag_gr, partial_typing[source], partial_typing[target])

    if move:
        for typing in hie.successors(nug_id):
            hie.remove_edge(nug_id, typing)
        hie.add_typing(nug_id, ag_id, partial_typing, total=True)
        hie.node[nug_id].attrs["type"] = "nugget"


