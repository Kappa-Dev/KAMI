"""Basic black box functionality."""
import sys
import time

from kami.resolvers.generators import (ModGenerator,
                                       # AutoModGenerator,
                                       # TransModGenerator,
                                       AnonymousModGenerator,
                                       BndGenerator)
from kami.hierarchy import KamiHierarchy


def _add_modification(mod, hierarchy, add_agents=True, anatomize=True,
                      apply_semantics=True):
    """Add modification nugget to the hierarchy."""
    gen = ModGenerator(hierarchy)
    gen.generate(
        mod, add_agents, anatomize, apply_semantics)

# def add_automodification(mod, hierarchy, add_agents=True, anatomize=True,
#                          merge_actions=True, apply_semantics=True):
#     """Add automodification nugget to the hierarchy."""
#     gen = AutoModGenerator(hierarchy)
#     gen.generate(
#         mod, add_agents, anatomize,
#         merge_actions, apply_semantics
#     )


# def add_transmodification(mod, hierarchy, add_agents=True, anatomize=True,
#                           merge_actions=True, apply_semantics=True):
#     """Add transmodification nugget to the hierarchy."""
#     gen = TransModGenerator(hierarchy)
#     gen.generate(
#         mod, add_agents, anatomize,
#         merge_actions, apply_semantics
#     )


def _add_anonymousmodification(mod, hierarchy, add_agents=True, anatomize=True,
                               merge_actions=True, apply_semantics=True):
    """Add anonymous modification nugget to the hierarchy."""
    gen = AnonymousModGenerator(hierarchy)
    gen.generate(
        mod, add_agents, anatomize, apply_semantics
    )


def _add_binding(bnd, hierarchy, add_agents=True, anatomize=True,
                 apply_semantics=True):
    """Add binary bnd nugget to the hierarchy."""
    gen = BndGenerator(hierarchy)
    gen.generate(
        bnd, add_agents, anatomize, apply_semantics)


def create_nugget(interaction, hierarchy=None, add_agents=True,
                  anatomize=True, apply_semantics=True):
    """Create a nugget from a KAMI interaction."""
    if hierarchy is None:
        hierarchy = KamiHierarchy()

    if "action_graph" not in hierarchy.nodes():
        hierarchy.create_empty_action_graph()

    interaction_type = type(interaction).__name__.lower()

    # Dynamically call function corresponding to an interaction type
    getattr(sys.modules[__name__], "_add_%s" % interaction_type)(
        interaction,
        hierarchy=hierarchy,
        add_agents=add_agents,
        anatomize=anatomize,
        apply_semantics=apply_semantics
    )

    return hierarchy


def create_nuggets(interactions, hierarchy=None, add_agents=True,
                   anatomize=True, apply_semantics=True):
    """Create nuggets from a collection of interactions."""
    if hierarchy is None:
        hierarchy = KamiHierarchy()

    if "action_graph" not in hierarchy.nodes():
        hierarchy.create_empty_action_graph()

    for i, interaction in enumerate(interactions):
        create_nugget(interaction, hierarchy, add_agents,
                      anatomize, apply_semantics)

    return hierarchy


def add_interactions(interactions, hierarchy=None, add_agents=True,
                     anatomize=True, apply_semantics=True):
    """Alias for 'create_nuggets'."""
    h = create_nuggets(
        interactions, hierarchy, add_agents, anatomize, apply_semantics)
    return h


def add_interaction(interaction, hierarchy=None, add_agents=True,
                    anatomize=True, apply_semantics=True):
    """Alias for 'create_nugget'."""
    h = create_nugget(interaction, hierarchy, add_agents,
                      anatomize, apply_semantics)
    return h
