"""Semantic AG."""
import networkx as nx

from regraph.primitives import (add_nodes_from,
                                add_edges_from)


semantic_action_graph = nx.DiGraph()
add_nodes_from(semantic_action_graph, [
    "kinase",
    ("activity", {"activity": {True}}),
    ("phospho", {"value": {True}}),
    ("phosphorylation_state", {"phosphorylation": {True, False}}),
    ("phospho_target_residue", {"aa": {"S", "T", "Y"}}),
    "phosphatase",
    ("dephospho", {"value": {False}}),
    "pY_motif",
    "pY_locus",
    ("sh2_pY_bnd", {"direct": True}),
    "sh2_locus",
    "sh2",
])

add_edges_from(semantic_action_graph, [
    ("activity", "kinase"),
    ("kinase", "phospho"),
    ("phospho", "phosphorylation_state"),
    ("phosphorylation_state", "phospho_target_residue"),
    ("activity", "phosphatase"),
    ("phosphatase", "dephospho"),
    ("dephospho", "phosphorylation_state"),
    ("phospho_target_residue", "pY_motif"),
    ("pY_motif", "pY_locus"),
    ("pY_locus", "sh2_pY_bnd"),
    ("sh2_locus", "sh2_pY_bnd"),
    ("sh2", "sh2_locus"),
])

kami_typing = {
    "kinase": "region",
    "activity": "state",
    "phospho": "mod",
    "phosphorylation_state": "state",
    "phospho_target_residue": "residue",
    "phosphatase": "region",
    "dephospho": "mod",
    "pY_motif": "region",
    "pY_locus": "locus",
    "sh2_pY_bnd": "bnd",
    "sh2_locus": "locus",
    "sh2": "region",
}
