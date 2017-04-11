"""Collection of metamodels used in Kami."""
import networkx as nx

from regraph.library.hierarchy import Hierarchy


base_kami = nx.DiGraph()
base_kami.add_nodes_from(
    [
        "component",
        "test",
        "state",
        "action"
    ]
)

base_kami.add_edges_from(
    [
        ("component", "component"),
        ("state", "component"),
        ("component", "action"),
        ("action", "component"),
        ("component", "test"),
        ("action", "state")
    ]
)

kami = nx.DiGraph(base_kami)

kami.add_nodes_from(
    [
        "agent",
        "region",
        "residue",
        "locus",
        "state",
        "mod",
        "syn",
        "deg",
        "bnd",
        "brk",
        "is_bnd",
        "is_free",
    ]
)

kami.add_edges_from(
    [
        ("region", "agent"),
        ("residue", "agent"),
        ("residue", "region"),
        ("state", "agent"),
        ("syn", "agent"),
        ("deg", "agent"),
        ("state", "region"),
        ("state", "residue"),
        ("locus", "agent"),
        ("locus", "region"),
        ("mod", "state"),
        ("locus", "bnd"),
        ("locus", "brk"),
        ("locus", "is_bnd"),
        ("locus", "is_free"),
        ("agent", "mod")
    ]
)

kami_base_kami_typing = {
    "agent": "component",
    "region": "component",
    "residue": "component",
    "locus": "component",
    "state": "state",
    "mod": "action",
    "syn": "action",
    "deg": "action",
    "bnd": "action",
    "brk": "action",
    "is_bnd": "test",
    "is_free": "test",
}
