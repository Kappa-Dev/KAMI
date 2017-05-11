"""Basic black box functionality."""
import time
import sys

from kami.resolvers.generators import ModGenerator
from kami.data_structures.kami_hierarchy import KamiHierarchy


def generate_nugget_id():
    return "nugget_at_%s" % str(round(time.time() * 1000))


def add_modification(mod, hierarchy, add_agents=True, anatomize=True,
                     merge_actions=True, apply_sematics=True):
    gen = ModGenerator(hierarchy)
    gen.generate(
        mod, add_agents=True, anatomize=True,
        merge_actions=True, apply_sematics=True
    )

    # # TODO: make it INFO
    # print("Created nugget '%s'." % nugget_id)
    # print("Action graph typing: %s." % ag_typing)
    # print("Template relation: %s." % template_rel)
    # if negative_id:
    #     print("Created negative conditions nugget '%s'." % negative_id)
    #     print("Action graph typing of negative conditions: %s." % negative_ag_typing)
    #     print("Template relation of negative conditions: %s." % negative_template_rel)


def add_automodification(mod, hierarchy, add_agents=True, anatomize=True,
                         merge_actions=True, apply_sematics=True):
    pass


def add_transmodification(mod, hierarchy, add_agents=True, anatomize=True,
                          merge_actions=True, apply_sematics=True):
    pass


def add_anonymousmodification(mod, hierarchy, add_agents=True, anatomize=True,
                              merge_actions=True, apply_sematics=True):
    pass


def add_binarybinding(bnd, hierarchy, add_agents=True, anatomize=True,
                      merge_actions=True, apply_sematics=True):
    pass


def add_complex(complex, hierarchy, add_agents=True, anatomize=True,
                merge_actions=True, apply_sematics=True):
    pass


def create_nuggets(interactions, hierarchy=None, add_agents=True, anatomize=True,
                   merge_actions=True, apply_sematics=True):
    """Create nuggets from a collection of interactions."""
    if not hierarchy:
        hierarchy = KamiHierarchy()

    for interaction in interactions:
        interaction_type = type(interaction).__name__.lower()

        # Dynamically call functions corresponding to an interaction type
        getattr(sys.modules[__name__], "add_%s" % interaction_type)(
            interaction, hierarchy, add_agents,
            anatomize, merge_actions, apply_sematics
        )
