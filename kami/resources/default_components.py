"""A set of default complnents of KAMI hierarchy."""
from kami.resources import (metamodels,
                            templates,
                            semantics)


GRAPHS = [
    ("meta_model", metamodels.meta_model, {"type": "meta_model"}),
    ("semantic_action_graph",
     semantics.action_graph,
     {"type": "semantic_action_graph"}),
    ("bnd_template", templates.bnd_nugget, {"type": "template"}),
    ("mod_template", templates.mod_nugget, {"type": "template"}),
    ("phosphorylation_semantic_nugget", semantics.phosphorylation,
     {
         "type": "semantic_nugget",
         "interaction_type": "mod"
     }),
    ("sh2_pY_binding_semantic_nugget", semantics.sh2_pY_binding,
     {
         "type": "semantic_nugget",
         "interaction_type": "bnd"
     })
]


MODEL_GRAPHS = [
    ("meta_model", metamodels.meta_model, {"type": "meta_model"}),
    ("bnd_template", templates.bnd_nugget, {"type": "template"}),
    ("mod_template", templates.mod_nugget, {"type": "template"})
]


TYPING = [
    ("semantic_action_graph", "meta_model", semantics.sag_meta_typing, None),
    ("bnd_template", "meta_model", templates.bnd_meta_typing, None),
    ("mod_template", "meta_model", templates.mod_meta_typing, None),
    ("phosphorylation_semantic_nugget", "semantic_action_graph",
     semantics.phosphorylation_semantic_AG, None),
    ("sh2_pY_binding_semantic_nugget", "semantic_action_graph",
     semantics.sh2_pY_semantic_AG, None),
    ("phosphorylation_semantic_nugget", "meta_model",
     semantics.phosphorylation_meta_typing, None),
    ("sh2_pY_binding_semantic_nugget", "meta_model",
     semantics.sh2_pY_meta_typing, None)
]

MODEL_TYPING = [
    ("bnd_template", "meta_model", templates.bnd_meta_typing, None),
    ("mod_template", "meta_model", templates.mod_meta_typing, None),
]


# In the future we may accomodate some default rules in the KAMI hierarchy
RULES = []
RULE_TYPING = []
RELATIONS = []

MODEL_RULES = []
MODEL_RULE_TYPING = []
MODEL_RELATIONS = []
