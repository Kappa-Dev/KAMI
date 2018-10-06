import math
import json
import warnings
import networkx as nx
from regraph.rules import Rule
from regraph.primitives import (add_nodes_from,
                                add_edges_from)
from kami.exceptions import (KamiError,
                             KamiWarning)

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

def find_label(hierarchy, node_id, node_typ, counter_dict, graph_level,
               gene_label, region_label):
    """Find appropriate node labels based on the types of label chosen."""

    label = node_typ
    if node_typ == "gene":
        try:
            field = (hierarchy.graph[graph_level]
                     .node[node_id]["label"])
        except:
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


def export_model(hierarchy,
                 gene_label="hgnc_symbol", region_label="label",
                 newlayout=None, prevlayout=None):
    """
    Convert a Kami hierarchy to a dictionary formatted for the old KamiStudio.
    To convert a Kami model into a KamiStudio readable file:
    yourmodel = to_kamistudio(kami_hierarchy)
    json.dump(yourmodel, outfile, indent=4, sort_keys=False)
    If I use a newlayout created with function create_layout, the keys of the
    dict are node ids. If I use a prevlayout, the keys are rather node labels.
    """

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

    # Place nodes according to input file.
    if prevlayout != None:
        ag = prevlayout["children"][0]["children"][0]["children"][0]
        prevpos = ag["top_graph"]["attributes"]["positions"]

    nodes = []
    positions = {}
    for ag_node in hierarchy.graph['action_graph'].nodes():
        node_type = action_graph_typing[ag_node]
        node_label, counters = find_label(hierarchy, ag_node, node_type,
                                          counters, "action_graph",
                                          gene_label, region_label)
        label_tracker[ag_node] = node_label
        # ----- Get all attributes of the action graph node (except rate) -----
        attrs = {}
        attributes = list(hierarchy.graph['action_graph']
                        .node[ag_node].keys())
        for attribute in attributes:
            if attribute != "rate" and attribute != "label":
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
        # I put ranges from edges into nodes for now as there seem to be
        # a problem with edge numeric attributes in the old regraph.
        out_edge_list = list(hierarchy.graph['action_graph']
                             .edge[ag_node].keys())
        for out_edge in out_edge_list:
            edge_str_attrs = {}
            edge_num_attrs = {}
            attributes = list(hierarchy.graph['action_graph']
                              .edge[ag_node][out_edge].keys())
            for attribute in attributes:
                if attribute == "start" or attribute == "end":
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
        # Set position of every node according to given layout file.
        if newlayout != None:
            try:
                positions[node_label] = newlayout[ag_node]
            except:
                pass
        if prevlayout != None:
            try:
                positions[node_label] = prevpos[node_label]
            except:
                pass

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
        nugget_graph["name"] = hierarchy.node[nugget_id].attrs["desc"]
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
            node_label, ngt_counters = find_label(hierarchy, nugget_node,
                                                  node_metatype,
                                                  ngt_counters, nugget_id,
                                                  gene_label, region_label)
            node_type_studio = label_tracker[node_type_ag]
            nugget_label_tracker[nugget_node] = node_label

            # ----- Get all attributes of the nugget node (except rate) -----
            attrs = {}
            attributes = list(hierarchy.graph[nugget_id]
                            .node[nugget_node].keys())
            for attribute in attributes:
                if attribute != "rate" and attribute != "label":
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
            # I put ranges from edges into nodes for now as there seem to be
            # a problem with edge numeric attributes in the old regraph.
            out_edge_list = list(hierarchy.graph[nugget_id]
                                 .edge[nugget_node].keys())
            for out_edge in out_edge_list:
                edge_str_attrs = {}
                edge_num_attrs = {}
                attributes = list(hierarchy.graph[nugget_id]
                                  .edge[nugget_node][out_edge].keys())
                for attribute in attributes:
                    if attribute == "start" or attribute == "end":
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

        # ====== Build a simple layout for nuggets. =====

        positions = {}
        placed_nodes = []
        # Search for the action node and put it at the center.
        edge_list = hierarchy.graph[nugget_id].edges()
        test_node = None
        for nugget_edge in edge_list:
            ag_source_type = nugget_graph_typing[nugget_edge[0]]
            source_type = action_graph_typing[ag_source_type]
            ag_target_type = nugget_graph_typing[nugget_edge[1]]
            target_type = action_graph_typing[ag_target_type]
            if source_type == "mod":
                act_node = nugget_edge[0]
                nug_type = "modif"
            if target_type == "bnd":
                attribs = hierarchy.graph[nugget_id].node[nugget_edge[1]]
                act_type = list(attribs["type"])[0]
                if act_type == "do":
                    act_node = nugget_edge[1]
                    nug_type = "binding"
                if act_type == "be":
                    test_node = nugget_edge[1]
        act_label = nugget_label_tracker[act_node]

        # Position nodes for a binding nugget.
        if nug_type == "binding":
            positions[act_label] = {"x": 0.0, "y": 0.0}
            placed_nodes.append(act_node)
            # Find the nodes that connect to the bnd node.
            side = "left"
            for nugget_edge in edge_list:
                if nugget_edge[1] == act_node:
                    if side == "left":
                        left_actor = nugget_edge[0]
                        side = "right"
                    else:
                        right_actor = nugget_edge[0]
            left_label = nugget_label_tracker[left_actor]
            right_label = nugget_label_tracker[right_actor]
            positions[left_label]  = {"x": -200, "y": 0}
            placed_nodes.append(left_actor)
            positions[right_label] = {"x":  200, "y": 0}
            placed_nodes.append(right_actor)
            # Left path to gene.
            x_del = -100
            x_pos = -200
            component = left_actor
            while component != None:
                next_component = None
                for nugget_edge in edge_list:
                    if nugget_edge[0] == component:
                        # Check the type of the outgoing node.
                        # Ignore test nodes at that point.
                        ag_target_type = nugget_graph_typing[nugget_edge[1]]
                        target_type = action_graph_typing[ag_target_type]
                        if target_type != "mod" and target_type != "bnd":
                            next_component = nugget_edge[1]
                            x_pos = x_pos + x_del
                            next_label = nugget_label_tracker[next_component]
                            positions[next_label] = {"x": x_pos, "y": 0}
                            placed_nodes.append(next_component)
                component = next_component
            # Right path to gene.
            x_del = 100
            x_pos = 200
            component = right_actor
            while component != None:
                next_component = None
                for nugget_edge in edge_list:
                    if nugget_edge[0] == component:
                        # Check the type of the outgoing node.
                        # Ignore test nodes at that point.
                        ag_target_type = nugget_graph_typing[nugget_edge[1]]
                        target_type = action_graph_typing[ag_target_type]
                        if target_type != "mod" and target_type != "bnd":
                            next_component = nugget_edge[1]
                            x_pos = x_pos + x_del
                            next_label = nugget_label_tracker[next_component]
                            positions[next_label] = {"x": x_pos, "y": 0}
                            placed_nodes.append(next_component)
                component = next_component
        # Position nodes for a modification nugget.
        if nug_type == "modif":
            # Place the test node if there is one. Proceed like for the
            # binding nugget for this part.
            x_left = -200
            x_right = 200
            if test_node != None:
                test_label = nugget_label_tracker[test_node]
                positions[test_label] = {"x": 0, "y": 0}
                placed_nodes.append(test_node)
                # Find the nodes that connect to the bnd node.
                side = "left"
                for nugget_edge in edge_list:
                    if nugget_edge[1] == test_node:
                        if side == "left":
                            left_actor = nugget_edge[0]
                            side = "right"
                        else:
                            right_actor = nugget_edge[0]
                left_label = nugget_label_tracker[left_actor]
                right_label = nugget_label_tracker[right_actor]
                positions[left_label]  = {"x": -200, "y": 0}
                placed_nodes.append(left_actor)
                positions[right_label] = {"x":  200, "y": 0}
                placed_nodes.append(right_actor)
                # Left path to gene.
                x_del = -100
                x_pos = -200
                component = left_actor
                while component != None:
                    next_component = None
                    for nugget_edge in edge_list:
                        if nugget_edge[0] == component:
                            # Check the type of the outgoing node.
                            # Ignore test nodes at that point.
                            ag_target_type = nugget_graph_typing[nugget_edge[1]]
                            target_type = action_graph_typing[ag_target_type]
                            if target_type != "mod" and target_type != "bnd":
                                next_component = nugget_edge[1]
                                x_pos = x_pos + x_del
                                next_label = nugget_label_tracker[next_component]
                                positions[next_label] = {"x": x_pos, "y": 0}
                                placed_nodes.append(next_component)
                    component = next_component
                x_left = x_pos
                # Right path to gene.
                x_del = 100
                x_pos = 200
                component = right_actor
                while component != None:
                    next_component = None
                    for nugget_edge in edge_list:
                        if nugget_edge[0] == component:
                            # Check the type of the outgoing node.
                            # Ignore test nodes at that point.
                            ag_target_type = nugget_graph_typing[nugget_edge[1]]
                            target_type = action_graph_typing[ag_target_type]
                            if target_type != "mod" and target_type != "bnd":
                                next_component = nugget_edge[1]
                                x_pos = x_pos + x_del
                                next_label = nugget_label_tracker[next_component]
                                positions[next_label] = {"x": x_pos, "y": 0}
                                placed_nodes.append(next_component)
                    component = next_component
                x_right = x_pos
            # Then position the action node.
            # Find the nodes that connect to the bnd node.
            left_actor = None
            for nugget_edge in edge_list:
                if nugget_edge[1] == act_node:
                        left_actor = nugget_edge[0]
                if nugget_edge[0] == act_node:
                        right_actor = nugget_edge[1]
            # Left path to gene. There is no left actor for
            # AnonymousModification
            if left_actor == None:
                positions[act_label] = {"x": 100.0, "y": -300.0}
                placed_nodes.append(act_node)
            if left_actor != None:
                positions[act_label] = {"x": 0.0, "y": -200.0}
                left_label = nugget_label_tracker[left_actor]
                positions[left_label]  = {"x": x_left, "y": -100}
                placed_nodes.append(left_actor)
                x_pos = x_left
                y_pos = -100
                x_del = 0
                y_del = 100
                component = left_actor
                while component != None:
                    next_component = None
                    for nugget_edge in edge_list:
                        if nugget_edge[0] == component:
                            # Check the type of the outgoing node.
                            # Ignore test nodes at that point.
                            ag_target_type = nugget_graph_typing[nugget_edge[1]]
                            target_type = action_graph_typing[ag_target_type]
                            if target_type != "mod" and target_type != "bnd":
                                next_component = nugget_edge[1]
                                x_pos = x_pos + x_del
                                y_pos = y_pos + y_del
                                next_label = nugget_label_tracker[next_component]
                                positions[next_label] = {"x": x_pos, "y": y_pos}
                                placed_nodes.append(next_component)
                    component = next_component
            # Right path to gene.
            # right_actor is necessarily a state.
            # I need to know if the state links to a residue
            # or directly to an actor before I place it.
            right_label = nugget_label_tracker[right_actor]
            for nugget_edge in edge_list:
                if nugget_edge[0] == right_actor:
                    state_target = nugget_edge[1]
                    target_label = nugget_label_tracker[state_target]
                    ag_target_type = nugget_graph_typing[state_target]
                    target_type = action_graph_typing[ag_target_type]
            if target_type == "residue":
                positions[right_label]  = {"x": x_right, "y": -300}
                placed_nodes.append(right_actor)
                positions[target_label] = {"x": x_right, "y": -200}
                placed_nodes.append(state_target)
                for nugget_edge in edge_list:
                        if nugget_edge[0] == state_target:
                            new_target = nugget_edge[1]
                            new_label = nugget_label_tracker[new_target]
                            positions[new_label] = {"x": x_right, "y": -100}
                            placed_nodes.append(new_target)
                component = new_target
            else:
                positions[right_label] = {"x": x_right, "y": -200}
                placed_nodes.append(right_actor)
                positions[target_label] = {"x": x_right, "y": -100}
                placed_nodes.append(state_target)
                component = state_target
            x_pos = x_right
            y_pos = -100
            x_del = 0
            y_del = 100
            while component != None:
                next_component = None
                for nugget_edge in edge_list:
                    if nugget_edge[0] == component:
                        # Check the type of the outgoing node.
                        # Ignore test nodes at that point.
                        ag_target_type = nugget_graph_typing[nugget_edge[1]]
                        target_type = action_graph_typing[ag_target_type]
                        if target_type != "mod" and target_type != "bnd":
                            next_component = nugget_edge[1]
                            x_pos = x_pos + x_del
                            y_pos = y_pos + y_del
                            next_label = nugget_label_tracker[next_component]
                            positions[next_label] = {"x": x_pos, "y": y_pos}
                            placed_nodes.append(next_component)
                component = next_component
            # Check that the test node is still
            # at the same height as its actors.
            if test_node != None:
                for nugget_edge in edge_list:
                    if nugget_edge[1] == test_node:
                        left_actor = nugget_edge[0]
                        break
                left_label = nugget_label_tracker[left_actor]
                x_pos = positions[test_label]["x"]
                y_pos = positions[left_label]["y"]
                positions[test_label] = {"x": x_pos, "y": y_pos}

        # Place nodes that still do not have a position in a
        # perpendicular orientation.
        remaining_nodes_tmp = []
        for nugget_edge in edge_list:
            for i in range(2):
                if nugget_edge[i] not in placed_nodes:
                    remaining_nodes_tmp.append(nugget_edge[i])
        remaining_nodes = list(set(remaining_nodes_tmp))
        while len(remaining_nodes) > 0:
            for remaining_node in remaining_nodes:
                remaining_label = nugget_label_tracker[remaining_node]
                # Check edges to and from that remaining node.
                has_edges = []
                for nugget_edge in edge_list:
                    if nugget_edge[1] == remaining_node:
                        has_edges.append(nugget_edge[0])
                    if nugget_edge[0] == remaining_node:
                        has_edges.append(nugget_edge[1])
                if len(has_edges) > 0:
                    # Find the position of connected nodes if any.
                    pos_defined = []
                    for a_node in has_edges:
                        if a_node in placed_nodes:
                            a_label = nugget_label_tracker[a_node]
                            pos_defined.append(positions[a_label])
                    if len(pos_defined) == 1:
                        positions[remaining_label] = {"x": pos_defined[0]["x"],
                                                      "y": pos_defined[0]["y"] - 100}
                        placed_nodes.append(remaining_node)
                    if len(pos_defined) == 2:
                        com_x = (pos_defined[0]["x"] + pos_defined[1]["x"])/2.
                        com_y = (pos_defined[0]["y"] + pos_defined[1]["y"])/2.
                        positions[remaining_label] = {"x": com_x, "y": com_y}
                        placed_nodes.append(remaining_node)
            still_remaining_nodes = []
            for remaining_node in remaining_nodes:
                if remaining_node not in placed_nodes:
                    still_remaining_nodes.append(remaining_node)
            remaining_nodes = still_remaining_nodes
        # ===================================================

        attributes = {"name": nugget_id, "type": "nugget", "rate": rate,
                      "positions": positions}
        top_graph["attributes"] = attributes

        nugget_graph["top_graph"] = top_graph
        nugget_graph["children"] = []
        action_graph["children"].append(nugget_graph)

    return kami_v1_dict


def create_layout(hierarchy,
              gene_label="hgnc_symbol", region_label="label", groups=None,
              grid_spacing=800, component_radius=80):
    """
    Outputs a dictionay with the x and y position of every node. By default,
    every gene is put on a grid and every structural component of a gene is
    positioned around that gene. Optionally, groups of genes can be given as a
    list of group objects. Group objects must be dictionaries formated like:
    {"genes": [ABL1, STAT5, ...], "center": {"x": 100, "y": 100}, "rows": 2}.
    The output of ag_layout can be passed to function to_kamistudio so that 
    the action graph can be visualized with the specified layout.
    """

    # The layout dict looks like { EGFR: {x: 12, y: 53}, HCK: {x: 27, y:32} }
    layout = {}

    # Find every gene that is present in the model. Also get their
    # labels and ids.
    identifiers = {}
    gene_list = []
    action_graph_typing = hierarchy.typing['action_graph']['kami']
    for ag_node in hierarchy.graph['action_graph'].nodes():
        if action_graph_typing[ag_node] == "gene":
            node_info = hierarchy.graph['action_graph'].node[ag_node]
            try:
                label = (list(node_info[gene_label])[0])
            except:
                label = (list(node_info["uniprotid"])[0])
            gene_list.append(label)
            identifiers[label] = ag_node
    gene_sort = sorted(gene_list)

    # Place the genes that are present in predefined groups.
    x_max = 0
    y_min = 0
    placed_genes = []
    if groups != None:
        x_max = -float("inf")
        y_min = float("inf")
        for group in groups:
            genes = group["genes"]
            num_genes = len(genes)
            center_x = group["center"]["x"]
            center_y = group["center"]["y"]
            try:
                num_rows = group["rows"]
            except:
                num_rows = "square"
            if num_rows != "square":
                num_cols = int(num_genes/num_rows)
            else:
               num_cols = int(math.sqrt(num_genes))
            start_xpos = center_x - (num_cols-1)/2 * grid_spacing
            start_ypos = center_y - (num_rows-1)/2 * grid_spacing
            col, row = 0, 0
            for gene in genes:
                # Ignore genes that are in predefined groups but absent
                # in the model.
                if gene in gene_sort:
                    xpos = start_xpos + col * grid_spacing
                    ypos = start_ypos + row * grid_spacing
                    node_id = identifiers[gene]
                    layout[node_id] = {"x": xpos, "y": ypos}
                    col += 1
                    if col >= num_cols:
                        col = 0
                        row += 1
                    placed_genes.append(gene)
                    # Keep track of the end of the layout.
                    if xpos > x_max:
                        x_max = xpos
                    if ypos < y_min:
                        y_min = ypos
                else:
                    warnings.warn(
                        "Gene %s from layout groups is absent in the action graph."
                        % gene, KamiWarning)
        x_max = x_max + 3*grid_spacing


    # Place genes that were not present in predefined groups at the far right.
    remaining_genes = []
    for gene in gene_sort:
        if gene not in placed_genes:
            remaining_genes.append(gene)
    num_genes = len(remaining_genes)
    num_col = int(math.sqrt(num_genes))
    start_xpos = x_max
    start_ypos = y_min
    col, row = 0, 0
    for gene in remaining_genes:
        xpos = start_xpos + col * grid_spacing
        ypos = start_ypos + row * grid_spacing
        node_id = identifiers[gene]
        layout[node_id] = {"x": xpos, "y": ypos}
        col += 1
        if col >= num_col+1:
            col = 0
            row += 1

    # Then, put the structural component of every gene around it.
    # I need to use edges to find which component belongs to each gene.
    # Follow ingoing edges but stop if I reach a mod node.
    edge_list = hierarchy.graph['action_graph'].edges()
    for gene in gene_sort:
        node_id = identifiers[gene]
        # Loops to position every structural elements around a 
        placed_components = [node_id]
        layer = 1
        while len(placed_components) > 0:
            next_components = []
            for placed_component in placed_components:
                component_pos = layout[placed_component]
                # Find components attached to an already placed component
                # using incoming edges.
                new_components = []
                for edge in edge_list:
                    if edge[1] == placed_component:
                        # Exclude transitive edges from seach.
                        try:
                            edge_type = list(hierarchy.graph['action_graph'].edge[edge[0]][edge[1]]["type"])[0]
                        except:
                            edge_type = "direct"
                        if edge_type != "transitive":
                            new_component = edge[0]
                            # Exclude mod or bnd nodes.
                            new_component_type = action_graph_typing[new_component]
                            if new_component_type != "mod" and new_component_type != "bnd":
                               new_components.append(new_component)
                if len(new_components) > 0:
                    # Place every new component around the already placed component.
                    if layer == 1:
                        # Zero degree is pointing to the right and 
                        # we rotate clockwise.
                        angle = 0
                        delta = 360. / len(new_components)
                        side = 1
                    else:
                        # First, find the orientation relative to the previous component.
                        previous_components = []
                        for edge in edge_list:
                            if edge[0] == placed_component:
                                previous_component = edge[1]
                                previous_component_type = action_graph_typing[previous_component]
                                if previous_component_type != "mod" and previous_component_type != "bnd":
                                    previous_components.append(previous_component)
                        previous_x = 0
                        previous_y = 0
                        for previous_component in previous_components:
                           previous_x += layout[previous_component]["x"]
                           previous_y += layout[previous_component]["y"]
                        n_components = len(previous_components)
                        previous_pos = {"x": previous_x/n_components, "y": previous_y/n_components}
                        ori_x = component_pos["x"] - previous_pos["x"]
                        ori_y = component_pos["y"] - previous_pos["y"]
                        if ori_x == 0 and ori_y == 0:
                            ori_angle = 0
                            side = 1
                        elif ori_x == 0:
                            ori_angle = 180 + (ori_y/abs(ori_y))*90
                            side = -1
                        elif ori_y == 0:
                            ori_angle = 0
                            side = ori_x / abs(ori_x)
                        else:
                            ori_angle = math.atan(ori_y/ori_x)*180/math.pi
                            side = ori_x / abs(ori_x)
                        delta = 180. / (len(new_components) + 1)
                        angle = ori_angle - 90 + delta

                    for new_component in new_components:
                        xvect = math.cos(angle*math.pi/180)*side
                        yvect = math.sin(angle*math.pi/180)*side
                        xpos = component_pos["x"] + (xvect * component_radius)
                        ypos = component_pos["y"] + (yvect * component_radius)
                        layout[new_component] = {"x": xpos, "y": ypos}
                        angle += delta
                        next_components.append(new_component)
            # All components of that layer are placed, ready for next loop.
            placed_components = next_components
            layer += 1

    # Finally, put the action nodes between the nodes that they link.
    for ag_node in hierarchy.graph['action_graph'].nodes():
        node_type = action_graph_typing[ag_node]
        if node_type == "bnd" or node_type == "mod":
            source_list = []
            for edge in edge_list:
                if edge[1] == ag_node:
                    source_list.append(edge[0])
                if edge[0] == ag_node:
                    source_list.append(edge[1])
            # Get the center of mass of every source node.
            if len(source_list) > 0:
                sum_x = 0
                sum_y = 0
                for source_node in source_list:
                    sum_x += layout[source_node]["x"]
                    sum_y += layout[source_node]["y"]
                n_source = len(source_list)
                com_x = sum_x / n_source
                com_y = sum_y / n_source
                layout[ag_node] = {"x": com_x, "y": com_y}
            else:
                layout[ag_node] = {"x": 0, "y": 0}

    return layout

# ============= Custom node merging functions ===============
def merge_actions(hierarchy, same_genes=False):
    """
    Merge action nodes that are of same type (mod or bnd) and that are
    connected to the same component nodes.
    """
    # If same_genes is set to True, further merge them also if they are
    # connected to the same genes.
    node_list = hierarchy.graph["action_graph"].nodes()
    edge_list = hierarchy.graph['action_graph'].edges()
    action_graph_typing = hierarchy.typing['action_graph']['kami']
    action_groups = get_action_groups(hierarchy, action_graph_typing,
                                      node_list, edge_list, same_genes)
    for node_group in action_groups:
        if len(node_group) > 1:
            ag_merge(hierarchy, node_group)

def get_action_groups(hierarchy, ag_typing, nod_list, edg_list, same_genes):
    """ Create the groups of action nodes that will have to be merged."""
    # Get the genes that are connected to every action node.
    bnd_dict = {}
    mod_dict = {}
    ano_dict = {}
    for ag_node in nod_list:
        node_type = ag_typing[ag_node]
        if node_type == "bnd":
            if same_genes == True:
                nodes = find_connected_genes(hierarchy, ag_typing,
                                             edg_list, ag_node)
            else:
                nodes = find_connected_nodes(hierarchy,
                                             edg_list, ag_node)
            bnd_dict[ag_node] = nodes
        if node_type == "mod":
            if same_genes == True:
                nodes = find_connected_genes(hierarchy, ag_typing,
                                             edg_list, ag_node)
            else:
                nodes = find_connected_nodes(hierarchy,
                                             edg_list, ag_node)
            # if mod node has no incoming edge, then
            # it is an anonymous modification.
            anonymous = True
            for edge in edg_list:
                if edge[1] == ag_node:
                    anonymous = False
                    break
            if anonymous == True:
                ano_dict[ag_node] = nodes
            else:
                mod_dict[ag_node] = nodes
    action_groups = action_node_groups(bnd_dict, mod_dict, ano_dict)
    return action_groups

def find_connected_nodes(hierarchy, edg_list, node_id):
    """
    Find every node directly connected to a given action node.
    """
    actor_nodes = []
    actor = None
    for edge in edg_list:
        if edge[0] == node_id:
            actor = edge[1]
        if edge[1] == node_id:
            actor = edge[0]
        if actor != None:
            actor_nodes.append(actor)
        actor = None
    actor_set = list(set(actor_nodes))
    actor_sort = sorted(actor_set)
    return actor_sort


def find_connected_genes(hierarchy, ag_typing, edg_list, node_id):
    """
    Find every gene connecting to a given action node.
    Inspired of function findGeneNode from InteractiveGraph.js.
    """
    seen_nodes = []
    actor = None
    for edge in edg_list:
        if edge[0] == node_id:
            actor = edge[1]
        if edge[1] == node_id:
            actor = edge[0]
        # Find every gene that is connected to the actor
        # (there may be more than one with composed sites)
        if actor != None:
            actors = [actor]
            seen_nodes.append(actor)
            while len(actors) > 0:
                target_nodes = []
                next_step = []
                for edge in edg_list:
                    if edge[0] in actors:
                        target_type = ag_typing[edge[1]]
                        if target_type != "bnd" and target_type != "mod":
                            target_nodes.append(edge[1])
                for target_node in target_nodes:
                    if target_node not in seen_nodes:
                        seen_nodes.append(target_node)
                    if target_node not in next_step:
                        next_step.append(target_node)
                actors = next_step
        actor = None
    gene_nodes = []
    for seen_node in seen_nodes:
        target_type = ag_typing[seen_node]
        if target_type == "gene":
            gene_nodes.append(seen_node)
    gene_set = list(set(gene_nodes))
    gene_sort = sorted(gene_set)
    return gene_sort

def action_node_groups(bnd_dico, mod_dico, ano_dico):
    """
    Find every action node than connect to the same elements and group them.
    """
    node_groups = []
    for action_dict in [bnd_dico, mod_dico]:
        seen_keys = []
        for action_node1 in action_dict.keys():
            if action_node1 not in seen_keys:
                seen_keys.append(action_node1)
                node_group = [action_node1]
                for action_node2 in action_dict.keys():
                    if action_node2 not in seen_keys:
                        if action_dict[action_node1] == action_dict[action_node2]:
                            node_group.append(action_node2)
                            seen_keys.append(action_node2)
                node_groups.append(node_group)
    return node_groups

def ag_merge(hierarchy, to_merge_list):
    """ Merge all the nodes in the to_merge_list inside the action_graph."""
    pattern = nx.DiGraph()
    add_nodes_from(pattern, to_merge_list)
    node_merge_rule = Rule.from_transform(pattern)
    node_merge_rule.inject_merge_nodes(to_merge_list)
    hierarchy.rewrite("action_graph", node_merge_rule)

# =========================================================
