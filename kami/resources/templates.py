"""Collection of nugget templates."""
import networkx as nx

from regraph.primitives import (add_nodes_from,
                                add_edges_from)


mod_nugget = nx.DiGraph()
add_nodes_from(
    mod_nugget,
    [
        "enzyme",
        "enzyme_region",
        "substrate",
        "substrate_region",
        "substrate_residue",
        "mod_state",
        "mod"
    ]
)
add_edges_from(mod_nugget, [
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

mod_kami_typing = {
    "enzyme": "gene",
    "enzyme_region": "region",
    "substrate": "gene",
    "substrate_region": "region",
    "substrate_residue": "residue",
    "mod_state": "state",
    "mod": "mod"
}

bnd_nugget = nx.DiGraph()
add_nodes_from(bnd_nugget, [
    "partner",
    "partner_region",
    "partner_locus",
    "bnd"
])
add_edges_from(bnd_nugget, [
    ("partner_region", "partner"),
    ("partner_region", "partner_locus"),
    ("partner", "partner_locus"),
    ("partner_locus", "bnd")
])

bnd_kami_typing = {
    "partner": "gene",
    "partner_region": "region",
    "partner_locus": "locus",
    "bnd": "bnd"
}
