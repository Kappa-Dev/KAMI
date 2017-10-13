"""A set of default complnents of KAMI hierarchy."""
from kami.resources import (metamodels,
                            templates,
                            semantics)

GRAPHS = [
    ("kami", metamodels.kami, {"type": "meta_model"}),
    ("semantic_action_graph",
     semantics.action_graph,
     {"type": "semantic_action_graph"}),
    ("bnd_template", templates.bnd_nugget, {"type": "template"}),
    ("mod_template", templates.mod_nugget, {"type": "template"}),
    ("phosphorylation", semantics.phosphorylation,
     {
         "type": "semantic_nugget",
         "interaction_type": "mod"
     }),
    ("sh2_pY_binding", semantics.sh2_pY_binding,
     {
         "type": "semantic_nugget",
         "interaction_type": "bnd"
     })
]

TYPING = [
    ("semantic_action_graph", "kami", semantics.sag_kami_typing, None),
    ("bnd_template", "kami", templates.bnd_kami_typing, None),
    ("mod_template", "kami", templates.mod_kami_typing, None),
    ("phosphorylation", "semantic_action_graph",
     semantics.phosphorylation_semantic_AG, None),
    ("sh2_pY_binding", "semantic_action_graph",
     semantics.sh2_pY_semantic_AG, None),
    ("phosphorylation", "kami",
     semantics.phosphorylation_kami_typing, None),
    ("sh2_pY_binding", "kami",
     semantics.sh2_pY_kami_typing, None)
]

# In the future we may accomodate some default rules in the KAMI hierarchy
RULES = []
RULE_TYPING = []
RELATIONS = []
