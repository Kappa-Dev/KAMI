"""Semantic AG."""
import networkx as nx

from regraph.primitives import (add_nodes_from,
                                add_edges_from)


semantic_action_graph = nx.DiGraph()
add_nodes_from(semantic_action_graph, [
    "kinase",
    ("kinase_activity", {"activity": {True}}),
    ("phospho", {"value": {True}}),
    ("target_state", {"phosphorylation": {False}}),
    ("target_residue", {"aa": {"S", "T", "Y"}})
])

add_edges_from(semantic_action_graph, [
    ("kinase_activity", "kinase"),
    ("kinase", "phospho"),
    ("phospho", "target_state"),
    ("target_state", "target_residue")
])

kami_typing = {
    "kinase": "region",
    "kinase_activity": "state",
    "phospho": "mod",
    "target_state": "state",
    "target_residue": "residue"
}
