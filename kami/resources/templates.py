"""Collection of nugget templates."""

mod_nugget = {
    "nodes": [
        "enzyme",
        "enzyme_region",
        "enzyme_site",
        "substrate",
        "substrate_region",
        "substrate_site",
        "substrate_residue",
        "mod_state",
        "mod"
    ],
    "edges": [
        ("enzyme_site", "enzyme"),
        ("enzyme_site", "enzyme_region"),
        ("enzyme_site", "mod"),
        ("enzyme_region", "enzyme"),
        ("enzyme", "mod"),
        ("enzyme_region", "mod"),
        ("mod", "mod_state"),
        ("mod_state", "substrate"),
        ("mod_state", "substrate_site"),
        ("mod_state", "substrate_region"),
        ("mod_state", "substrate_residue"),
        ("substrate_region", "substrate"),
        ("substrate_residue", "substrate"),
        ("substrate_residue", "substrate_region"),
        ("substrate_site", "substrate"),
        ("substrate_site", "substrate_region"),
        ("substrate_residue", "substrate_site")
    ]
}

mod_meta_typing = {
    "enzyme": "gene",
    "enzyme_region": "region",
    "enzyme_site": "site",
    "substrate": "gene",
    "substrate_region": "region",
    "substrate_residue": "residue",
    "substrate_site": "site",
    "mod_state": "state",
    "mod": "mod"
}

bnd_nugget = {
    "nodes": [
        "left_partner",
        "right_partner",
        "left_partner_region",
        "right_partner_region",
        "left_partner_site",
        "right_partner_site",
        "bnd"
    ],
    "edges": [
        ("left_partner_site", "left_partner"),
        ("left_partner_site", "left_partner_region"),
        ("right_partner_site", "right_partner"),
        ("right_partner_site", "right_partner_region"),
        ("left_partner_region", "left_partner"),
        ("right_partner_region", "right_partner"),
        ("left_partner_site", "bnd"),
        ("right_partner_site", "bnd"),
        ("left_partner_region", "bnd"),
        ("right_partner_region", "bnd"),
        ("left_partner", "bnd"),
        ("right_partner", "bnd"),
    ]
}

bnd_meta_typing = {
    "left_partner": "gene",
    "right_partner": "gene",
    "left_partner_region": "region",
    "right_partner_region": "region",
    "left_partner_site": "site",
    "right_partner_site": "site",
    "bnd": "bnd",
}
