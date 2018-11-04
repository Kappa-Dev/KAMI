"""Collection of bookkeeping updates."""
import networkx as nx
import warnings

from regraph import Rule
from regraph.primitives import (get_edge,
                                get_node,
                                add_edge,
                                add_nodes_from,
                                add_edges_from,
                                add_edge_attrs)

from anatomizer.new_anatomizer import GeneAnatomy
from kami import Region
from kami.aggregation.identifiers import find_fragment
from kami.exceptions import KamiHierarchyError, KamiHierarchyWarning
from kami.utils.id_generators import generate_new_id


def reconnect_residues(model, gene, residues,
                       regions=None, sites=None):
    """Reconnect residues of a gene to regions/sites of compatible range."""
    for res in residues:
        loc = None
        res_gene_edge = get_edge(model.action_graph, res, gene)
        if "loc" in res_gene_edge.keys():
            loc = list(res_gene_edge["loc"])[0]
        if loc is not None:
            region_dict = {}
            if regions is not None:
                for region in regions:
                    region_gene_edge = get_edge(model.action_graph, region, gene)
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
                    site_gene_edge = get_edge(model.action_graph, site, gene)
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
                   (res, region) not in model.action_graph.edges():
                    add_edge(model.action_graph, res, region,
                             {"loc": loc})
                    add_edge_attrs(
                        model.action_graph, res, gene,
                        {"type": "transitive"})

            for site, (start, end) in site_dict.items():
                if int(loc) >= start and\
                   int(loc) <= end and\
                   (res, site) not in model.action_graph.edges():
                    for suc in model.action_graph.successors(res):
                        if model.get_action_graph_typing()[suc] != "site":
                            if model._hierarchy.get_typing(
                                "action_graph", "meta_model")[suc] == "region" and\
                               suc in model.action_graph.successors(site):
                                add_edge_attrs(
                                    model.action_graph, res, suc,
                                    {"type": "transitive"})
                    add_edge_attrs(
                        model.action_graph, res, gene,
                        {"type": "transitive"})
                    add_edge(model.action_graph, res, site,
                             {"loc": loc})


def reconnect_sites(model, gene, sites, regions):
    """Reconnect sites of a gene to regions of compatible range."""
    for site in sites:
        start = None
        end = None
        site_gene_edge = get_edge(model.action_graph, site, gene)
        if "start" in site_gene_edge.keys():
            start = list(site_gene_edge["start"])[0]
        if "end" in site_gene_edge.keys():
            end = list(site_gene_edge["end"])[0]

        if start is not None and end is not None:
            for region in regions:
                region_gene_edge = get_edge(model.action_graph, region, gene)
                if "start" in region_gene_edge and\
                   "end" in region_gene_edge:
                    region_start = min(
                        region_gene_edge["start"])
                    region_end = max(
                        region_gene_edge["end"])
                    if int(start) >= region_start and\
                       int(end) <= region_end and\
                       (site, region) not in model.action_graph.edges():
                        add_edge(model.action_graph, site, region,
                                 {"start": start, "end": end})
                        add_edge_attrs(
                            model.action_graph, site, gene,
                            {"type": "transitive"})


def connect_transitive_components(model, new_nodes):
    """Add edges between components connected transitively."""
    gene_region_site = nx.DiGraph()
    add_nodes_from(gene_region_site, ["gene", "region", "site"])
    add_edges_from(
        gene_region_site, [("region", "gene"), ("site", "region")])
    gene_region_site_rule = Rule.from_transform(gene_region_site)
    gene_region_site_rule.inject_add_edge(
        "site", "gene", {"type": "transitive"})
    lhs_typing = {
        "meta_model": {"gene": "gene", "region": "region", "site": "site"}
    }
    instances = model._hierarchy.find_matching(
        "action_graph", gene_region_site_rule.lhs, pattern_typing=lhs_typing,
        nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = model.rewrite(
            "action_graph", gene_region_site_rule, instance)
        site_region_edge = get_edge(
            model.action_graph,
            instance["site"],
            instance["region"])
        if "start" in site_region_edge:
            start = site_region_edge["start"]
            add_edge_attrs(model.action_graph,
                           rhs_instance["site"],
                           rhs_instance["gene"],
                           {"start": start})
        if "end" in site_region_edge:
            end = site_region_edge["end"]
            add_edge_attrs(model.action_graph,
                           rhs_instance["site"],
                           rhs_instance["gene"],
                           {"end": end})
        if "order" in site_region_edge:
            order = site_region_edge["order"]
            add_edge_attrs(model.action_graph,
                           rhs_instance["site"],
                           rhs_instance["gene"],
                           {"order": order})

    region_site_residue = nx.DiGraph()
    add_nodes_from(region_site_residue, ["region", "site", "residue"])
    add_edges_from(
        region_site_residue, [("site", "region"), ("residue", "site")])
    region_site_residue_rule = Rule.from_transform(region_site_residue)
    region_site_residue_rule.inject_add_edge(
        "residue", "region", {"type": "transitive"})
    lhs_typing = {
        "meta_model": {"region": "region", "site": "site", "residue": "residue"}
    }
    instances = model._hierarchy.find_matching(
        "action_graph", region_site_residue_rule.lhs,
        pattern_typing=lhs_typing, nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = model.rewrite(
            "action_graph", region_site_residue_rule, instance)

        residue_site_edge = get_edge(
            model.action_graph,
            instance["residue"],
            instance["site"])
        if "loc" in residue_site_edge:
            loc = residue_site_edge["loc"]
            add_edge_attrs(model.action_graph,
                           rhs_instance["residue"],
                           rhs_instance["region"],
                           {"loc": loc})

    gene_region_residue = nx.DiGraph()
    add_nodes_from(gene_region_residue, ["gene", "region", "residue"])
    add_edges_from(
        gene_region_residue, [("region", "gene"), ("residue", "region")])
    gene_region_residue_rule = Rule.from_transform(gene_region_residue)
    gene_region_residue_rule.inject_add_edge(
        "residue", "gene", {"type": "transitive"})
    lhs_typing = {
        "meta_model": {"gene": "gene", "region": "region", "residue": "residue"}
    }
    instances = model._hierarchy.find_matching(
        "action_graph", gene_region_residue_rule.lhs,
        pattern_typing=lhs_typing, nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = model.rewrite(
            "action_graph", gene_region_residue_rule, instance)

        res_region_edge = get_edge(
            model.action_graph,
            instance["residue"], instance["region"])
        if "loc" in res_region_edge:
            loc = res_region_edge["loc"]
            add_edge_attrs(model.action_graph,
                           rhs_instance["residue"],
                           rhs_instance["gene"],
                           {"loc": loc})

    gene_site_residue = nx.DiGraph()
    add_nodes_from(gene_site_residue, ["gene", "site", "residue"])
    add_edges_from(
        gene_site_residue, [("site", "gene"), ("residue", "site")])
    gene_site_residue_rule = Rule.from_transform(gene_site_residue)
    gene_site_residue_rule.inject_add_edge(
        "residue", "gene", {"type": "transitive"})
    lhs_typing = {
        "meta_model": {"gene": "gene", "site": "site", "residue": "residue"}
    }
    instances = model._hierarchy.find_matching(
        "action_graph", gene_site_residue_rule.lhs, pattern_typing=lhs_typing,
        nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = model.rewrite(
            "action_graph", gene_site_residue_rule, instance)

        res_site_edge = get_edge(
            model.action_graph,
            instance["residue"], instance["site"])

        if "loc" in res_site_edge:
            loc = res_site_edge["loc"]
            add_edge_attrs(model.action_graph,
                           rhs_instance["residue"],
                           rhs_instance["gene"],
                           {"loc": loc})


def connect_nested_fragments(model, genes):
    """Add edges between spacially nested framgents."""
    for gene in genes:
        regions = model.get_attached_regions(gene)
        for site in model.get_attached_sites(gene):
            f = find_fragment(
                {}, get_edge(model.action_graph, site, gene),
                {r: ({}, get_edge(model.action_graph, r, gene)) for r in regions}
            )
            if f is not None:
                if model.get_action_graph_typing()[f] == "region" and\
                   (site, f) not in model.action_graph.edges():
                    add_edge(model.action_graph, site, f,
                             get_edge(model.action_graph, site, gene))
                    add_edge_attrs(
                        model.action_graph,
                        site, gene, {"type": "transitive"})


def anatomize_gene(model, gene):
    """Anatomize existing gene node in the action graph."""
    new_regions = list()
    if gene not in model.action_graph.nodes() or\
       model.get_action_graph_typing()[gene] != "gene":
        raise KamiHierarchyError(
            "Gene node '%s' does not exist in the model!" % gene)

    anatomy = None
    anatomization_rule = None
    instance = None

    gene_attrs = get_node(model.action_graph, gene)
    if "uniprotid" in gene_attrs and\
       len(gene_attrs["uniprotid"]) == 1:
        anatomy = GeneAnatomy(
            list(
                gene_attrs["uniprotid"])[0],
            merge_features=True,
            nest_features=False,
            merge_overlap=0.005,
            offline=True
        )
    elif "hgnc_symbol" in gene_attrs and\
         len(gene_attrs["hgnc_symbol"]) == 1:
        anatomy = GeneAnatomy(
            list(
                gene_attrs["hgnc_symbol"])[0],
            merge_features=True,
            nest_features=False,
            merge_overlap=0.05,
            offline=True
        )
    elif "synonyms" in gene_attrs and\
         len(gene_attrs["synonyms"]) > 0:
        for s in gene_attrs["synonyms"]:
            anatomy = GeneAnatomy(
                s,
                merge_features=True,
                nest_features=False,
                merge_overlap=0.05,
                offline=True
            )
            if anatomy is not None:
                break
    if anatomy is not None:

        # Generate an update rule to add
        # entities fetched by the anatomizer

        lhs = nx.DiGraph()
        add_nodes_from(lhs, ["gene"])
        instance = {"gene": gene}

        anatomization_rule = Rule.from_transform(lhs)
        anatomization_rule.inject_add_node_attrs(
            "gene", {"hgnc_symbol": anatomy.hgnc_symbol})
        anatomization_rule_typing = {
            "meta_model": {}
        }
        # Build a rule that adds all regions and sites
        semantic_relations = dict()
        new_regions = []
        for i, domain in enumerate(anatomy.domains):
            if domain.feature_type == "Domain":
                region = Region(
                    name=" ".join(
                        [n.replace(
                            "iSH2", "").replace(
                            "inter-SH2", "")
                         for n in domain.short_names]),
                    start=domain.start,
                    end=domain.end,
                    label=domain.prop_label,
                    interproid=domain.ipr_ids)

                region_id = "region_{}".format(i + 1)
                if region_id in model.action_graph.nodes():
                    region_id = generate_new_id(
                        model.action_graph, region_id)
                anatomization_rule.inject_add_node(
                    region_id, region.meta_data())
                new_regions.append(region_id)
                anatomization_rule.inject_add_edge(
                    region_id, "gene", region.location())

                anatomization_rule_typing["meta_model"][
                    region_id] = "region"
                # Resolve semantics
                semantic_relations[region_id] = set()
                if "IPR000719" in domain.ipr_ids or\
                   "IPR001245" in domain.ipr_ids or\
                   "IPR020635" in domain.ipr_ids:
                    semantic_relations[region_id].add("protein_kinase")
                    # autocomplete with activity
                    activity_state_id = "{}_activity".format(region_id)
                    if activity_state_id in model.action_graph.nodes():
                        activity_state_id = generate_new_id(
                            model.action_graph, activity_state_id)
                    anatomization_rule.inject_add_node(
                        activity_state_id, {
                            "name": "activity", "test": {True}})
                    anatomization_rule.inject_add_edge(
                        activity_state_id, region_id)
                    semantic_relations[activity_state_id] = {"activity"}
                    anatomization_rule_typing["meta_model"][
                        activity_state_id] = "state"
                if "IPR000980" in domain.ipr_ids:
                    semantic_relations[region_id].add("sh2_domain")

        existing_regions = model.get_attached_regions(gene)
        for existing_region in existing_regions:
            matching_region = find_fragment(
                get_node(model.action_graph, existing_region),
                get_edge(model.action_graph, existing_region, gene),
                {n: (
                    anatomization_rule.rhs.node[n],
                    anatomization_rule.rhs.edge[n]["gene"]
                ) for n in new_regions})
            if matching_region is not None:
                anatomization_rule._add_node_lhs(existing_region)
                anatomization_rule._add_edge_lhs(existing_region, "gene")
                instance[existing_region] = existing_region
                new_name = anatomization_rule.inject_merge_nodes(
                    [existing_region, matching_region])
                semantic_relations[new_name] = semantic_relations[
                    matching_region]
                del semantic_relations[matching_region]
                if matching_region in anatomization_rule_typing[
                        "meta_model"].keys():
                    del anatomization_rule_typing["meta_model"][
                        matching_region]

                new_regions.remove(matching_region)
                new_regions.append(new_name)

        _, rhs_g = model.rewrite(
            "action_graph", anatomization_rule,
            instance, rhs_typing=anatomization_rule_typing)

        for node_id, semantics in semantic_relations.items():
            for s in semantics:
                model._hierarchy.set_node_relation(
                    "action_graph",
                    "semantic_action_graph",
                    rhs_g[node_id], s)
    else:
        warnings.warn(
            "Unable to anatomize gene node '%s'" % gene,
            KamiHierarchyWarning)
    return new_regions
