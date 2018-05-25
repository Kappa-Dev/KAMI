def ag_to_edge_list(hierarchy, agent_ids="hgnc_symbol"):
    edge_list = []
    for u, v in hierarchy.action_graph.edges():
        if hierarchy.action_graph_typing[u] == "gene":
            hgnc = None
            if "hgnc_symbol" in hierarchy.action_graph.node[u].keys():
                hgnc = list(hierarchy.action_graph.node[u]["hgnc_symbol"])[0]
            if hgnc is not None:
                n1 = hgnc
            else:
                n1 = u
        else:
            n1 = u.replace(",", "").replace(" ", "")
        if hierarchy.action_graph_typing[v] == "gene":
            hgnc = None
            if "hgnc_symbol" in hierarchy.action_graph.node[v].keys():
                hgnc = list(hierarchy.action_graph.node[v]["hgnc_symbol"])[0]
            if hgnc is not None:
                n2 = hgnc
            else:
                n2 = v
        else:
            n2 = v.replace(",", "").replace(" ", "")
        edge_list.append((n1, n2))
    return edge_list


def get_studio_v1(hierarchy,
                  gene_label="hgnc_symbol", region_label="label"):
    """
    Convert a Kami hierarchy to a dictionary formatted for the old KamiStudio.
    To convert a Kami model into a KamiStudio readable file:
    yourmodel = kami_hierarchy.get_studio_v1()
    json.dump(yourmodel, outfile, indent=4, sort_keys=False)
    """

    def find_studio_label(node_id, node_typ, counter_dict, graph_level):
        """
        Subfunction to find appropriate node labels based on the types
        of labels chosen on get_studio_v1 call.
        """

        label = node_typ  # For bnd, brk, mod, syn and deg.
        if node_typ == "half-act":
            label = "half"
        if node_typ == "is_bnd":
            label = "bound"
        if node_typ == "is_free":
            label = "free"
        # Labeling of entities is more subtle.
        if node_typ == "gene":
            try:
                field = (hierarchy.graph[graph_level]
                         .node[node_id][gene_label])
            except:
                field = (hierarchy.graph[graph_level]
                         .node[node_id]["uniprotid"])
            label = list(field)[0]
        if node_typ == "region":
            try:
                field = (hierarchy.graph[graph_level]
                         .node[node_id][region_label])
            except:
                field = (hierarchy.graph[graph_level]
                         .node[node_id]["name"])
            label = list(field)[0]
        if node_typ == "site":
            field = (hierarchy.graph[graph_level]
                     .node[node_id]["name"])
            label = list(field)[0]
        if node_typ == "residue":
            aa_field = (hierarchy.graph[graph_level]
                        .node[node_id]["aa"])
            loc_field = (hierarchy.graph[graph_level]
                         .node[node_id]["loc"])
            aa = list(aa_field)[0]
            loc = list(loc_field)[0]
            label = '%s%s' % (aa, loc)
        if node_typ == "state":
            underscore = node_id.rfind("_")
            state_name = node_id[underscore + 1:]
            if state_name == "phosphorylation":
                label = "phos"
            else:
                label = state_name

        # Add a count number to uniquely identify nodes with a same label.
        if label in counter_dict.keys():
            label_with_count = "%s %i" % (label, counter_dict[label])
            counter_dict[label] = counter_dict[label] + 1
        elif label not in counter_dict.keys():
            label_with_count = label
            counter_dict[label] = 2

        return label_with_count, counter_dict

    # Create graph hierarchy root.
    kami_v1_dict = {}
    kami_v1_dict["id"] = '/'
    kami_v1_dict["name"] = '/'
    top_graph = {"attributes": {"name": "/"}, "edges": [], "nodes": []}
    kami_v1_dict["top_graph"] = top_graph
    kami_v1_dict["children"] = []

    # Create kami_base. Hard coded since this level is absent in the new Kami.
    kami_base = {}
    kami_base["id"] = "kami_base"
    kami_base["name"] = "kami_base"
    top_graph = {}

    nodes = []
    for node_type in ["component", "action", "state", "test"]:
        node = {"id": "", "type": "",
                "attrs": {"val": {"numSet": {"neg_list": []},
                                  "strSet": {"neg_list": []}}}}
        node["id"] = node_type
        nodes.append(node)
    top_graph["nodes"] = nodes

    edges = [{"from": "component", "to": "component", "attrs": {}},
             {"from": "component", "to": "action",    "attrs": {}},
             {"from": "component", "to": "test", "attrs": {}},
             {"from": "action",    "to": "component", "attrs": {}},
             {"from": "action",    "to": "state", "attrs": {}},
             {"from": "state",     "to": "component", "attrs": {}}]
    top_graph["edges"] = edges

    positions = {
        "action":    {"x": 818.1, "y": 530.9},
        "component": {"x": 621.4, "y": 435.1},
        "state":     {"x": 801.8, "y": 298.7},
        "test":      {"x": 585.1, "y": 517.5}
    }
    attributes = {"name": "kami_base", "positions": positions}
    top_graph["attributes"] = attributes

    kami_base["top_graph"] = top_graph
    kami_base["children"] = []
    kami_v1_dict["children"].append(kami_base)

    # Create kami (meta model). Typing by kami_base is hard coded
    # since it is absent from the new Kami. Node positions are added
    # when possible.
    kami_meta_model = {}
    kami_meta_model["id"] = "kami"
    kami_meta_model["name"] = "kami"
    top_graph = {}

    kami_typing = {"bnd": "action", "is_free": "test", "state": "state",
                   "is_bnd": "test", "brk": "action", "mod": "action",
                   "residue": "component", "deg": "action", "syn": "action",
                   "half-act": "component", "gene": "component",
                   "region": "component", "site": "component"}

    nodes = []
    for kami_node in hierarchy.graph['kami'].nodes():
        node = {"id": "", "type": "",
                "attrs": {"val": {"numSet": {"neg_list": []},
                                  "strSet": {"neg_list": []}}}}
        node_id = kami_node
        if kami_node == "locus":  # Rename locus to half-action.
            node_id = "half-act"
        node["id"] = node_id
        node["type"] = kami_typing[node_id]
        nodes.append(node)
    top_graph["nodes"] = nodes

    edges = []
    for kami_edge in hierarchy.graph['kami'].edges():
        source = kami_edge[0]
        if source == "locus":
            source = "half-act"
        target = kami_edge[1]
        if target == "locus":
            target = "half-act"
        edge = {"from": source, "to": target, "attrs": {}}
        edges.append(edge)
    top_graph["edges"] = edges

    positions = {
        "bnd":      {"x": 539.3,  "y": 267.3},
        "is_free":  {"x": 378.0,  "y": 413.9},
        "state":    {"x": 1212.4, "y": 450.9},
        "is_bnd":   {"x": 406.3,  "y": 519.7},
        "brk":      {"x": 417.2,  "y": 285.0},
        "mod":      {"x": 1218.1, "y": 588.0},
        "residue":  {"x": 1088.2, "y": 334.3},
        "deg":      {"x": 820.5,  "y": 721.8},
        "syn":      {"x": 652.8,  "y": 722.4},
        "half-act": {"x": 543.1,  "y": 409.8},
        "gene":     {"x": 728.5,  "y": 591.6},
        "region":   {"x": 728.5,  "y": 443.3},
        "site":     {"x": 893.0,  "y": 335.3},
        "compo":    {"x": 727.4,  "y": 275.3}
    }
    attributes = {"name": "kami", "positions": positions}
    top_graph["attributes"] = attributes

    kami_meta_model["top_graph"] = top_graph
    kami_meta_model["children"] = []
    kami_base["children"].append(kami_meta_model)

    # Create action_graph by reading in the new Kami hierarchy.
    action_graph = {}
    action_graph["id"] = "action_graph"
    action_graph["name"] = "action_graph"
    top_graph = {}

    action_graph_typing = hierarchy.typing['action_graph']['kami']
    counters = {}
    label_tracker = {}

    nodes = []
    for ag_node in hierarchy.graph['action_graph'].nodes():
        node_type = action_graph_typing[ag_node]
        if node_type == "locus":
            node_type = "half-act"
        node_label, counters = find_studio_label(ag_node,
                                                 node_type,
                                                 counters,
                                                 "action_graph")
        label_tracker[ag_node] = node_label
        attrs = {}
        vals = "empty"
        if node_type == "mod":
            vals = list(hierarchy.graph['action_graph']
                        .node[ag_node]['value'])
        elif node_type == "state":
            vals = list(hierarchy.graph['action_graph']
                        .node[ag_node].values())[0]
        if vals != "empty":
            value_list = []
            for val in vals:
                if val is True:
                    val = "True"
                if val is False:
                    val = "False"
                value_list.append(val)
            attrs = {"val": {"numSet": {"pos_list": []},
                             "strSet": {"pos_list": []}}}
            attrs["val"]["strSet"]["pos_list"] = value_list
        node = {"id": node_label, "type": node_type, "attrs": attrs}
        nodes.append(node)
    top_graph["nodes"] = nodes

    edges = []
    for ag_edge in hierarchy.graph['action_graph'].edges():
        source_label = label_tracker[ag_edge[0]]
        target_label = label_tracker[ag_edge[1]]
        edge = {"from": source_label, "to": target_label, "attrs": {}}
        edges.append(edge)
    top_graph["edges"] = edges

    attributes = {"name": "action_graph", "type": "graph",
                  "children_types": ["nugget", "rule", "variant"]}
    top_graph["attributes"] = attributes

    action_graph["top_graph"] = top_graph
    action_graph["children"] = []
    kami_meta_model["children"].append(action_graph)

    # Read the nuggets.
    for nugget_id in hierarchy.nugget.keys():
        nugget_graph = {}
        nugget_graph["id"] = nugget_id
        nugget_graph["name"] = nugget_id
        top_graph = {}

        nugget_graph_typing = (hierarchy
                               .typing[nugget_id]['action_graph'])
        ngt_counters = {}
        nugget_label_tracker = {}

        nodes = []
        rate = 'und'
        for nugget_node in hierarchy.graph[nugget_id].nodes():
            node_type_ag = nugget_graph_typing[nugget_node]
            node_metatype = action_graph_typing[node_type_ag]
            if node_metatype == "locus":
                node_metatype = "half-act"
            node_label, ngt_counters = find_studio_label(nugget_node,
                                                         node_metatype,
                                                         ngt_counters,
                                                         nugget_id)
            node_type_studio = label_tracker[node_type_ag]
            nugget_label_tracker[nugget_node] = node_label
            attrs = {}
            vals = "empty"
            if node_metatype == "mod":
                vals = list(hierarchy.graph[nugget_id]
                            .node[nugget_node]['value'])
            elif node_metatype == "state":
                vals = list(hierarchy.graph[nugget_id]
                            .node[nugget_node].values())[0]
            if vals != "empty":
                value_list = []
                for val in vals:
                    if val is True:
                        val = "True"
                    if val is False:
                        val = "False"
                    value_list.append(val)
                attrs = {"val": {"numSet": {"pos_list": []},
                                 "strSet": {"pos_list": []}}}
                attrs["val"]["strSet"]["pos_list"] = value_list

            node = {"id": node_label, "type": node_type_studio,
                    "attrs": attrs}
            nodes.append(node)
            # Find the rate of the nugget, which is stored in the attributes
            # of the bnd node for now.
            if node_metatype == "bnd":
                try:
                    rate_value = list(hierarchy.graph[nugget_id]
                                      .node[nugget_node]['rate'])[0]
                    if rate == 'und':
                        rate = rate_value
                    else:
                        warnings.warn(
                            "Several rates given for a single nugget.",
                            KamiWarning)
                except:
                    pass
        top_graph["nodes"] = nodes

        edges = []
        for nugget_edge in hierarchy.graph[nugget_id].edges():
            source_label = nugget_label_tracker[nugget_edge[0]]
            target_label = nugget_label_tracker[nugget_edge[1]]
            edge = {"from": source_label, "to": target_label, "attrs": {}}
            edges.append(edge)
        top_graph["edges"] = edges

        attributes = {"name": nugget_id, "type": "nugget", "rate": rate}
        top_graph["attributes"] = attributes

        nugget_graph["top_graph"] = top_graph
        nugget_graph["children"] = []
        action_graph["children"].append(nugget_graph)

    return kami_v1_dict
