"""Build graph by composing subgraphs"""

from regraph.library.category_op import (pullback, pushout,
                                         pullback_complement,
                                         compose_homomorphisms,
                                         compose_chain_homomorphisms,
                                         pullback_pushout)
from regraph.library.primitives import find_match
from pyparsing import Word, alphas
import networkx as nx


class AlgForm(object):
    """abstract formula"""


class Concat(AlgForm):
    """concatenate graphs"""
    def __init__(self, forms):
        self.forms = forms

    def eval(self):
        if self.forms == []:
            return []
        current_patterns = self.forms[0].eval()
        for next_patterns in self.forms[1:]:
            current_patterns = concat_sets(current_patterns,
                                           next_patterns.eval())
        return current_patterns


class Pattern(AlgForm):
    """composable patterns"""

    def __init__(self, name, graph, in_pat, in_morph, out_pat, out_morph,
                 typings, typing_graphs):
        self.name = name
        self.graph = graph
        self.in_pat = in_pat
        self.out_pat = out_pat
        self.in_morph = in_morph
        self.out_morph = out_morph
        self.typings = typings
        self.typing_graphs = typing_graphs

    def eval(self):
        return [self]


def concat(p1, p2):
    p2_in_typing = {typ_gr: compose_homomorphisms(typ_map, p2.in_morph)
                    for (typ_gr, typ_map) in p2.typings.items()}
    p1_out_typing = {typ_gr: compose_homomorphisms(typ_map, p1.out_morph)
                     for (typ_gr, typ_map) in p1.typings.items()}
    matchings = find_match(p2.in_pat, p1.out_pat, p2_in_typing, p1_out_typing,
                           p1.typing_graphs, decr_types=True)
    new_patterns = []
    for i, matching in enumerate(matchings):

        out1_p2 = compose_homomorphisms(p2.in_morph, matching)
        (p12, p1_p12, p2_p12) = pushout(p1.out_pat, p1.graph, p2.graph,
                                        p1.out_morph, out1_p2)
        in1_p12 = compose_homomorphisms(p1_p12, p1.in_morph)
        in2_p12 = compose_homomorphisms(p2_p12, p2.in_morph)
        out2_p12 = compose_homomorphisms(p2_p12, p2.out_morph)
        new_typings = {}
        for (typ_id, typ_map) in p1.typings.items():
            if typ_id not in new_typings.keys():
                new_typings[typ_id] = {}
            for node in p1.graph.nodes():
                if node in typ_map.keys():
                    new_typings[typ_id][p1_p12[node]] = typ_map[node]
        for (typ_id, typ_map) in p2.typings.items():
            if typ_id not in new_typings.keys():
                new_typings[typ_id] = {}
            for node in p2.graph.nodes():
                if node in typ_map.keys():
                    new_typings[typ_id][p2_p12[node]] = typ_map[node]
        (new_in, _, _, newin_p12) = pullback_pushout(p1.in_pat, p2.in_pat,
                                                     p12, in1_p12, in2_p12)
        new_pattern = Pattern(f"{p1.name}_{p2.name}_{i}",
                              p12, new_in, newin_p12, p2.out_morph, out2_p12,
                              new_typings,
                              p1.typing_graphs.update(p2.typing_graphs))
        new_patterns.append(new_pattern)
    return new_patterns


def concat_sets(s1, s2):
    sets = [concat(p1, p2) for p1 in s1 for p2 in s2]
    return [pat for pat_list in sets for pat in pat_list]




def concat_test(g1, g2):
    """"""
    g1_out_nodes = [n for n in g1.nodes() if n.startswith("out")]
    g2_in_nodes = [n for n in g2.nodes() if n.startswith("in")]
    pout1 = g1.subgraph(g1_out_nodes)
    mout1 = {n: n for n in g1_out_nodes}
    pin2 = g2.subgraph(g2_in_nodes)
    min2 = {n: n for n in g2_in_nodes}
    pat1 = Pattern("pat1", g1, nx.DiGraph(), {}, pout1, mout1)
    pat2 = Pattern("pat2", g2, pin2, min2, nx.DiGraph, {})
    return concat(pat1, pat2, {}, {}, {})


def id_to_pattern(hie, g_id):
    graph = hie.node[g_id].graph
    out_nodes = [n for n in graph.nodes() if n.startswith("out")]
    in_nodes = [n for n in graph.nodes() if n.startswith("in")]
    pout = graph.subgraph(out_nodes)
    pin = graph.subgraph(in_nodes)
    mout = {n: n for n in out_nodes}
    min = {n: n for n in in_nodes}
    typings = {typ_id: hie.edge[g_id][typ_id].mapping
               for typ_id in hie.successors(g_id)}
    typing_graphs = {typ_id: hie.node[typ_id].graph
                     for typ_id in hie.successors(g_id)}
    return Pattern(g_id, graph, pin, min, pout, mout, typings, typing_graphs)


def create_compositions(hie, compositions, g_id):
    if "compositions" not in hie.node[g_id].attrs.keys():
        raise ValueError(f"no compositions field in graph {g_id}")
    known_comps_list = hie.node[g_id].attrs["compositions"]
    known_comps = {c["id"]: c["formula"] for c in known_comps_list}

    all_new_ids = []
    for compo in compositions:
        generated_patterns = _create_composition_tree(hie, known_comps[compo])
        for pat in generated_patterns:
            new_id = hie.unique_graph_id(pat.name)
            hie.add_graph(new_id, pat.graph, {"name": new_id})
            for typing_graph in pat.typings:
                hie.add_typing(new_id, typing_graph, pat.typings[typing_graph])
            all_new_ids.append(new_id)
    return all_new_ids


# TODO: use name instead of ids
def _create_composition(hie, compo):
    pattern_lists = [[id_to_pattern(hie, pat)] for pat in eval(compo)]
    if len(pattern_lists) == 0:
        return []
    current_patterns = pattern_lists[0]
    print(pattern_lists)
    for next_patterns in pattern_lists[1:]:
        print([pat.name for pat in current_patterns])
        current_patterns = concat_sets(current_patterns, next_patterns)
    return current_patterns


def comp_to_concat_tree(hie, comp):
    if type(comp) is list:
        comps = [comp_to_concat_tree(hie, c) for c in comp]
        return Concat(comps)
    elif type(comp) is str:
        return id_to_pattern(hie, comp)


def _create_composition_tree(hie, compo):
    formula = comp_to_concat_tree(hie, eval(compo))
    return formula.eval()





