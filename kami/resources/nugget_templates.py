"""Collection of nugget templates."""
import networkx as nx


MOD_NUGGET = nx.DiGraph()
MOD_NUGGET.add_nodes_from([
    "enzyme",
    "enzyme_region",
    "substrate",
    "substrate_region",
    "substrate_residue",
    "mod_state",
    "mod"
])
MOD_NUGGET.add_edges_from([
    ("enzyme_region", "enzyme"),
    ("enzyme", "mod"),
    ("enzyme_region", "mod"),
    ("mod", "mod_state"),
    ("mod_state", "substrate"),
    ("mod_state", "substrate_region"),
    ("mod_state", "substrate_residue"),
    ("substrate_region", "substrate"),
    ("substrate_residue", "substrate"),
    ("substrate_residue", "substrate_region")
])

MOD_KAMI_TYPING = {
    "enzyme": "agent",
    "enzyme_region": "region",
    "substrate": "agent",
    "substrate_region": "region",
    "substrate_residue": "residue",
    "mod_state": "state",
    "mod": "mod"
}

BND_NUGGET = nx.DiGraph()
BND_NUGGET.add_nodes_from([
    "partner",
    "partner_region",
    "partner_locus",
    "bnd"
])
BND_NUGGET.add_edges_from([
    ("partner_region", "partner"),
    ("partner_region", "partner_locus"),
    ("partner", "partner_locus"),
    ("partner_locus", "bnd")
])

BND_KAMI_TYPING = {
    "partner": "agent",
    "partner_region": "region",
    "partner_locus": "locus",
    "bnd": "bnd"
}
