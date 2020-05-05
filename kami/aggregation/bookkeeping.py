"""Collection of bookkeeping updates."""
import warnings

import regraph

from anatomizer import fetch_gene_meta_data, fetch_gene_domains
from kami.data_structures.entities import Region
from kami.aggregation.identifiers import find_fragment
from kami.exceptions import KamiHierarchyWarning
from kami.utils.id_generators import generate_new_id


def merge_residues(identifier, protoform):
    """Merge residues of the same location."""
    residues = identifier.get_attached_residues(protoform)
    locs = {}
    # group residues by their location
    for res in residues:
        loc = None
        res_gene_edge = identifier.graph.get_edge(res, protoform)
        if "loc" in res_gene_edge.keys():
            loc = list(res_gene_edge["loc"])[0]
        if loc is not None:
            if loc in locs.keys():
                locs[loc].append(res)
            else:
                locs[loc] = [res]

    for k, v in locs.items():
        if len(v) > 1:
            # merges these residues
            if identifier.hierarchy:
                pattern = regraph.NXGraph()
                pattern.add_nodes_from(v)
                rule = regraph.Rule.from_transform(pattern)
                rule.inject_merge_nodes(v)

                protoform_attrs = identifier.graph.get_node(protoform)
                uniprot = list(protoform_attrs["uniprotid"])[0]
                message = (
                    "Merged residues with the same location '{}' ".format(
                        k) +
                    "of the protoform with the UniProtAC '{}'".format(uniprot)
                )

                identifier.rewrite_graph(
                    rule,
                    message=message,
                    update_type="auto")
            else:
                identifier.graph.merge_nodes(v)


def reconnect_residues(identifier, protoform, residues,
                       regions=None, sites=None):
    """Reconnect residues of a protoform to regions/sites of compatible range."""
    for res in residues:
        loc = None
        res_gene_edge = identifier.graph.get_edge(res, protoform)
        if "loc" in res_gene_edge.keys():
            loc = list(res_gene_edge["loc"])[0]
        if loc is not None:
            region_dict = {}
            if regions is not None:
                for region in regions:
                    region_gene_edge = identifier.graph.get_edge(region, protoform)
                    if "start" in region_gene_edge and\
                       "end" in region_gene_edge:
                        start = min(
                            region_gene_edge["start"])
                        end = max(
                            region_gene_edge["end"])
                        region_dict[region] = (start, end)

            site_dict = {}
            if sites is not None:
                for site in sites:
                    site_gene_edge = identifier.graph.get_edge(site, protoform)
                    if "start" in site_gene_edge and\
                       "end" in site_gene_edge:
                        start = min(
                            site_gene_edge["start"])
                        end = max(
                            site_gene_edge["end"])
                        site_dict[site] = (start, end)

            for region, (start, end) in region_dict.items():
                if int(loc) >= start and\
                   int(loc) <= end and\
                   (res, region) not in identifier.graph.edges():
                    identifier.graph.add_edge(
                        res, region, {"loc": loc})
                    identifier.graph.add_edge_attrs(
                        res, protoform, {"type": "transitive"})

            for site, (start, end) in site_dict.items():
                if int(loc) >= start and\
                   int(loc) <= end and\
                   (res, site) not in identifier.graph.edges():
                    for suc in identifier.graph.successors(res):
                        if identifier.meta_typing[suc] != "site":
                            if identifier.meta_typing[suc] == "region" and\
                               suc in identifier.graph.successors(site):
                                identifier.graph.add_edge_attrs(
                                    res, suc, {"type": "transitive"})
                    identifier.graph.add_edge_attrs(
                        res, protoform, {"type": "transitive"})
                    identifier.graph.add_edge(res, site, {"loc": loc})


def reconnect_sites(identifier, protoform, sites, regions):
    """Reconnect sites of a protoform to regions of compatible range."""
    for site in sites:
        start = None
        end = None
        site_gene_edge = identifier.graph.get_edge(site, protoform)
        if "start" in site_gene_edge.keys():
            start = list(site_gene_edge["start"])[0]
        if "end" in site_gene_edge.keys():
            end = list(site_gene_edge["end"])[0]

        if start is not None and end is not None:
            for region in regions:
                region_gene_edge = identifier.graph.get_edge(region, protoform)
                if "start" in region_gene_edge and\
                   "end" in region_gene_edge:
                    region_start = min(
                        region_gene_edge["start"])
                    region_end = max(
                        region_gene_edge["end"])
                    if int(start) >= region_start and\
                       int(end) <= region_end and\
                       (site, region) not in identifier.graph.edges():
                        identifier.graph.add_edge(
                            site, region,
                            {"start": start, "end": end})
                        identifier.graph.add_edge_attrs(
                            site, protoform, {"type": "transitive"})


def connect_transitive_components(identifier, new_nodes):
    """Add edges between components connected transitively."""
    gene_region_site = regraph.NXGraph()
    gene_region_site.add_nodes_from(["protoform", "region", "site"])
    gene_region_site.add_edges_from([("region", "protoform"), ("site", "region")])
    gene_region_site_rule = regraph.Rule.from_transform(gene_region_site)
    gene_region_site_rule.inject_add_edge("site", "protoform")
    lhs_typing = {
        "protoform": "protoform", "region": "region", "site": "site"
    }

    instances = identifier.find_matching_in_graph(
        gene_region_site_rule.lhs,
        lhs_typing,
        new_nodes)

    for instance in instances:
        if not identifier.graph.exists_edge(
           instance["site"], instance["protoform"]):
            edge_attrs = dict()
            edge_attrs.update(identifier.graph.get_edge(
                instance["site"],
                instance["region"]))
            edge_attrs["type"] = "transitive"
            gene_region_site_rule.rhs.set_edge("site", "protoform", edge_attrs)

            message = (
                "Reconnected transitive components: pattern "
                "'Protoform<-Region<-Site(ID '{}'), created Protoform<-Site".format(
                    instance["site"])
            )

            identifier.rewrite_graph(
                gene_region_site_rule, instance,
                message=message, update_type="auto")

    region_site_residue = regraph.NXGraph()
    region_site_residue.add_nodes_from(["region", "site", "residue"])
    region_site_residue.add_edges_from(
        [("site", "region"), ("residue", "site")])
    region_site_residue_rule = regraph.Rule.from_transform(region_site_residue)
    region_site_residue_rule.inject_add_edge("residue", "region")
    lhs_typing = {
        "region": "region", "site": "site", "residue": "residue"
    }

    instances = identifier.find_matching_in_graph(
        region_site_residue_rule.lhs,
        lhs_typing,
        new_nodes)

    for instance in instances:
        if not identifier.graph.exists_edge(
                instance["residue"], instance["region"]):
            edge_attrs = dict()
            edge_attrs.update(identifier.graph.get_edge(
                instance["residue"],
                instance["site"]))
            edge_attrs["type"] = "transitive"
            region_site_residue_rule.rhs.set_edge(
                "residue", "region", edge_attrs)

            message = (
                "Reconnected transitive components: pattern "
                "'Region<-Site<-Residue(ID '{}'), created Region<-Residue".format(
                    instance["residue"])
            )
            identifier.rewrite_graph(
                region_site_residue_rule, instance,
                message=message, update_type="auto")

    gene_region_residue = regraph.NXGraph()
    gene_region_residue.add_nodes_from(["protoform", "region", "residue"])
    gene_region_residue.add_edges_from(
        [("region", "protoform"), ("residue", "region")])
    gene_region_residue_rule = regraph.Rule.from_transform(gene_region_residue)
    gene_region_residue_rule.inject_add_edge(
        "residue", "protoform")
    lhs_typing = {
        "protoform": "protoform", "region": "region", "residue": "residue"
    }

    instances = identifier.find_matching_in_graph(
        gene_region_residue_rule.lhs,
        lhs_typing,
        new_nodes)

    for instance in instances:
        if not identifier.graph.exists_edge(
                instance["residue"], instance["protoform"]):

            edge_attrs = dict()
            edge_attrs.update(identifier.graph.get_edge(
                instance["residue"], instance["region"]))
            edge_attrs["type"] = "transitive"
            gene_region_residue_rule.rhs.set_edge("residue", "protoform", edge_attrs)
            message = (
                "Reconnected transitive components: pattern "
                "'Protoform<-Region<-Residue(ID '{}'), created Protoform<-Residue".format(
                    instance["residue"])
            )
            identifier.rewrite_graph(
                gene_region_residue_rule, instance,
                message=message, update_type="auto")

    gene_site_residue = regraph.NXGraph()
    gene_site_residue.add_nodes_from(["protoform", "site", "residue"])
    gene_site_residue.add_edges_from([("site", "protoform"), ("residue", "site")])
    gene_site_residue_rule = regraph.Rule.from_transform(gene_site_residue)
    gene_site_residue_rule.inject_add_edge(
        "residue", "protoform")
    lhs_typing = {
        "protoform": "protoform", "site": "site", "residue": "residue"
    }

    instances = identifier.find_matching_in_graph(
        gene_site_residue_rule.lhs, lhs_typing, new_nodes)
    for instance in instances:
        if not identifier.graph.exists_edge(
                instance["residue"], instance["protoform"]):

            edge_attrs = dict()
            edge_attrs.update(identifier.graph.get_edge(
                instance["residue"], instance["site"]))
            edge_attrs["type"] = "transitive"
            gene_site_residue_rule.rhs.set_edge("residue", "protoform", edge_attrs)

            message = (
                "Reconnected transitive components: pattern "
                "'Protoform<-Site<-Residue(ID '{}'), created Protoform<-Residue".format(
                    instance["residue"])
            )

            identifier.rewrite_graph(
                gene_site_residue_rule, instance,
                message=message, update_type="auto")


def connect_nested_fragments(identifier, genes):
    """Add edges between spacially nested framgents."""
    for protoform in genes:
        regions = identifier.get_attached_regions(protoform)
        for site in identifier.get_attached_sites(protoform):
            f = find_fragment(
                {}, identifier.graph.get_edge(site, protoform),
                {r: ({}, identifier.graph.get_edge(r, protoform)) for r in regions}
            )
            if f is not None:
                if identifier.meta_typing[f] == "region" and\
                   (site, f) not in identifier.graph.edges():
                    identifier.graph.add_edge(
                        site, f,
                        identifier.graph.get_edge(site, protoform))
                    identifier.graph.add_edge_attrs(
                        site, protoform, {"type": "transitive"})


def anatomize_gene(model, protoform):
    """Anatomize existing protoform node in the action graph."""
    new_regions = list()

    if protoform in model.action_graph.nodes() and\
       protoform in model.get_action_graph_typing() and\
       model.get_action_graph_typing()[protoform] == "protoform":
        anatomization_rule = None
        instance = None

        uniprot_ac = model.get_uniprot(protoform)

        meta_data = None
        domains = []

        try:
            meta_data = fetch_gene_meta_data(uniprot_ac)
            domains = fetch_gene_domains(uniprot_ac, merge_overlap=0.1)
        except:
            pass
        if meta_data or domains:
            # Generate an update rule to add
            # entities fetched by the anatomizer

            hgnc_symbol = None
            synonyms = None
            if meta_data:
                hgnc_symbol, synonyms = meta_data

            lhs = regraph.NXGraph()
            lhs.add_nodes_from(["protoform"])
            instance = {"protoform": protoform}

            anatomization_rule = regraph.Rule.from_transform(lhs)
            if hgnc_symbol:
                anatomization_rule.inject_add_node_attrs(
                    "protoform", {"hgnc_symbol": hgnc_symbol})
            if synonyms:
                anatomization_rule.inject_add_node_attrs(
                    "protoform", {"synonyms": synonyms})

            anatomization_rule_typing = {
                "meta_model": {}
            }

            # Build a rule that adds all regions and sites
            semantic_relations = dict()
            new_regions = []
            new_states = {}
            for i, domain in enumerate(domains):
                region_node_attrs = {}

                if domain["names"]:
                    region_node_attrs["name"] = [
                        n.replace(
                            "iSH2", "").replace(
                            "inter-SH2", "")
                        for n in domain["names"]
                    ]

                if domain["canonical_name"]:
                    region_node_attrs["label"] = domain["canonical_name"].replace(
                        "iSH2", "").replace(
                        "inter-SH2", "")

                region_node_attrs["interproid"] = domain["interproids"]

                region_edge_attrs = {
                    "start": domain["start"],
                    "end": domain["end"]
                }

                region_id = "region_{}".format(i + 1)
                if region_id in model.action_graph.nodes():
                    region_id = generate_new_id(
                        model.action_graph, region_id)
                anatomization_rule.inject_add_node(
                    region_id, region_node_attrs)
                new_regions.append(region_id)
                anatomization_rule.inject_add_edge(
                    region_id, "protoform", region_edge_attrs)

                anatomization_rule_typing["meta_model"][
                    region_id] = "region"
                # Resolve semantics
                semantic_relations[region_id] = set()
                if "IPR000719" in domain["interproids"] or\
                   "IPR001245" in domain["interproids"] or\
                   "IPR020635" in domain["interproids"]:
                    semantic_relations[region_id].add("protein_kinase")
                    # autocomplete with activity
                    activity_state_id = "{}_activity".format(region_id)
                    if activity_state_id in model.action_graph.nodes():
                        activity_state_id = generate_new_id(
                            model.action_graph, activity_state_id)
                    anatomization_rule.inject_add_node(
                        activity_state_id, {
                            "name": "activity", "test": {True}})
                    new_states[region_id] = activity_state_id
                    anatomization_rule.inject_add_edge(
                        activity_state_id, region_id)
                    semantic_relations[activity_state_id] = {
                        "protein_kinase_activity"
                    }
                    anatomization_rule_typing["meta_model"][
                        activity_state_id] = "state"
                if "IPR000980" in domain["interproids"]:
                    semantic_relations[region_id].add("sh2_domain")

            existing_regions = model.get_attached_regions(protoform)
            merged_activities = {}
            for existing_region in existing_regions:
                matching_region = find_fragment(
                    model.action_graph.get_node(existing_region),
                    model.action_graph.get_edge(existing_region, protoform),
                    {n: (
                        anatomization_rule.rhs.get_node(n),
                        anatomization_rule.rhs.get_edge(n, "protoform")
                    ) for n in new_regions})
                if matching_region is not None:
                    anatomization_rule._add_node_lhs(existing_region)
                    anatomization_rule._add_edge_lhs(existing_region, "protoform")
                    instance[existing_region] = existing_region

                    # Merge their activity state
                    state_nodes = model.get_attached_states(existing_region)
                    for s in state_nodes:
                        if matching_region in new_states:
                            s_attrs = model.action_graph.get_node(s)
                            if "activity" in s_attrs["name"]:
                                anatomization_rule._add_node_lhs(s)
                                anatomization_rule._add_edge_lhs(
                                    s, existing_region)
                                instance[s] = s
                                merged_state_rhs_id = anatomization_rule.rhs.merge_nodes(
                                    [s, new_states[matching_region]])
                                anatomization_rule.p_rhs[s] =\
                                    merged_state_rhs_id
                                del anatomization_rule_typing["meta_model"][
                                    new_states[matching_region]]
                                anatomization_rule_typing[
                                    "meta_model"][merged_state_rhs_id] = "state"
                                merged_activities[
                                    new_states[
                                        matching_region]] = merged_state_rhs_id

                    # Merge the new region with the existing
                    merged_rhs_id = anatomization_rule.rhs.merge_nodes(
                        [existing_region, matching_region])
                    anatomization_rule.p_rhs[existing_region] = merged_rhs_id
                    del anatomization_rule_typing["meta_model"][matching_region]
                    anatomization_rule_typing["meta_model"][merged_rhs_id] = "region"

                    s = semantic_relations[matching_region]
                    del semantic_relations[matching_region]
                    semantic_relations[merged_rhs_id] = s
                    new_regions.remove(matching_region)
                    new_regions.append(merged_rhs_id)

            message = (
                "Anatomizated the protoform with the UniProtAC '{}'".format(
                    uniprot_ac)
            )

            rhs_g = model.rewrite(
                model._action_graph_id, anatomization_rule,
                instance, rhs_typing=anatomization_rule_typing,
                message=message, update_type="auto")

            for node_id, semantics in semantic_relations.items():
                for s in semantics:
                    if node_id in rhs_g:
                        n = rhs_g[node_id]
                    else:
                        n = rhs_g[merged_activities[node_id]]
                    model._hierarchy.set_node_relation(
                        model._action_graph_id,
                        "semantic_action_graph", n, s)
        else:
            warnings.warn(
                "Unable to anatomize protoform node '{}'".format(protoform),
                KamiHierarchyWarning)
        return new_regions
    else:
        warnings.warn(
            "Protoform node '{}' does not exist in the model!".format(protoform),
            KamiHierarchyWarning)
        return []


def apply_bookkeeping(identifier, all_nodes, genes):
    # Apply bookkeeping updates
    connect_nested_fragments(identifier, genes)
    connect_transitive_components(identifier, all_nodes)
    for g in genes:
        residues = identifier.get_attached_residues(g)
        sites = identifier.get_attached_sites(g)
        regions = identifier.get_attached_regions(g)
        reconnect_residues(identifier, g, residues, regions, sites)
        reconnect_sites(identifier, g, sites, regions)
        merge_residues(identifier, g)
