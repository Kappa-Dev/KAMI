"""Collection of untils for parsing KAMIql.

Examples
--------

1. Mathch all the pairs of interacting protoforms, where the first protoform
interacts through an SH2 domain:

```
MATCH (p1:protoform)<-(r1:region {name: "SH2"})-(i:interaction)-..-(p2:protoform)
RETURN p1, i, p2
```

mechanism
id



"""
from pyparsing import (Word, alphas, alphanums, nums,
                       CaselessKeyword, Suppress,
                       Literal, delimitedList, Group,
                       Optional, Forward, Combine, QuotedString,
                       OneOrMore)

# Definition of variable
var = Word(alphas, alphanums + "_")

# Definition of literals
point = Literal('.')
plusorminus = (Literal('+') | Literal('-'))

# For names of the nodes and the attributes definition
number = Word(nums).setParseAction(lambda s, l, t: [int(t[0])])
integer = Optional(plusorminus) + Word(nums)


def eval_int(s, l, t):
    """Evaluate integer."""
    if len(t) > 1:
        if t[0] == '-' or t[0] == '+':
            return [int(t[0] + t[1])]
        else:
            return [int(t[0])]
    else:
        return [int(t[0])]


integer.setParseAction(eval_int)

floatnumber = Optional(plusorminus).setResultsName("sign") + Combine(
    Word(nums) + point + Optional(number)
)


def eval_float(s, l, t):
    """Evaluate float."""
    if len(t) > 1:
        if t[0] == '-' or t[0] == '+':
            return [float(t[0] + t[1])]
        else:
            return [float(t[0])]
    else:
        return [float(t[0])]


floatnumber.setParseAction(eval_float)
string_literal = (QuotedString("'", escChar='\\') | QuotedString("\"", escChar='\\'))


# Definition of key literal and words
eq = Literal("=")
neq = Literal("<>")

single_quote = Suppress(Literal("\'"))
double_quote = Suppress(Literal("\""))

node_open = Suppress(Literal("("))
node_close = Suppress(Literal(")"))

label_start = Suppress(Literal(":"))
property_start = Suppress(Literal("."))

rel_source = Suppress(Literal("-"))
rel_target_left = Suppress(Literal("<-"))
rel_target_right = Suppress(Literal("->"))

rel_open = Suppress(Literal("["))
rel_close = Suppress(Literal("]"))

match = CaselessKeyword("MATCH")
match.setParseAction(lambda t: t[0].lower())

where = CaselessKeyword("WHERE")
where.setParseAction(lambda t: t[0].lower())

and_connective = CaselessKeyword("AND")
and_connective.setParseAction(lambda t: t[0].lower())

or_connective = CaselessKeyword("OR")
or_connective.setParseAction(lambda t: t[0].lower())

return_kw = CaselessKeyword("RETURN")
return_kw.setParseAction(lambda t: t[0].lower())

star = Suppress(Literal("*"))
# star.setParseAction(lambda t: t[0])

# Syntax of node and edge definitions
node = node_open +\
    Optional(var).setResultsName("node_var") +\
    Optional(label_start + var.setResultsName("node_label")) +\
    node_close
node_element = node.setResultsName("node")

edge_start = (
    rel_source |
    rel_target_left
)
edge_end = (
    rel_target_right |
    rel_source
)

# range_expr = (
#     Optional(integer).setResultsName("start") +
#     Suppress(Literal("..")) +
#     Optional(integer).setResultsName("end")
# )

# edge_def = (
#     rel_open +
#     Optional(var).setResultsName("edge_var") +
#     Optional(label_start + var.setResultsName("edge_label")) +
#     Optional(star + Optional(
#         range_expr).setResultsName("range")).setResultsName("star") +
#     rel_close
# )
undirected_edge = rel_source + Optional(Suppress(Literal(".."))) + rel_source
edge_to_right = rel_source + Optional(Suppress(Literal(".."))) + rel_target_right
edge_to_left = rel_target_left + Optional(Suppress(Literal(".."))) + rel_source

edge = (
    edge_to_left | edge_to_right
)

edge = (
    node.setResultsName("source_node") + edge_to_right +
    node.setResultsName("target_node") |
    node.setResultsName("target_node") + edge_to_left +
    node.setResultsName("source_node") |
    node.setResultsName("left_node") + undirected_edge +
    node.setResultsName("right_node")
)

unfinished_edge = (
    edge_to_right + node.setResultsName("target_node") |
    edge_to_left + node.setResultsName("source_node") |
    undirected_edge + node.setResultsName("right_node")
)

multiedge = (
    edge + Optional(OneOrMore(unfinished_edge))
)

# Syntax for patterns
element = Group(multiedge | edge | node)
pattern = delimitedList(element)

# Syntax for conditions
boolean_connective = (
    and_connective |
    or_connective
)
condition_member = (
    string_literal |
    integer |
    floatnumber |
    Group(var.setResultsName("var") + property_start + var.setResultsName("property")))

binary_operator = eq | neq
binary_condition = Group(
    condition_member.setResultsName("lhs") +
    binary_operator.setResultsName("operator") +
    condition_member.setResultsName("rhs"))

condition_statement = Group(
    binary_condition.setResultsName("binary_condition") |
    Group(condition_member).setResultsName("unary_condition")
)

condition = Forward()
condition << condition_statement + Optional(boolean_connective + condition)
conditions = condition

# Syntax for results
result = (
    Group(
        var.setResultsName("var") +
        property_start +
        var.setResultsName("property")) |
    Group(var.setResultsName("var")))
results = delimitedList(result)

# Statements
match_statement = match + pattern.setResultsName("pattern_elements")
where_statement = where + conditions.setResultsName("conditions")
return_statement = return_kw + results.setResultsName("results")

# Queries
query = (
    match_statement.setResultsName("match_statement") +
    Optional(where_statement.setResultsName("where_statement")) +
    return_statement.setResultsName("return_statement")
)

parser = query.setResultsName("query") + ";"
parser.setDefaultWhitespaceChars(' tn')


def parse_query(string):
    """Parse a Cypher query."""
    parsed = parser.parseString(string).asDict()
    print(parsed)
    print()
    print(parsed["pattern_elements"])
    # if "where_statement" in parsed:
    #     where_result = parse_where(
    #         parsed["conditions"])
    # else:
    #     where_result = None
    # result = {
    #     "match": parse_pattern(
    #         parsed["pattern_elements"]),
    #     "where": where_result,
    #     "return": parsed["results"]
    # }
    # return result
