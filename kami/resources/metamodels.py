"""Collection of metamodels used in Kami."""
import math
import networkx as nx

from regraph.primitives import (add_nodes_from,
                                add_edges_from)
from regraph.attribute_sets import RegexSet, IntegerSet, UniversalSet


UNIPROT_REGEX =\
    "[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"

base_kami = nx.DiGraph()
add_nodes_from(
    base_kami,
    [
        "component",
        "test",
        "state",
        "action"
    ]
)

add_edges_from(
    base_kami,
    [
        ("component", "component"),
        ("state", "component"),
        ("component", "action"),
        ("action", "component"),
        ("component", "test"),
        ("action", "state")
    ]
)

kami = nx.DiGraph()

add_nodes_from(
    kami,
    [
        ("gene", {
            "uniprotid": RegexSet(UNIPROT_REGEX),
            "hgnc_symbol": RegexSet.universal(),
            "synonyms": RegexSet.universal(),
            "xrefs": UniversalSet()
        }),
        ("region", {
            "start": IntegerSet([(1, math.inf)]),
            "end": IntegerSet([(1, math.inf)]),
            "name": RegexSet.universal(),
            "order": IntegerSet([(1, math.inf)]),
            "label": RegexSet.universal()
        }),
        ("site", {
            "start": IntegerSet([(1, math.inf)]),
            "end": IntegerSet([(1, math.inf)]),
            "name": RegexSet.universal(),
            "order": IntegerSet([(1, math.inf)]),
            "label": RegexSet.universal()
        }),
        ("residue", {
            "aa": {
                "G", "P", "A", "V", "L", "I", "M",
                "C", "F", "Y", "W", "H", "K", "R",
                "Q", "N", "E", "D", "S", "T"
            },
            "loc": IntegerSet([(1, math.inf)])
        }),
        "locus",
        ("state", {
            "activity": {True, False},
            "phosphorylation": {True, False},
            "acetylation": {True, False}
        }),
        ("mod", {
            "value": {True, False},
            "direct": {True, False},
            "text": RegexSet.universal()
        }),
        "syn",
        "deg",
        ("bnd", {"direct": {True, False}}),
        "brk",
        "is_bnd",
        "is_free",
    ]
)

add_edges_from(
    kami,
    [
        ("region", "gene"),
        ("site", "gene"),
        ("site", "region"),
        ("residue", "gene"),
        ("residue", "region"),
        ("residue", "site"),
        ("state", "gene"),
        ("state", "region"),
        ("state", "site"),
        ("state", "residue"),
        ("syn", "gene"),
        ("deg", "gene"),
        ("gene", "locus"),
        ("region", "locus"),
        ("site", "locus"),
        ("mod", "state"),
        ("locus", "bnd"),
        ("locus", "brk"),
        ("locus", "is_bnd"),
        ("locus", "is_free"),
        ("gene", "mod"),
        ("region", "mod"),
        ("site", "mod")
    ]
)

kami_base_kami_typing = {
    "gene": "component",
    "region": "component",
    "site": "component",
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
