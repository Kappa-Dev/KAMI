"""Basic black box functionality."""
import json
import sys
import time

from kami.resolvers.generators import (ModGenerator,
                                       # AutoModGenerator,
                                       # TransModGenerator,
                                       AnonymousModGenerator,
                                       BndGenerator)
from kami.hierarchy import KamiHierarchy


def add_modification(mod, hierarchy, add_agents=True, anatomize=True,
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


def add_anonymousmodification(mod, hierarchy, add_agents=True, anatomize=True,
                              merge_actions=True, apply_semantics=True):
    """Add anonymous modification nugget to the hierarchy."""
    gen = AnonymousModGenerator(hierarchy)
    gen.generate(
        mod, add_agents, anatomize, apply_semantics
    )

def add_binding(bnd, hierarchy, add_agents=True, anatomize=True,
                apply_semantics=True):
    """Add binary bnd nugget to the hierarchy."""
    gen = BndGenerator(hierarchy)
    gen.generate(
        bnd, add_agents, anatomize, apply_semantics)

# def add_complex(complex, hierarchy, add_agents=True, anatomize=True,
#                 merge_actions=True, apply_semantics=True):
#     """Add complex nugget to the hierarchy."""
#     gen = ComplexGenerator(hierarchy)
#     gen.generate(
#         complex, add_agents, anatomize,
#         merge_actions, apply_semantics
#     )


def create_nuggets(interactions, hierarchy=None, add_agents=True,
                   anatomize=True, apply_semantics=True):
    """Create nuggets from a collection of interactions."""
    if hierarchy is None:
        hierarchy = KamiHierarchy()

    if "action_graph" not in hierarchy.nodes():
        hierarchy.create_empty_action_graph()
    time_to_generate_nugget = []
    size_of_ag = []

    with open(filename, "a+") as f:
        for i, interaction in enumerate(interactions):
            interaction_type = type(interaction).__name__.lower()

            # Dynamically call functions corresponding to an interaction type
            start = time.time()
            getattr(sys.modules[__name__], "add_%s" % interaction_type)(
                interaction,
                hierarchy=hierarchy,
                add_agents=add_agents,
                anatomize=anatomize,
                apply_semantics=apply_semantics
            )
            end = time.time() - start
            time_to_generate_nugget.append(end)
            size_of_ag.append(len(hierarchy.action_graph.nodes()))

    return hierarchy
