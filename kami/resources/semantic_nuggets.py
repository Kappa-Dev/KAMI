"""Collection of semantic nuggets."""
import networkx as nx


phosphorylation = nx.DiGraph()
phosphorylation.add_nodes_from([
    "kinase",
    ("kinase_activity", {"activity": {True}}),
    ("phospho", {"value": {True}}),
    ("target_state", {"phosphorylation": {False}}),
    ("target_residue", {"aa": {"S", "T", "Y"}})
])

phosphorylation.add_edges_from([
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

phosphorylation_semantic_AG = {
    "kinase": "kinase",
    "kinase_activity": "kinase_activity",
    "phospho": "phospho",
    "target_state": "target_state",
    "target_residue": "target_residue"
}
