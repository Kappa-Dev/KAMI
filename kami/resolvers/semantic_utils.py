import networkx as nx
import warnings

from kami.exceptions import KamiHierarchyWarning

from regraph.rules import Rule
from regraph.primitives import (add_nodes_from,
                                add_edges_from)


def _propagate_semantics_to_ag(hierarchy, nugget_id,
                               semantic_nugget_id):
    """."""
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
    rules = []

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
        if "phosphorylation" in hierarchy.nugget[nugget_id].node[mod_state].keys():
            if True in hierarchy.nugget[nugget_id].node[
                    mod_node]["value"]:
                phospho = True
            elif False in hierarchy.nugget[nugget_id].node[mod_node]["value"]:
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
                       "activity" in hierarchy.nugget[nugget_id].node[pred].keys() and\
                       True in hierarchy.nugget[nugget_id].node[pred]["activity"]:
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
                    # rules.append({
                    #     "rule": autocompletion_rule.to_json(),
                    #     "instance": {n: n for n in autocompletion_rule.lhs.nodes()}
                    # })
                    phospho_semantic_rel[rhs_g[ag_activity]] = "protein_kinase_activity"
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
                    hierarchy.ag_successors_of_type(unique_kinase_region, "mod")
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
                rules.append({
                    "rule": mod_merge_rule.to_json(),
                    "instance": {n: n for n in mod_merge_rule.lhs.nodes()},
                    "origin": "mod_semantic_merge"
                })

                if len(kinase_mods) > 0:
                    new_ag_mod = rhs_ag[new_mod_id]
                else:
                    new_ag_mod = ag_mod_node
                autocompletion_rule = Rule.from_transform(
                    hierarchy.nugget[nugget_id])
                autocompletion_rule.inject_add_node(
                    unique_kinase_region,
                    hierarchy.action_graph.node[unique_kinase_region])
                ag_activity = hierarchy.get_activity_state(unique_kinase_region)
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
                # rules.append({
                #     "rule": autocompletion_rule.to_json(),
                #     "instance": {n: n for n in autocompletion_rule.lhs.nodes()}
                # })

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
    return rules

def apply_bnd_semantics(hierarchy, nugget_id):
    """Apply bnd semantics to the created nugget."""

    rules = []

    def _apply_sh2_py_semantics(region_node, region_locus,
                                region_bnd, opposite_locus,
                                partner_sites=None):
        ag_region_node =\
            hierarchy.typing[nugget_id]["action_graph"][region_node]
        if ag_region_node in hierarchy.relation["action_graph"][
            "semantic_action_graph"].keys() and\
            "sh2_domain" in hierarchy.relation["action_graph"][
                "semantic_action_graph"][ag_region_node]:
            sh2_semantic_rel = {
                region_node: "sh2_domain",
                region_locus: "sh2_domain_locus",
                region_bnd: "sh2_domain_pY_bnd",
                opposite_locus: "pY_locus"
            }
            ag_region_loci = hierarchy.ag_successors_of_type(
                ag_region_node, "locus")

            if len(ag_region_loci) > 1:
                opposite_loci = []
                bnds = []
                for locus in ag_region_loci:
                    bnd = hierarchy.ag_successors_of_type(
                        locus, "bnd")[0]
                    all_bnd_loci = hierarchy.ag_predecessors_of_type(
                        bnd, "locus")
                    opposite_loci += [l for l in all_bnd_loci if l != locus]
                    bnds.append(bnd)

                # generate a rule that merges bnds and loci
                pattern = nx.DiGraph()
                add_nodes_from(pattern, ag_region_loci)
                add_nodes_from(pattern, bnds)
                add_nodes_from(pattern, opposite_loci)
                bnd_merge_rule = Rule.from_transform(pattern)
                bnd_merge_rule.inject_merge_nodes(
                    ag_region_loci)
                bnd_merge_rule.inject_merge_nodes(bnds)
                bnd_merge_rule.inject_merge_nodes(
                    opposite_loci)
                _, rhs_ag = hierarchy.rewrite(
                    "action_graph", bnd_merge_rule)
                rules.append({
                    "rule": bnd_merge_rule.to_json(),
                    "instance": {n: n for n in bnd_merge_rule.lhs.nodes()},
                    "origin": "bnd_semantic_merge"
                })
                # Process sites
                if partner_sites:
                    for site in partner_sites:
                        sh2_semantic_rel[site] = "pY_site"
                        # add semantics of this site to the ag
                        ag_site = hierarchy.typing[nugget_id]["action_graph"][site]
                        ag_sag_rel =\
                            hierarchy.relation["action_graph"][
                                "semantic_action_graph"]
                        if ag_site in ag_sag_rel.keys():
                            ag_sag_rel[ag_site].add("pY_site")
                        else:
                            ag_sag_rel[ag_site] = {"pY_site"}

                # # generate nugget autocompletion rule (adding pY site)
                # else:
                #     pattern = hierarchy.nugget[nugget_id]
                #     autocompletion_rule = Rule.from_transform(pattern)
                #     if "right_partner_region" in template_rel.keys():
                #         pass
                #     autocompletion_rule
                #     autocompletion_rule.inject_add_node("pY_site")
                #     _, rhs_nugget = hierarchy.rewrite(
                #         nugget_id, autocompletion_rule)

            return sh2_semantic_rel
        return None

    template_rel = hierarchy.relation["bnd_template"][nugget_id]

    if "left_partner_region" in template_rel.keys():
        if len(template_rel["left_partner_region"]) == 1:
            region_node =\
                list(template_rel["left_partner_region"])[0]
            region_locus =\
                list(template_rel["left_partner_locus"])[0]
            region_bnd =\
                list(template_rel["bnd"])[0]
            opposite_locus =\
                list(template_rel["right_partner_locus"])[0]

            partner_sites = None
            if "right_partner_site" in template_rel.keys():
                partner_sites = template_rel["right_partner_site"]

            sh2_semantic_rel = _apply_sh2_py_semantics(
                region_node, region_locus, region_bnd, opposite_locus,
                partner_sites)

            if sh2_semantic_rel is not None:
                hierarchy.add_semantic_nugget_rel(
                    nugget_id,
                    "sh2_pY_binding",
                    sh2_semantic_rel)
                _propagate_semantics_to_ag(
                    hierarchy, nugget_id, "sh2_pY_binding")

    if "right_partner_region" in template_rel.keys():
        if len(template_rel["right_partner_region"]) == 1:
            region_node =\
                list(template_rel["right_partner_region"])[0]
            region_locus =\
                list(template_rel["right_partner_locus"])[0]
            region_bnd =\
                list(template_rel["bnd"])[0]
            opposite_locus =\
                list(template_rel["left_partner_locus"])[0]

            partner_sites = None
            if "left_partner_site" in template_rel.keys():
                partner_sites = template_rel["left_partner_site"]

            sh2_semantic_rel = _apply_sh2_py_semantics(
                region_node, region_locus, region_bnd, opposite_locus,
                partner_sites)

            if sh2_semantic_rel is not None:
                hierarchy.add_semantic_nugget_rel(
                    nugget_id,
                    "sh2_pY_binding",
                    sh2_semantic_rel)
                _propagate_semantics_to_ag(
                    hierarchy, nugget_id, "sh2_pY_binding")
    return rules
