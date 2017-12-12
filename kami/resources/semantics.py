"""Semantic AG."""
import networkx as nx

from regraph.primitives import (add_nodes_from,
                                add_edges_from)


action_graph = nx.DiGraph()
add_nodes_from(action_graph, [
    "protein_kinase",
    ("activity", {"activity": {True}}),
    ("phospho", {"value": {True}}),
    ("phosphorylation_state", {"phosphorylation": {True, False}}),
    ("phospho_target_residue", {"aa": {"S", "T", "Y"}}),
    "phosphatase",
    ("dephospho", {"value": {False}}),
    "pY_motif",
    "pY_locus",
    ("sh2_domain_pY_bnd", {"direct": True}),
    "sh2_domain_locus",
    "sh2_domain",
])

add_edges_from(action_graph, [
    ("activity", "protein_kinase"),
    ("protein_kinase", "phospho"),
    ("phospho", "phosphorylation_state"),
    ("phosphorylation_state", "phospho_target_residue"),
    ("activity", "phosphatase"),
    ("phosphatase", "dephospho"),
    ("dephospho", "phosphorylation_state"),
    ("phospho_target_residue", "pY_motif"),
    ("pY_motif", "pY_locus"),
    ("pY_locus", "sh2_domain_pY_bnd"),
    ("sh2_domain_locus", "sh2_domain_pY_bnd"),
    ("sh2_domain", "sh2_domain_locus"),
])

sag_kami_typing = {
    "protein_kinase": "region",
    "activity": "state",
    "phospho": "mod",
    "phosphorylation_state": "state",
    "phospho_target_residue": "residue",
    "phosphatase": "region",
    "dephospho": "mod",
    "pY_motif": "region",
    "pY_locus": "locus",
    "sh2_domain_pY_bnd": "bnd",
    "sh2_domain_locus": "locus",
    "sh2_domain": "region",
}

# Phosphorylation semantic nugget
phosphorylation = nx.DiGraph()
add_nodes_from(
    phosphorylation,
    ["protein_kinase",
     ("protein_kinase_activity", {"activity": {True}}),
     ("phospho", {"value": {True}}),
     ("target_state", {"phosphorylation": {False}}),
     ("target_residue", {"aa": {"S", "T", "Y"}})]
)

add_edges_from(
    phosphorylation,
    [("protein_kinase_activity", "protein_kinase"),
     ("protein_kinase", "phospho"),
     ("phospho", "target_state"),
     ("target_state", "target_residue")]
)

phosphorylation_kami_typing = {
    "protein_kinase": "region",
    "protein_kinase_activity": "state",
    "phospho": "mod",
    "target_state": "state",
    "target_residue": "residue"
}

phosphorylation_semantic_AG = {
    "protein_kinase": "protein_kinase",
    "protein_kinase_activity": "activity",
    "phospho": "phospho",
    "target_state": "phosphorylation_state",
    "target_residue": "phospho_target_residue"
}

# Dephosphorylation semantic nugget
dephosphorylation = nx.DiGraph()
add_nodes_from(
    dephosphorylation,
    [
        "phosphatase",
        ("phosphatase_activity", {"activity": True}),
        ("dephospho", {"value": False}),
        ("target_state", {"phosphorylation": {True}}),
        ("target_residue", {"aa": {"S", "T", "Y"}})
    ]
)

add_edges_from(
    dephosphorylation,
    [
        ("phosphatase_activity", "phosphatase"),
        ("phosphatase", "dephospho"),
        ("dephospho", "target_state"),
        ("target_state", "target_residue")
    ]
)

dephosphorylation_kami_typing = {
    "phosphatase": "region",
    "phosphatase_activity": "state",
    "dephospho": "mod",
    "target_state": "state",
    "target_residue": "residue"
}

dephosphorylation_semantic_AG = {
    "phosphatase": "phosphatase",
    "phosphatase_activity": "activity",
    "dephospho": "dephospho",
    "target_state": "phosphorylation_state",
    "target_residue": "phospho_target_residue"
}

# SH2 - pY binding semantic nugget
sh2_pY_binding = nx.DiGraph()
add_nodes_from(
    sh2_pY_binding,
    [
        "sh2_domain",
        "sh2_domain_locus",
        ("sh2_domain_pY_bnd", {"direct": True}),
        "pY_locus",
        "pY_motif",
        ("pY_residue", {"aa": "Y"}),
        ("phosphorylation", {"phosphorylation": True})
    ]
)

add_edges_from(
    sh2_pY_binding,
    [("sh2_domain", "sh2_domain_locus"),
     ("sh2_domain_locus", "sh2_domain_pY_bnd"),
     ("pY_locus", "sh2_domain_pY_bnd"),
     ("pY_motif", "pY_locus"),
     ("pY_residue", "pY_motif"),
     ("phosphorylation", "pY_residue")]
)

sh2_pY_kami_typing = {
    "sh2_domain": "region",
    "sh2_domain_locus": "locus",
    "sh2_domain_pY_bnd": "bnd",
    "pY_locus": "locus",
    "pY_motif": "region",
    "pY_residue": "residue",
    "phosphorylation": "state",
}

sh2_pY_semantic_AG = {
    "sh2_domain": "sh2_domain",
    "sh2_domain_locus": "sh2_domain_locus",
    "sh2_domain_pY_bnd": "sh2_domain_pY_bnd",
    "pY_locus": "pY_locus",
    "pY_motif": "pY_motif",
    "pY_residue": "phospho_target_residue",
    "phosphorylation": "phosphorylation_state"
}
