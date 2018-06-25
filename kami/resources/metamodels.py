"""Collection of metamodels used in Kami."""
import math
import networkx as nx

from regraph.primitives import (add_nodes_from,
                                add_edges_from)
from regraph.attribute_sets import RegexSet, IntegerSet, UniversalSet


UNIPROT_REGEX =\
    "[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"

INTERPRO_REGEX = "IPR\d{6}"

base_kami = nx.DiGraph()
add_nodes_from(
    base_kami,
    [
        "component",
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
            "name": RegexSet.universal(),
            "interproid": RegexSet(INTERPRO_REGEX),
            "label": RegexSet.universal()
        }),
        ("site", {
            "name": RegexSet.universal(),
            "interproid": RegexSet(INTERPRO_REGEX),
            "label": RegexSet.universal()
        }),
        ("residue", {
            "aa": {
                "G", "P", "A", "V", "L", "I", "M",
                "C", "F", "Y", "W", "H", "K", "R",
                "Q", "N", "E", "D", "S", "T"
            },
            "test": {True, False}
        }),
        ("state", {
            "name": {
                "phosphorylation",
                "activity",
                "acetylation"
            },
            "test": {True, False}
        }),
        ("mod", {
            "value": {True, False},
            "text": RegexSet.universal(),
            "rate": UniversalSet(),
            "unimolecular_rate": UniversalSet()
        }),
        "syn",
        "deg",
        ("bnd", {
            "type": {"do", "be"},
            "test": {True, False},
            "text": RegexSet.universal(),
            "rate": UniversalSet(),
            "unimolecular_rate": UniversalSet()
        })
    ]
)

add_edges_from(
    kami,
    [
        (
            "region", "gene",
            {"start": IntegerSet([(1, math.inf)]),
             "end": IntegerSet([(1, math.inf)]),
             "order": IntegerSet([(1, math.inf)])}
        ),
        (
            "site", "gene",
            {"start": IntegerSet([(1, math.inf)]),
             "end": IntegerSet([(1, math.inf)]),
             "order": IntegerSet([(1, math.inf)]),
             "type": {"transitive"}}
        ),
        (
            "site", "region",
            {"start": IntegerSet([(1, math.inf)]),
             "end": IntegerSet([(1, math.inf)]),
             "order": IntegerSet([(1, math.inf)])}
        ),
        (
            "residue", "gene",
            {"loc": IntegerSet([(1, math.inf)]),
             "type": {"transitive"}}
        ),
        (
            "residue", "region",
            {"loc": IntegerSet([(1, math.inf)]),
             "type": {"transitive"}}
        ),
        (
            "residue", "site",
            {"loc": IntegerSet([(1, math.inf)])}
        ),
        ("state", "gene"),
        ("state", "region"),
        ("state", "site"),
        ("state", "residue"),
        ("syn", "gene"),
        ("deg", "gene"),
        ("gene", "bnd"),
        ("region", "bnd"),
        ("site", "bnd"),
        ("mod", "state"),
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
    "state": "state",
    "mod": "action",
    "syn": "action",
    "deg": "action",
    "bnd": "action"
}
