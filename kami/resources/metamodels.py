"""Collection of metamodels used in Kami."""
import math

from regraph.attribute_sets import RegexSet, IntegerSet, UniversalSet


UNIPROT_REGEX =\
    "[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"

INTERPRO_REGEX = "IPR\d{6}"

base_graph = {
    "nodes": [
        "component",
        "state",
        "action"
    ],
    "edges": [
        ("component", "component"),
        ("state", "component"),
        ("component", "action"),
        ("action", "component"),
        ("action", "state")
    ]
}

meta_model = {
    "nodes": [
        ("gene", {
            "uniprotid": RegexSet.universal(),
            "hgnc_symbol": RegexSet.universal(),
            "synonyms": RegexSet.universal(),
            "xrefs": RegexSet.universal()
            # "xrefs": UniversalSet()
        }),
        ("region", {
            "name": RegexSet.universal(),
            "interproid": RegexSet.universal(),
            # "interproid": RegexSet(INTERPRO_REGEX),
            "label": RegexSet.universal()
        }),
        ("site", {
            "name": RegexSet.universal(),
            "interproid": RegexSet.universal(),
            # "interproid": RegexSet(INTERPRO_REGEX),
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
                "acetylation",
                "ubiquitination",
                "glycosylation",
                "palmitoylation",
                "myristoylation",
                "sumoylation"
            },
            "test": {True, False}
        }),
        ("mod", {
            "value": {True, False},
            "text": RegexSet.universal(),
            "rate": RegexSet.universal(),
            "unimolecular_rate": RegexSet.universal()
            # "rate": UniversalSet(),
            # "unimolecular_rate": UniversalSet()
        }),
        "syn",
        "deg",
        ("bnd", {
            "type": {"do", "be"},
            "test": {True, False},
            "text": RegexSet.universal(),
            "rate": RegexSet.universal(),
            "unimolecular_rate": RegexSet.universal()
            # "rate": UniversalSet(),
            # "unimolecular_rate": UniversalSet()
        })
    ],

    "edges": [
        (
            "region", "gene",
            {"start": IntegerSet.universal(),
             "end": IntegerSet.universal(),
             "order": IntegerSet.universal()}
            # {"start": IntegerSet([(1, math.inf)]),
            #  "end": IntegerSet([(1, math.inf)]),
            #  "order": IntegerSet([(1, math.inf)])}
        ),
        (
            "site", "gene",
            # {"start": IntegerSet([(1, math.inf)]),
            #  "end": IntegerSet([(1, math.inf)]),
            #  "order": IntegerSet([(1, math.inf)]),
            {"start": IntegerSet.universal(),
             "end": IntegerSet.universal(),
             "order": IntegerSet.universal(),
             "type": {"transitive"}}
        ),
        (
            "site", "region",
            {"start": IntegerSet.universal(),
             "end": IntegerSet.universal(),
             "order": IntegerSet.universal()}
            # {"start": IntegerSet([(1, math.inf)]),
            #  "end": IntegerSet([(1, math.inf)]),
            #  "order": IntegerSet([(1, math.inf)])}
        ),
        (
            "residue", "gene",
            # {"loc": IntegerSet([(1, math.inf)]),
            {"loc": IntegerSet.universal(),
             "type": {"transitive"}}
        ),
        (
            "residue", "region",
            # {"loc": IntegerSet([(1, math.inf)]),
            {"loc": IntegerSet.universal(),
             "type": {"transitive"}}
        ),
        (
            "residue", "site",
            # {"loc": IntegerSet([(1, math.inf)])}
            {"loc": IntegerSet.universal()}
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
}
meta_model_base_typing = {
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
