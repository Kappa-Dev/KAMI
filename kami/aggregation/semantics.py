"""Collection of utils for semantic updates in KAMI models."""
import networkx as nx
import warnings

from kami.exceptions import KamiHierarchyWarning

from regraph.rules import Rule
from regraph.primitives import (add_nodes_from,
                                add_edges_from)


def _propagate_semantics_to_ag(hierarchy, nugget_id,
                               semantic_nugget_id):
    """Propagate semantic rels from a nugget to the ag."""
    ag_sag_rel = hierarchy.relation["action_graph"][
        "semantic_action_graph"]
    for nugget_node, semantics in hierarchy.relation[nugget_id][
            semantic_nugget_id].items():
        ag_node = hierarchy.typing[nugget_id]["action_graph"][nugget_node]
        if ag_node not in ag_sag_rel.keys():
            ag_sag_rel[ag_node] = set()
        for s in semantics:
            ag_sag_rel[ag_node].add(
                hierarchy.typing[semantic_nugget_id][
                    "semantic_action_graph"][s])


def apply_mod_semantics(hierarchy, nugget_id):
    """Apply mod semantics to the created nugget."""
    # TODO: Check the phosphorylated residue

    template_rel = hierarchy.relation["mod_template"][nugget_id]
    enzyme = None
    if "enzyme" in template_rel.keys():
        enzyme = list(template_rel["enzyme"])[0]
    mod_state = list(template_rel["mod_state"])[0]
    mod_residue = None

    if "substrate_residue" in template_rel.keys():
        mod_residue = list(template_rel["substrate_residue"])[0]

    mod_node = list(template_rel["mod"])[0]
    ag_enzyme = None
    if enzyme is not None:
        ag_enzyme = hierarchy.typing[nugget_id]["action_graph"][enzyme]
    ag_mod_node = hierarchy.typing[nugget_id]["action_graph"]["mod"]

    dephospho = False
    phospho = False

    if enzyme is not None:
        if "phosphorylation" in hierarchy.nugget[
                nugget_id].node[mod_state].keys():
            if True in hierarchy.nugget[nugget_id].node[
                    mod_node]["test"]:
                phospho = True
            elif False in hierarchy.nugget[nugget_id].node[mod_node]["test"]:
                dephospho = True

    # 1. Phospho semantics
    if phospho:
        phospho_semantic_rel = {
            "mod": "phospho",
            mod_state: "target_state",
        }
        if mod_residue is not None:
            phospho_semantic_rel[mod_residue] = "target_residue"

        if "enzyme_region" in template_rel.keys():
            enz_region = list(template_rel["enzyme_region"])[0]
            ag_enz_region = hierarchy.typing[nugget_id][
                "action_graph"][enz_region]
            if ag_enz_region in hierarchy.relation["action_graph"][
               "semantic_action_graph"].keys() and\
                    "protein_kinase" in hierarchy.relation["action_graph"][
                    "semantic_action_graph"][ag_enz_region]:
                phospho_semantic_rel[enz_region] = "protein_kinase"
                enz_region_predecessors = hierarchy.nugget[
                    nugget_id].predecessors(enz_region)
                activity_found = False
                for pred in enz_region_predecessors:
                    ag_pred = hierarchy.typing[nugget_id]["action_graph"][pred]
                    ag_pred_type = hierarchy.action_graph_typing[ag_pred]
                    if ag_pred_type == "state" and\
                       "activity" in hierarchy.nugget[
                            nugget_id].node[pred].keys() and\
                       True in hierarchy.nugget[nugget_id].node[
                            pred]["activity"]:
                        phospho_semantic_rel[pred] = "protein_kinase_activity"
                        activity_found = True
                        break
                if activity_found is False:
                    ag_activity = hierarchy.get_activity_state(ag_enz_region)

                    autocompletion_rule = Rule.from_transform(
                        hierarchy.nugget[nugget_id])
                    autocompletion_rule.inject_add_node(
                        ag_activity,
                        hierarchy.action_graph.node[ag_activity])
                    rhs_typing = {
                        "action_graph": {
                            ag_activity: ag_activity
                        }
                    }
                    _, rhs_g = hierarchy.rewrite(
                        nugget_id, autocompletion_rule,
                        rhs_typing=rhs_typing)
                    phospho_semantic_rel[rhs_g[ag_activity]] =\
                        "protein_kinase_activity"
            else:
                warnings.warn(
                    "Region '%s' performing phosphorylation is not "
                    "a protein kinase region" % ag_enz_region,
                    KamiHierarchyWarning)
        elif "enzyme_site" in template_rel:
            pass
        else:
            enz_region = None
            unique_kinase_region =\
                hierarchy.unique_kinase_region(ag_enzyme)
            if unique_kinase_region is not None:

                kinase_mods =\
                    hierarchy.ag_successors_of_type(
                        unique_kinase_region, "mod")
                pattern = nx.DiGraph()
                add_nodes_from(
                    pattern,
                    [ag_mod_node, ag_enzyme])
                add_edges_from(pattern, [(ag_enzyme, ag_mod_node)])
                mod_merge_rule = Rule.from_transform(pattern)
                mod_merge_rule.inject_remove_edge(ag_enzyme, ag_mod_node)

                if len(kinase_mods) > 0:
                    # generate a rule that merges mods
                    for n in kinase_mods:
                        mod_merge_rule._add_node_lhs(n)
                    new_mod_id = mod_merge_rule.inject_merge_nodes(
                        [ag_mod_node] + kinase_mods)

                _, rhs_ag = hierarchy.rewrite("action_graph", mod_merge_rule)

                if len(kinase_mods) > 0:
                    new_ag_mod = rhs_ag[new_mod_id]
                else:
                    new_ag_mod = ag_mod_node
                autocompletion_rule = Rule.from_transform(
                    hierarchy.nugget[nugget_id])
                autocompletion_rule.inject_add_node(
                    unique_kinase_region,
                    hierarchy.action_graph.node[unique_kinase_region])
                ag_activity = hierarchy.get_activity_state(
                    unique_kinase_region)
                autocompletion_rule.inject_add_node(
                    ag_activity, hierarchy.action_graph.node[ag_activity])
                autocompletion_rule.inject_add_edge(
                    unique_kinase_region, enzyme)
                autocompletion_rule.inject_add_edge(
                    unique_kinase_region, mod_node)
                autocompletion_rule.inject_add_edge(
                    ag_activity, unique_kinase_region)
                rhs_typing = {
                    "action_graph": {
                        unique_kinase_region: unique_kinase_region,
                        mod_node: new_ag_mod,
                        ag_activity: ag_activity
                    }
                }

                _, rhs_nugget = hierarchy.rewrite(
                    nugget_id, autocompletion_rule,
                    rhs_typing=rhs_typing)

                enz_region = rhs_nugget[unique_kinase_region]
                phospho_semantic_rel[rhs_nugget[unique_kinase_region]] =\
                    "protein_kinase"
                phospho_semantic_rel[rhs_nugget[ag_activity]] =\
                    "protein_kinase_activity"
                hierarchy.relation[nugget_id]["mod_template"][enz_region] =\
                    {"enzyme_region"}
            else:
                warnings.warn(
                    "Could not find the unique protein kinase "
                    "region associated with the gene '%s'" % ag_enzyme,
                    KamiHierarchyWarning)

        hierarchy.add_semantic_nugget_rel(
            nugget_id,
            "phosphorylation",
            phospho_semantic_rel)
        # propagate this phospho semantics to the ag nodes
        _propagate_semantics_to_ag(hierarchy, nugget_id, "phosphorylation")


def apply_bnd_semantics(hierarchy, nugget_id):
    """Apply known binding semantics to the created nugget."""
    nugget = hierarchy.nugget[nugget_id]

    def _apply_sh2_py_semantics(region_node, region_bnd, partner_gene,
                                partner_region=None, partner_site=None):
        ag_region =\
            hierarchy.typing[nugget_id]["action_graph"][region_node]
        if ag_region in hierarchy.relation["action_graph"][
            "semantic_action_graph"].keys() and\
            "sh2_domain" in hierarchy.relation["action_graph"][
                "semantic_action_graph"][ag_region]:
            sh2_semantic_rel = {
                region_node: "sh2_domain",
                region_bnd: "sh2_domain_pY_bnd",
            }
            # Check if there are multiple bnd actions associated with the
            # same SH2 domain, merge them if it's the case
            ag_region_bnds = []
            for bnd in hierarchy.ag_successors_of_type(ag_region, "bnd"):
                ag_region_bnds.append(bnd)
            if len(ag_region_bnds) > 1:
                # generate a rule that merges bnds and loci
                pattern = nx.DiGraph()
                add_nodes_from(pattern, ag_region_bnds)
                bnd_merge_rule = Rule.from_transform(pattern)
                bnd_merge_rule.inject_merge_nodes(ag_region_bnds)
                _, rhs_ag = hierarchy.rewrite(
                    "action_graph", bnd_merge_rule)

            # Process/autocomplete sites and residues
            if partner_site:
                sh2_semantic_rel[partner_site] = "pY_site"
                # check if site has phosphorylated 'Y' residue
                py_residue_states = []
                for pred in nugget.predecessors(
                        partner_site):
                    ag_pred = hierarchy.typing[nugget_id][
                        "action_graph"][pred]
                    if hierarchy.action_graph_typing[ag_pred] == "residue" and\
                       "Y" in nugget.node[pred]["aa"]:
                        for residue_pred in nugget.predecessors(pred):
                            ag_residue_pred = hierarchy.typing[nugget_id][
                                "action_graph"][residue_pred]
                            if hierarchy.action_graph_typing[
                                    ag_residue_pred] == "state" and\
                               "phosphorylation" in nugget.node[
                                    residue_pred]["name"]:
                                py_residue_states.append((pred, residue_pred))

                # if pY residue was not found it, autocomplete nugget with it
                if len(py_residue_states) == 0:
                    pattern = nx.DiGraph()
                    add_nodes_from(pattern, [partner_site])
                    autocompletion_rule = Rule.from_transform(pattern)
                    autocompletion_rule.inject_add_node(
                        "pY_residue", {"aa": "Y"})
                    autocompletion_rule.inject_add_node(
                        "pY_residue_phospho",
                        {"name": "phosphorylation", "test": True})
                    autocompletion_rule.inject_add_edge(
                        "pY_residue_phospho", "pY_residue")
                    autocompletion_rule.inject_add_edge(
                        "pY_residue", partner_site)
                    rhs_typing = {
                        "kami": {
                            "pY_residue": "residue",
                            "pY_residue_phospho": "state"
                        }
                    }
                    _, rhs_nugget = hierarchy.rewrite(
                        nugget_id, autocompletion_rule,
                        rhs_typing=rhs_typing, strict=False)
                    # add necessary semantic rels
                    sh2_semantic_rel[rhs_nugget["pY_residue"]] = "pY_residue"
                    sh2_semantic_rel[rhs_nugget["pY_residue_phospho"]] =\
                        "phosphorylation"
                else:
                    # Update action graph by merging all the sites
                    # sharing the same residue
                    ag_gene = hierarchy.typing[nugget_id][
                        "action_graph"][partner_gene]
                    sites = [
                        s for s in hierarchy.get_attached_sites(ag_gene)
                        if s != partner_site]

                    sites_to_merge = set()
                    for residue, state in py_residue_states:
                        sh2_semantic_rel[residue] = "pY_residue"
                        sh2_semantic_rel[state] = "phosphorylation"
                        ag_residue = hierarchy.typing[
                            nugget_id]["action_graph"][residue]
                        for s in sites:
                            if ag_residue in hierarchy.get_attached_residues(s):
                                sites_to_merge.add(s)
                    if len(sites_to_merge) > 0:
                        sites_to_merge.add(partner_site)
                        pattern = nx.DiGraph()
                        add_nodes_from(pattern, sites_to_merge)
                        site_merging_rule = Rule.from_transform(pattern)
                        site_merging_rule.inject_merge_nodes(sites_to_merge)
                        hierarchy.rewrite("action_graph", site_merging_rule)

            else:
                if partner_region is not None:
                    attached_to = partner_region
                else:
                    attached_to = partner_gene
                pattern = nx.DiGraph()
                add_nodes_from(pattern, [region_bnd, attached_to])
                add_edges_from(pattern, [(attached_to, region_bnd)])
                autocompletion_rule = Rule.from_transform(pattern)
                autocompletion_rule.inject_remove_edge(
                    attached_to, region_bnd)
                autocompletion_rule.inject_add_node("pY_site")
                autocompletion_rule.inject_add_node(
                    "pY_residue", {"aa": "Y"})
                autocompletion_rule.inject_add_node(
                    "pY_residue_phospho",
                    {"name": "phosphorylation", "test": True})
                autocompletion_rule.inject_add_edge(
                    "pY_residue_phospho", "pY_residue")
                autocompletion_rule.inject_add_edge(
                    "pY_residue", "pY_site")
                autocompletion_rule.inject_add_edge(
                    "pY_site", attached_to)
                autocompletion_rule.inject_add_edge(
                    "pY_site", region_bnd)
                rhs_typing = {
                    "kami": {
                        "pY_site": "site",
                        "pY_residue": "residue",
                        "pY_residue_phospho": "state"
                    }
                }

                _, rhs_nugget = hierarchy.rewrite(
                    nugget_id, autocompletion_rule,
                    rhs_typing=rhs_typing, strict=False)
                sh2_semantic_rel[rhs_nugget["pY_site"]] = "pY_site"
                sh2_semantic_rel[rhs_nugget["pY_residue"]] = "pY_residue"
                sh2_semantic_rel[rhs_nugget["pY_residue_phospho"]] =\
                    "phosphorylation"
            return sh2_semantic_rel
        return None

    template_rel = hierarchy.relation["bnd_template"][nugget_id]

    if "left_partner_region" in template_rel.keys():
        region_node =\
            list(template_rel["left_partner_region"])[0]
        region_bnd =\
            list(template_rel["bnd"])[0]

        partner_site = None
        if "right_partner_site" in template_rel.keys():
            partner_site = list(template_rel["right_partner_site"])[0]
        partner_region = None
        if "right_partner_region" in template_rel.keys():
            partner_region = list(template_rel["right_partner_region"])[0]
        partner_gene = list(template_rel["right_partner"])[0]

        sh2_semantic_rel = _apply_sh2_py_semantics(
            region_node, region_bnd, partner_gene, partner_region,
            partner_site)
        if sh2_semantic_rel is not None:
            hierarchy.add_semantic_nugget_rel(
                nugget_id,
                "sh2_pY_binding",
                sh2_semantic_rel)
            _propagate_semantics_to_ag(
                hierarchy, nugget_id, "sh2_pY_binding")

    if "right_partner_region" in template_rel.keys():
        region_node =\
            list(template_rel["right_partner_region"])[0]
        region_bnd =\
            list(template_rel["bnd"])[0]

        partner_site = None
        if "left_partner_site" in template_rel.keys():
            partner_site = list(template_rel["left_partner_site"])[0]
        partner_region = None
        if "left_partner_region" in template_rel.keys():
            partner_region = list(template_rel["left_partner_region"])[0]
        partner_gene = list(template_rel["left_partner"])[0]

        sh2_semantic_rel = _apply_sh2_py_semantics(
            region_node, region_bnd, partner_gene, partner_region,
            partner_site)
        if sh2_semantic_rel is not None:
            hierarchy.add_semantic_nugget_rel(
                nugget_id,
                "sh2_pY_binding",
                sh2_semantic_rel)
            _propagate_semantics_to_ag(
                hierarchy, nugget_id, "sh2_pY_binding")
