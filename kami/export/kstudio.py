import math

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


def to_kamistudio(hierarchy,
                  gene_label="hgnc_symbol", region_label="label"):
    """
    Convert a Kami hierarchy to a dictionary formatted for the old KamiStudio.
    To convert a Kami model into a KamiStudio readable file:
    yourmodel = to_kamistudio(kami_hierarchy)
    json.dump(yourmodel, outfile, indent=4, sort_keys=False)
    """

    def find_studio_label(node_id, node_typ, counter_dict, graph_level):
        """
        Subfunction to find appropriate node labels based on the types
        of labels chosen on get_studio_v1 call.
        """

        label = node_typ
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
            aa = list(aa_field)[0]
            # Location is now an attribute of edges.
            out_edges = (hierarchy.graph[graph_level]
                         .edge[node_id].keys())
            aa_locations = []
            for out_edge in out_edges:
                try:
                    loc_field = (hierarchy.graph[graph_level]
                                 .edge[node_id][out_edge]["loc"])
                    aa_locations.append(list(loc_field)[0])
                except:
                    pass
            if len(aa_locations) == 0:
                loc = 'unknown'
            else:
                if len(set(aa_locations)) == 1:
                    loc = aa_locations[0]
                else:
                    loc = 'unknown'
                    warnings.warn(
                        "Conflicting information about location of residue %s."
                        % node_id, KamiWarning)
            if loc == 'unknown':
                label = '%s' % (aa)
            else:
                label = '%s%s' % (aa, loc)
        if node_typ == "state":
            field = (hierarchy.graph[graph_level]
                     .node[node_id]["name"])
            state_name = list(field)[0]
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
    for node_type in ["component", "action", "state"]:
        node = {"id": "", "type": "", "attrs": {}}
        node["id"] = node_type
        nodes.append(node)
    top_graph["nodes"] = nodes

    attrs = {}
    attrs["type"] = {"numSet": {"pos_list": []},
                     "strSet": {"pos_list": ["transitive"]}}
    edges = [{"from": "component", "to": "component", "attrs": attrs},
             {"from": "component", "to": "action",    "attrs": attrs},
             {"from": "action",    "to": "component", "attrs": attrs},
             {"from": "action",    "to": "state", "attrs": attrs},
             {"from": "state",     "to": "component", "attrs": attrs}]
    top_graph["edges"] = edges

    positions = {
        "action":    {"x": 820, "y": 530},
        "component": {"x": 620, "y": 435},
        "state":     {"x": 800, "y": 300}
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

    kami_typing = {"bnd": "action", "state": "state", "mod": "action",
                   "residue": "component", "deg": "action", "syn": "action",
                   "gene": "component", "region": "component", "site": "component"}

    nodes = []
    for kami_node in hierarchy.graph['kami'].nodes():
        node = {"id": "", "type": "", "attrs": {}}
        node_id = kami_node
        node["id"] = node_id
        node["type"] = kami_typing[node_id]
        nodes.append(node)
    top_graph["nodes"] = nodes

    edges = []
    for kami_edge in hierarchy.graph['kami'].edges():
        source = kami_edge[0]
        target = kami_edge[1]
        attrs = {}
        attrs["type"] = {"numSet": {"pos_list": []},
                         "strSet": {"pos_list": ["transitive"]}}
        edge = {"from": source, "to": target, "attrs": attrs}
        edges.append(edge)
    top_graph["edges"] = edges

    positions = {
        "bnd":      {"x": 780, "y": 500},
        "state":    {"x": 780, "y": 766},
        "mod":      {"x": 700, "y": 900},
        "residue":  {"x": 860, "y": 900},
        "deg":      {"x": 500, "y": 800},
        "syn":      {"x": 500, "y": 600},
        "gene":     {"x": 620, "y": 700},
        "region":   {"x": 940, "y": 700},
        "site":     {"x": 780, "y": 633}
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
    # Position all nodes of the action graph. Try a square lattice.
    positions = {}
    spacing = 150
    num_nodes = len(hierarchy.graph['action_graph'].nodes())
    num_col = int(math.sqrt(num_nodes))
    start_xpos, start_ypos = 0, 0
    col, row = 0, 0
    for ag_node in hierarchy.graph['action_graph'].nodes():
        node_type = action_graph_typing[ag_node]
        node_label, counters = find_studio_label(ag_node,
                                                 node_type,
                                                 counters,
                                                 "action_graph")
        label_tracker[ag_node] = node_label
        # ----- Get all attributes of the action graph node (except rate) -----
        attrs = {}
        attributes = list(hierarchy.graph['action_graph']
                        .node[ag_node].keys())
        for attribute in attributes:
            if attribute != "rate":
                attrs[attribute] = {"numSet": {"pos_list": []},
                                    "strSet": {"pos_list": []}}
                vals = list(hierarchy.graph['action_graph']
                            .node[ag_node][attribute])
                str_value_list = []
                num_value_list = []
                for val in vals:
                    if val is True:
                        val = "true"
                    if val is False:
                        val = "false"
                    try:
                        float(val)
                        num_value_list.append(val)
                    except:
                        str_value_list.append(val)
                attrs[attribute]["numSet"]["pos_list"] = num_value_list
                attrs[attribute]["strSet"]["pos_list"] = str_value_list
        # I put attributes from edges into nodes for now as there seem to be
        # a problem with edge attributes in the old regraph.
        out_edge_list = list(hierarchy.graph['action_graph']
                             .edge[ag_node].keys())
        for out_edge in out_edge_list:
            edge_str_attrs = {}
            edge_num_attrs = {}
            attributes = list(hierarchy.graph['action_graph']
                              .edge[ag_node][out_edge].keys())
            for attribute in attributes:
                if attribute != "type":
                    attrs[attribute] = {"numSet": {"pos_list": []},
                                        "strSet": {"pos_list": []}}
                    vals = list(hierarchy.graph['action_graph']
                                .edge[ag_node][out_edge][attribute])
                    # Temporary solution for when the range of a site is split
                    # between two regions. The two ranges will be displayed, but
                    # not which region each range comes from.
                    if attribute in attrs.keys():
                        str_value_list = attrs[attribute]["strSet"]["pos_list"]
                        num_value_list = attrs[attribute]["numSet"]["pos_list"]
                    else:
                        str_value_list = []
                        num_value_list = []
                    for val in vals:
                        if val is True:
                            val = "true"
                        if val is False:
                            val = "false"
                        try:
                            float(val)
                            num_value_list.append(val)
                        except:
                            str_value_list.append(val)
                    attrs[attribute]["numSet"]["pos_list"] = num_value_list
                    attrs[attribute]["strSet"]["pos_list"] = str_value_list
        # ---------------------------------------------------------
        node = {"id": node_label, "type": node_type, "attrs": attrs}
        nodes.append(node)
        # Set position of every node. Try with just a square first.
        xpos = start_xpos + col * spacing
        ypos = start_ypos + row * spacing
        positions[node_label] = {"x": xpos, "y": ypos}
        col += 1
        if col >= num_col+1:
            col = 0
            row += 1
    top_graph["nodes"] = nodes

    edges = []
    for ag_edge in hierarchy.graph['action_graph'].edges():
        source_label = label_tracker[ag_edge[0]]
        target_label = label_tracker[ag_edge[1]]
        # Uncomment when edge attributes will work in KAMIStudio
        # ----- Get all attributes of the nugget edge --------------------
        attrs = {}
        attributes = list(hierarchy.graph["action_graph"]
                          .edge[ag_edge[0]][ag_edge[1]].keys())
        for attribute in attributes:
            if attribute != "rate":
                if attribute == "type": # temporary fix
                    attrs[attribute] = {"numSet": {"pos_list": []},
                                        "strSet": {"pos_list": []}}
                    vals = list(hierarchy.graph["action_graph"]
                                .edge[ag_edge[0]][ag_edge[1]][attribute])
                    value_list = []
                    for val in vals:
                        if val is True:
                            val = "true"
                        if val is False:
                            val = "false"
                        value_list.append(val)
                    attrs[attribute]["strSet"]["pos_list"] = value_list
        # ---------------------------------------------------------
        edge = {"from": source_label, "to": target_label, "attrs": attrs}
        #edge = {"from": source_label, "to": target_label, "attrs": {}}
        edges.append(edge)
    top_graph["edges"] = edges

    attributes = {"name": "action_graph", "type": "graph",
                  "children_types": ["nugget", "rule", "variant"],
                  "positions": positions}
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
            node_label, ngt_counters = find_studio_label(nugget_node,
                                                         node_metatype,
                                                         ngt_counters,
                                                         nugget_id)
            node_type_studio = label_tracker[node_type_ag]
            nugget_label_tracker[nugget_node] = node_label

            # ----- Get all attributes of the nugget node (except rate) -----
            attrs = {}
            attributes = list(hierarchy.graph[nugget_id]
                            .node[nugget_node].keys())
            for attribute in attributes:
                if attribute != "rate":
                    attrs[attribute] = {"numSet": {"pos_list": []},
                                        "strSet": {"pos_list": []}}
                    vals = list(hierarchy.graph[nugget_id]
                                .node[nugget_node][attribute])
                    str_value_list = []
                    num_value_list = []
                    for val in vals:
                        if val is True:
                            val = "true"
                        if val is False:
                            val = "false"
                        try:
                            float(val)
                            num_value_list.append(val)
                        except:
                            str_value_list.append(val)
                    attrs[attribute]["numSet"]["pos_list"] = num_value_list
                    attrs[attribute]["strSet"]["pos_list"] = str_value_list
            # I put attributes from edges into nodes for now as there seem to be
            # a problem with edge attributes in the old regraph.
            out_edge_list = list(hierarchy.graph[nugget_id]
                                 .edge[nugget_node].keys())
            for out_edge in out_edge_list:
                edge_str_attrs = {}
                edge_num_attrs = {}
                attributes = list(hierarchy.graph[nugget_id]
                                  .edge[nugget_node][out_edge].keys())
                for attribute in attributes:
                    attrs[attribute] = {"numSet": {"pos_list": []},
                                        "strSet": {"pos_list": []}}
                    vals = list(hierarchy.graph[nugget_id]
                                .edge[nugget_node][out_edge][attribute])
                    # Temporary solution for when the range of a site is split
                    # between two regions. The two ranges will be displayed, but
                    # not which region each range comes from.
                    if attribute in attrs.keys():
                        str_value_list = attrs[attribute]["strSet"]["pos_list"]
                        num_value_list = attrs[attribute]["numSet"]["pos_list"]
                    else:
                        str_value_list = []
                        num_value_list = []
                    for val in vals:
                        if val is True:
                            val = "true"
                        if val is False:
                            val = "false"
                        try:
                            float(val)
                            num_value_list.append(val)
                        except:
                            str_value_list.append(val)
                    attrs[attribute]["numSet"]["pos_list"] = num_value_list
                    attrs[attribute]["strSet"]["pos_list"] = str_value_list
            # ---------------------------------------------------------
            node = {"id": node_label, "type": node_type_studio,
                    "attrs": attrs}
            nodes.append(node)
            # Find the rate of the nugget, which is stored in the attributes
            # of the bnd or mod.
            if node_metatype == "bnd" or node_metatype == "mod":
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
            ## Uncomment when edge attributes will work in KAMIStudio
            ## ----- Get all attributes of the nugget edge --------------------
            #attrs = {}
            #attributes = list(hierarchy.graph[nugget_id]
            #                  .edge[nugget_edge[0]][nugget_edge[1]].keys())
            #for attribute in attributes:
            #    if attribute != "rate":
            #        attrs[attribute] = {"numSet": {"pos_list": []},
            #                            "strSet": {"pos_list": []}}
            #        vals = list(hierarchy.graph[nugget_id]
            #                    .edge[nugget_edge[0]][nugget_edge[1]][attribute])
            #        value_list = []
            #        for val in vals:
            #            if val is True:
            #                val = "true"
            #            if val is False:
            #                val = "false"
            #            value_list.append(val)
            #        attrs[attribute]["strSet"]["pos_list"] = value_list
            ## ---------------------------------------------------------
            #edge = {"from": source_label, "to": target_label, "attrs": attrs}
            edge = {"from": source_label, "to": target_label, "attrs": {}}
            edges.append(edge)
        top_graph["edges"] = edges

        attributes = {"name": nugget_id, "type": "nugget", "rate": rate}
        top_graph["attributes"] = attributes

        nugget_graph["top_graph"] = top_graph
        nugget_graph["children"] = []
        action_graph["children"].append(nugget_graph)

    return kami_v1_dict
