"""Semantic AG."""
import networkx as nx


semantic_action_graph = nx.DiGraph()
semantic_action_graph.add_nodes_from([
    "kinase",
    ("kinase_activity", {"activity": {True}}),
    ("phospho", {"value": {True}}),
    ("target_state", {"phosphorylation": {False}}),
    ("target_residue", {"aa": {"S", "T", "Y"}})
])

semantic_action_graph.add_edges_from([
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
