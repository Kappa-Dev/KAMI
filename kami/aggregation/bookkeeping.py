"""."""
import networkx as nx
import warnings

from regraph import Rule
from regraph.primitives import (add_edge,
                                add_nodes_from,
                                add_edges_from,
                                add_edge_attrs)

from anatomizer.new_anatomizer import GeneAnatomy
from kami import Region
from kami.aggregation.identifiers import find_fragment
from kami.exceptions import KamiHierarchyError, KamiHierarchyWarning
from kami.utils.id_generators import generate_new_id


def reconnect_residues(hierarchy, gene, residues,
                       regions=None, sites=None):
    """Reconnect residues of a gene to regions/sites of compatible range."""
    for res in residues:
        loc = None
        if "loc" in hierarchy.action_graph.edge[res][gene].keys():
            loc = list(hierarchy.action_graph.edge[res][gene]["loc"])[0]
        if loc is not None:
            if regions is not None:
                for region in regions:
                    if "start" in hierarchy.action_graph.edge[region][gene] and\
                       "end" in hierarchy.action_graph.edge[region][gene]:
                        start = min(
                            hierarchy.action_graph.edge[region][gene]["start"])
                        end = max(
                            hierarchy.action_graph.edge[region][gene]["end"])
                        if int(loc) >= start and\
                           int(loc) <= end and\
                           (res, region) not in hierarchy.action_graph.edges():
                            add_edge(hierarchy.action_graph, res, region,
                                     {"loc": loc})
                            add_edge_attrs(
                                hierarchy.action_graph, res, gene,
                                {"type": "transitive"})

            if sites is not None:
                for site in sites:
                    if "start" in hierarchy.action_graph.edge[site][gene] and\
                       "end" in hierarchy.action_graph.edge[site][gene]:
                        start = min(
                            hierarchy.action_graph.edge[site][gene]["start"])
                        end = max(
                            hierarchy.action_graph.edge[site][gene]["end"])
                        if int(loc) >= start and\
                           int(loc) <= end and\
                           (res, site) not in hierarchy.action_graph.edges():
                            add_edge(hierarchy.action_graph, res, site,
                                     {"loc": loc})
                            add_edge_attrs(
                                hierarchy.action_graph, res, gene,
                                {"type": "transitive"})
        return


def reconnect_sites(hierarchy, gene, sites, regions):
    """Reconnect sites of a gene to regions of compatible range."""
    for site in sites:
        start = None
        end = None
        if "start" in hierarchy.action_graph.edge[site][gene].keys():
            start = list(hierarchy.action_graph.edge[site][gene]["start"])[0]
        if "end" in hierarchy.action_graph.edge[site][gene].keys():
            end = list(hierarchy.action_graph.edge[site][gene]["end"])[0]

        if start is not None and end is not None:
            for region in regions:
                if "start" in hierarchy.action_graph.edge[region][gene] and\
                   "end" in hierarchy.action_graph.edge[region][gene]:
                    region_start = min(
                        hierarchy.action_graph.edge[region][gene]["start"])
                    region_end = max(
                        hierarchy.action_graph.edge[region][gene]["end"])
                    if int(start) >= region_start and\
                       int(end) <= region_end and\
                       (site, region) not in hierarchy.action_graph.edges():
                        add_edge(hierarchy.action_graph, site, region,
                                 {"start": start, "end": end})
                        add_edge_attrs(
                            hierarchy.action_graph, site, gene,
                            {"type": "transitive"})


def connect_transitive_components(hierarchy, new_nodes):
    """Add edges between components connected transitively."""
    gene_region_site = nx.DiGraph()
    add_nodes_from(gene_region_site, ["gene", "region", "site"])
    add_edges_from(
        gene_region_site, [("region", "gene"), ("site", "region")])
    gene_region_site_rule = Rule.from_transform(gene_region_site)
    gene_region_site_rule.inject_add_edge(
        "site", "gene", {"type": "transitive"})
    lhs_typing = {
        "kami": {"gene": "gene", "region": "region", "site": "site"}
    }
    instances = hierarchy.find_matching(
        "action_graph", gene_region_site_rule.lhs, pattern_typing=lhs_typing,
        nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = hierarchy.rewrite(
            "action_graph", gene_region_site_rule, instance)
        if "start" in hierarchy.action_graph.edge[
                instance["site"]][instance["region"]]:
            start = hierarchy.action_graph.edge[
                instance["site"]][instance["region"]]["start"]
            add_edge_attrs(hierarchy.action_graph,
                           rhs_instance["site"],
                           rhs_instance["gene"],
                           {"start": start})
        if "end" in hierarchy.action_graph.edge[
                instance["site"]][instance["region"]]:
            end = hierarchy.action_graph.edge[
                instance["site"]][instance["region"]]["end"]
            add_edge_attrs(hierarchy.action_graph,
                           rhs_instance["site"],
                           rhs_instance["gene"],
                           {"end": end})
        if "order" in hierarchy.action_graph.edge[
                instance["site"]][instance["region"]]:
            order = hierarchy.action_graph.edge[
                instance["site"]][instance["region"]]["order"]
            add_edge_attrs(hierarchy.action_graph,
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
        "kami": {"region": "region", "site": "site", "residue": "residue"}
    }
    instances = hierarchy.find_matching(
        "action_graph", region_site_residue_rule.lhs,
        pattern_typing=lhs_typing, nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = hierarchy.rewrite(
            "action_graph", region_site_residue_rule, instance)
        if "loc" in hierarchy.action_graph.edge[
                instance["residue"]][instance["site"]]:
            loc = hierarchy.action_graph.edge[
                instance["residue"]][instance["site"]]["loc"]
            add_edge_attrs(hierarchy.action_graph,
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
        "kami": {"gene": "gene", "region": "region", "residue": "residue"}
    }
    instances = hierarchy.find_matching(
        "action_graph", gene_region_residue_rule.lhs,
        pattern_typing=lhs_typing, nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = hierarchy.rewrite(
            "action_graph", gene_region_residue_rule, instance)
        if "loc" in hierarchy.action_graph.edge[
                instance["residue"]][instance["region"]]:
            loc = hierarchy.action_graph.edge[
                instance["residue"]][instance["region"]]["loc"]
            add_edge_attrs(hierarchy.action_graph,
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
        "kami": {"gene": "gene", "site": "site", "residue": "residue"}
    }
    instances = hierarchy.find_matching(
        "action_graph", gene_site_residue_rule.lhs, pattern_typing=lhs_typing,
        nodes=new_nodes)
    for instance in instances:
        _, rhs_instance = hierarchy.rewrite(
            "action_graph", gene_site_residue_rule, instance)
        if "loc" in hierarchy.action_graph.edge[
                instance["residue"]][instance["site"]]:
            loc = hierarchy.action_graph.edge[
                instance["residue"]][instance["site"]]["loc"]
            add_edge_attrs(hierarchy.action_graph,
                           rhs_instance["residue"],
                           rhs_instance["gene"],
                           {"loc": loc})
    return


def connect_nested_fragments(hierarchy, genes):
    """Add edges between spacially nested framgents."""
    for gene in genes:
        regions = hierarchy.get_attached_regions(gene)
        for site in hierarchy.get_attached_sites(gene):
            f = find_fragment(
                {}, hierarchy.action_graph.edge[site][gene],
                {r: ({}, hierarchy.action_graph.edge[r][gene]) for r in regions}
            )
            if f is not None:
                if hierarchy.action_graph_typing[f] == "region" and\
                   (site, f) not in hierarchy.action_graph.edges():
                    add_edge(hierarchy.action_graph, site, f,
                             hierarchy.action_graph.edge[site][gene])
                    add_edge_attrs(
                        hierarchy.action_graph,
                        site, gene, {"type": "transitive"})


def anatomize_gene(hierarchy, gene):
    """Anatomize existing gene node in the action graph."""
    new_regions = list()
    if gene not in hierarchy.action_graph.nodes() or\
       hierarchy.action_graph_typing[gene] != "gene":
        raise KamiHierarchyError(
            "Gene node '%s' does not exist in the hierarchy!" % gene)

    anatomy = None
    anatomization_rule = None
    instance = None

    if "uniprotid" in hierarchy.action_graph.node[gene] and\
       len(hierarchy.action_graph.node[gene]["uniprotid"]) == 1:
        anatomy = GeneAnatomy(
            list(
                hierarchy.action_graph.node[gene]["uniprotid"])[0],
            merge_features=True,
            nest_features=False,
            merge_overlap=0.005,
            offline=True
        )
    elif "hgnc_symbol" in hierarchy.action_graph.node[gene] and\
         len(hierarchy.action_graph.node[gene]["hgnc_symbol"]) == 1:
        anatomy = GeneAnatomy(
            list(
                hierarchy.action_graph.node[gene]["hgnc_symbol"])[0],
            merge_features=True,
            nest_features=False,
            merge_overlap=0.05,
            offline=True
        )
    elif "synonyms" in hierarchy.action_graph.node[gene] and\
         len(hierarchy.action_graph.node[gene]["synonyms"]) > 0:
        for s in hierarchy.action_graph.node[gene]["synonyms"]:
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
            "kami": {}
        }
        # Build a rule that adds all regions and sites
        semantic_relations = dict()
        new_regions = []
        for domain in anatomy.domains:
            if domain.feature_type == "Domain":
                region = Region(
                    name=" ".join(
                        [n.replace("iSH2", "").replace("inter-SH2", "")
                         for n in domain.short_names]),
                    start=domain.start,
                    end=domain.end,
                    label=domain.prop_label,
                    interproid=domain.ipr_ids)

                region_id = "%s_%s" % (gene, str(region))
                if region_id in hierarchy.action_graph.nodes():
                    region_id = generate_new_id(
                        hierarchy.action_graph, region_id)
                anatomization_rule.inject_add_node(
                    region_id, region.meta_data())
                new_regions.append(region_id)
                anatomization_rule.inject_add_edge(
                    region_id, "gene", region.location())

                anatomization_rule_typing["kami"][region_id] = "region"
                # Resolve semantics
                semantic_relations[region_id] = set()
                if "IPR000719" in domain.ipr_ids:
                    semantic_relations[region_id].add("protein_kinase")
                    # autocomplete with activity
                    activity_state_id = "{}_activity".format(region_id)
                    if activity_state_id in hierarchy.action_graph.nodes():
                        activity_state_id = generate_new_id(
                            hierarchy.action_graph, activity_state_id)
                    anatomization_rule.inject_add_node(
                        activity_state_id, {
                            "name": "activity", "test": {True}})
                    anatomization_rule.inject_add_edge(
                        activity_state_id, region_id)
                    semantic_relations[activity_state_id] = {"activity"}
                    anatomization_rule_typing["kami"][
                        activity_state_id] = "state"
                if "IPR000980" in domain.ipr_ids:
                    semantic_relations[region_id].add("sh2_domain")

        existing_regions = hierarchy.get_attached_regions(gene)
        for existing_region in existing_regions:
            matching_region = find_fragment(
                hierarchy.action_graph.node[existing_region],
                hierarchy.action_graph.edge[existing_region][gene],
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
                new_regions.remove(matching_region)
                new_regions.append(new_name)

        _, rhs_g = hierarchy.rewrite(
            "action_graph", anatomization_rule,
            instance, rhs_typing=anatomization_rule_typing,
            strict=True, inplace=True)

        for new_node_id, semantics in semantic_relations.items():
            for s in semantics:
                if rhs_g[new_node_id] in hierarchy.relation["action_graph"][
                        "semantic_action_graph"].keys():
                    hierarchy.relation["action_graph"][
                        "semantic_action_graph"][rhs_g[new_node_id]].add(s)
                else:
                    hierarchy.relation["action_graph"][
                        "semantic_action_graph"][rhs_g[new_node_id]] = {s}
    else:
        warnings.warn(
            "Unable to anatomize gene node '%s'" % gene,
            KamiHierarchyWarning)
    return new_regions
