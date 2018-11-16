"""Semantic AG."""
import networkx as nx


action_graph = {
    "nodes": [
        "protein_kinase",
        ("protein_kinase_activity", {"name": {"activity"}, "test": {True}}),
        ("phospho", {"value": {True}}),
        ("phospho_state", {"name": {"phosphorylation"}, "test": {True, False}}),
        ("phospho_target_residue", {"aa": {"S", "T", "Y"}, "test": {True}}),
        "phosphatase",
        ("phosphatase_activity", {"name": {"activity"}, "test": {True}}),
        ("dephospho", {"value": {False}}),
        "pY_site",
        ("sh2_domain_pY_bnd", {"type": "do", "test": True}),
        "sh2_domain",
    ],
    "edges": [
        ("protein_kinase_activity", "protein_kinase"),
        ("protein_kinase", "phospho"),
        ("phospho", "phospho_state"),
        ("phospho_state", "phospho_target_residue"),
        ("phosphatase_activity", "phosphatase"),
        ("phosphatase", "dephospho"),
        ("dephospho", "phospho_state"),
        ("phospho_target_residue", "pY_site"),
        ("pY_site", "sh2_domain_pY_bnd"),
        ("sh2_domain", "sh2_domain_pY_bnd"),
    ]
}

sag_meta_typing = {
    "protein_kinase": "region",
    "protein_kinase_activity": "state",
    "phospho": "mod",
    "phospho_state": "state",
    "phospho_target_residue": "residue",
    "phosphatase": "region",
    "phosphatase_activity": "state",
    "protein_kinase_activity": "state",
    "dephospho": "mod",
    "pY_site": "site",
    "sh2_domain_pY_bnd": "bnd",
    "sh2_domain": "region",
}

# Phosphorylation semantic nugget
phosphorylation = {
    "nodes":
        ["protein_kinase",
         ("protein_kinase_activity", {"name": {"activity"}, "test": {True}}),
         ("phospho", {"value": {True}}),
         ("phospho_state", {"name": {"phosphorylation"}, "test": {False}}),
         ("phospho_target_residue", {"aa": {"S", "T", "Y"}, "test": {True}})],
    "edges":
        [("protein_kinase_activity", "protein_kinase"),
         ("protein_kinase", "phospho"),
         ("phospho", "phospho_state"),
         ("phospho_state", "phospho_target_residue")]
}

phosphorylation_meta_typing = {
    "protein_kinase": "region",
    "protein_kinase_activity": "state",
    "phospho": "mod",
    "phospho_state": "state",
    "phospho_target_residue": "residue"
}

phosphorylation_semantic_AG = {
    "protein_kinase": "protein_kinase",
    "protein_kinase_activity": "protein_kinase_activity",
    "phospho": "phospho",
    "phospho_state": "phospho_state",
    "phospho_target_residue": "phospho_target_residue"
}

# Dephosphorylation semantic nugget
dephosphorylation = {
    "nodes": [
        "phosphatase",
        ("phosphatase_activity", {"name": {"activity"}, "test": {True}}),
        ("dephospho", {"value": False}),
        ("phospho_state", {"name": {"phosphorylation"}, "test": {True}}),
        ("phospho_target_residue", {"aa": {"S", "T", "Y"}, "test": {True}})
    ],
    "edges": [
        ("phosphatase_activity", "phosphatase"),
        ("phosphatase", "dephospho"),
        ("dephospho", "phospho_state"),
        ("phospho_state", "phospho_target_residue")
    ]
}

dephosphorylation_meta_typing = {
    "phosphatase": "region",
    "phosphatase_activity": "state",
    "dephospho": "mod",
    "phospho_state": "state",
    "phospho_target_residue": "residue"
}

dephosphorylation_semantic_AG = {
    "phosphatase": "phosphatase",
    "phosphatase_activity": "phosphatase_activity",
    "dephospho": "dephospho",
    "phospho_state": "phospho_state",
    "phospho_target_residue": "phospho_target_residue"
}

# SH2 - pY binding semantic nugget
sh2_pY_binding = {
    "nodes":
        [
            "sh2_domain",
            ("sh2_domain_pY_bnd", {"type": "do", "test": True}),
            "pY_site",
            ("pY_residue", {"aa": "Y", "test": True}),
            ("phosphorylation", {"name": "phosphorylation", "test": True})
        ],
    "edges":
        [("sh2_domain", "sh2_domain_pY_bnd"),
         ("pY_site", "sh2_domain_pY_bnd"),
         ("pY_residue", "pY_site"),
         ("phosphorylation", "pY_residue")]
}

sh2_pY_meta_typing = {
    "sh2_domain": "region",
    "sh2_domain_pY_bnd": "bnd",
    "pY_site": "site",
    "pY_residue": "residue",
    "phosphorylation": "state",
}

sh2_pY_semantic_AG = {
    "sh2_domain": "sh2_domain",
    "sh2_domain_pY_bnd": "sh2_domain_pY_bnd",
    "pY_site": "pY_site",
    "pY_residue": "phospho_target_residue",
    "phosphorylation": "phospho_state"
}
