import regraph.library.tree as tree

from regraph.library.category_op import (pullback, pushout,
                                         compose_homomorphisms,
                                         pullback_pushout)
from regraph.library.utils import keys_by_value
from regraph.library.rules import Rule
from regraph.library.primitives import (unique_node_id, add_node, add_edge)
from math import sqrt
import networkx as nx
""" represent a kappa model as python """


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


def _agent_decl(action_graph, typing, agent):
    components = _components_of_agent(action_graph, typing, agent)
    sites_decl = []
    for comp in components:
        if typing[comp] == "locus":
            sites_decl.append(SiteDecl(comp))
        if typing[comp] == "state":
            sites_decl.append(SiteDecl(comp, action_graph.node[comp]["val"]))

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
    print("name", name)
    print("nodes", nug.nodes())
    print("mm_typing", mm_typing)

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
            loci_defs[loc] = BindingSite(ag_typing[loc], before, after)

    state_defs = {}
    for state in nug.nodes():
        if mm_typing[state] == "state":
            if len(nug.node[state]["val"]) != 1:
                raise ValueError("states should have exactly one value"
                                 " before exporting to kappa")
            before = list(nug.node[state]["val"])[0]
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
            state_defs[state] = StateSite(ag_typing[state], before, after)

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
                if agent_defs[agent].prefic == "+":
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
        ag_typing = hie.get_typing(nug, ag_id)
        mm_typing = hie.get_typing(nug, mm_id)
        graph = hie.node[nug].graph
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


def compose_splices(hie, ag_id, mm_id, splices_list):
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
        agents = [ag_typing[node] for node in splg.nodes()
                  if mm_typing[node] == "agent"]
        if len(agents) != 1:
            raise ValueError("there must be exactly one agent in a splice")
        if agents[0] not in known_agents:
            known_agents.append(agents[0])
            components = _components_of_agent(action_graph,
                                              hie.edge[ag_id][mm_id].mapping,
                                              agents[0])
            new_agent = action_graph.subgraph(components)
            newagent_ag = {n: n for n in new_agent.nodes()}
            # (tmp, tmp_lhs, tmp_newagent) =\
            #     pullback(lhs, new_agent, action_graph, lhs_ag, newagent_ag)
            # (new_lhs, lhs_newlhs, newagent_newlhs) =\
            #     pushout(tmp, lhs, new_agent, tmp_lhs, tmp_newagent)
            # newlhs_ag = {}
            # for node in lhs.nodes():
            #     newlhs_ag[lhs_newlhs[node]] = lhs_ag[node]
            # for node in new_agent.nodes():
            #     newlhs_ag[newagent_newlhs[node]] = newagent_ag[node]
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
                                 " image in new_agent".format(node))
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
    rule_id = hie.unique_graph_id("big_rule")
    rule_name = tree.get_valid_name(hie, ag_id, "big_rule")
    hie.add_rule(rule_id, rule, {"name": rule_name})
    hie.add_rule_typing(rule_id, ag_id, lhs_ag,
                        compose_homomorphisms(lhs_ag, finalppp_lhs),
                        ignore_attrs=True)


# must be an action graph
def link_components(hie, g_id, comp1, comp2):
    """ link two componenst together with brk, bnd"""
    typing = hie.edge[g_id]["kami"].mapping
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

    if "positions" in hie.node[g_id].attrs.keys():
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


def unfold_nugget(hie, nug_id, ag_id, mm_id):
    nug_gr = hie.node[nug_id].graph
    mm_typing = hie.get_typing(nug_id, mm_id)
    conected_components = nx.weakly_connected_components_subgraphs()

