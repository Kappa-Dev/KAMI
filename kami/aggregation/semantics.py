"""Collection of utils for semantic updates in KAMI models."""
import networkx as nx
import warnings

from kami.exceptions import KamiHierarchyWarning

from regraph.rules import Rule
from regraph.primitives import (add_nodes_from,
                                add_edges_from,
                                get_node)


def _propagate_semantics_to_ag(hierarchy, nugget_id,
                               semantic_nugget_id):
    """Propagate semantic rels from a nugget to the ag."""
    semantic_nugget_typing = hierarchy.get_typing(
        semantic_nugget_id, "semantic_action_graph")
    for nugget_node, semantics in hierarchy.get_relation(
            nugget_id, semantic_nugget_id).items():
        ag_node = hierarchy.get_typing(
            nugget_id, "action_graph")[nugget_node]
        for s in semantics:
            hierarchy.set_node_relation(
                "action_graph", "semantic_action_graph",
                ag_node, semantic_nugget_typing[s])


def apply_mod_semantics(model, nugget_id):
    """Apply mod semantics to the created nugget."""
    template_rel = model._hierarchy.get_relation(
        "mod_template", nugget_id)
    enzyme = None
    if "enzyme" in template_rel.keys():
        enzyme = list(template_rel["enzyme"])[0]
    mod_state = list(template_rel["mod_state"])[0]
    mod_residue = None

    if "substrate_residue" in template_rel.keys():
        mod_residue = list(template_rel["substrate_residue"])[0]

    mod_node = list(template_rel["mod"])[0]
    ag_enzyme = None
    ag_typing = model._hierarchy.get_typing(nugget_id, "action_graph")
    if enzyme is not None:
        ag_enzyme = ag_typing[enzyme]
    ag_mod_node = ag_typing[mod_node]

    ag_sag_rel = model._hierarchy.get_relation(
        "action_graph",
        "semantic_action_graph")

    phospho = False

    if enzyme is not None:
        if "phosphorylation" in get_node(model.nugget[
                nugget_id], mod_state)["name"]:
            if True in get_node(model.nugget[nugget_id],
               mod_node)["value"]:
                phospho = True
            # elif False in model.nugget[nugget_id].node[mod_node]["test"]:
            #     dephospho = True

    # 1. Phospho semantics
    if phospho:
        phospho_semantic_rel = {
            "mod": "phospho",
            mod_state: "phospho_state",
        }
        if mod_residue is not None:
            phospho_semantic_rel[mod_residue] = "phospho_target_residue"

        if "enzyme_region" in template_rel.keys():
            # Enzyme region is specified in the nugget
            enz_region = list(template_rel["enzyme_region"])[0]
            ag_enz_region = ag_typing[enz_region]
            if ag_enz_region in ag_sag_rel.keys() and\
                    "protein_kinase" in ag_sag_rel[ag_enz_region]:
                # This enzyme region is typed by the protein kinase
                # in the action graph
                phospho_semantic_rel[enz_region] = "protein_kinase"

                # 1. MOD action merge
                kinase_mods =\
                    model.ag_successors_of_type(
                        ag_enz_region, "mod")

                if len(kinase_mods) > 1:
                    pattern = nx.DiGraph()
                    add_nodes_from(
                        pattern, [ag_enz_region] + kinase_mods)

                    mod_merge_rule = Rule.from_transform(pattern)
                    new_mod_id = mod_merge_rule.inject_merge_nodes(
                        kinase_mods)

                    _, rhs_ag = model.rewrite(
                        "action_graph", mod_merge_rule,
                        instance={
                            n: n for n in mod_merge_rule.lhs.nodes()
                        })

                # 2. Autocompletion
                enz_region_predecessors = model.nugget[
                    nugget_id].predecessors(enz_region)

                # Check if kinase activity is specified in the nugget
                activity_found = False
                for pred in enz_region_predecessors:
                    ag_pred = ag_typing[pred]
                    ag_pred_type = ag_typing[ag_pred]
                    pred_attrs = get_node(model.nugget[nugget_id], pred)
                    if ag_pred_type == "state" and\
                       "activity" in pred_attrs["name"] and\
                       True in pred_attrs["test"]:
                        phospho_semantic_rel[pred] = "protein_kinase_activity"
                        activity_found = True
                        break
                if activity_found is False:
                    # If activity is not specified, we autocomplete
                    # nugget with it
                    autocompletion_rule = Rule.from_transform(
                        model.nugget[nugget_id])
                    new_activity_state = "{}_activity".format(enzyme)
                    autocompletion_rule.inject_add_node(
                        new_activity_state,
                        {"name": "activity", "test": True})
                    autocompletion_rule.inject_add_edge(
                        new_activity_state, enz_region)
                    # identify if there already exists the activity state
                    # in the action graph
                    rhs_typing = {"action_graph": {}}
                    ag_activity = model.get_activity_state(ag_enz_region)
                    if ag_activity is not None:
                        rhs_typing["action_graph"][new_activity_state] =\
                            ag_activity
                    # Apply autocompletion rule
                    _, rhs_g = model.rewrite(
                        nugget_id, autocompletion_rule,
                        rhs_typing=rhs_typing)
                    phospho_semantic_rel[rhs_g[new_activity_state]] =\
                        "protein_kinase_activity"

            else:
                # Phosphorylation is performed by the region not
                # identified as a protein kinase
                warnings.warn(
                    "Region '%s' performing phosphorylation is not "
                    "a protein kinase region" % ag_enz_region,
                    KamiHierarchyWarning)
        elif "enzyme_site" in template_rel:
            pass
        else:
            # Enzyme region is NOT specified in the nugget
            enz_region = None
            # Search for the unique kinase region associated
            # with respective gene in the action graph
            unique_kinase_region =\
                model.unique_kinase_region(ag_enzyme)

            if unique_kinase_region is not None:
                # 1. MOD action merge
                kinase_mods =\
                    model.ag_successors_of_type(
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

                _, rhs_ag = model.rewrite(
                    "action_graph", mod_merge_rule,
                    instance={
                        n: n for n in mod_merge_rule.lhs.nodes()
                    })

                # 2. Autocompletion
                if len(kinase_mods) > 0:
                    new_ag_mod = rhs_ag[new_mod_id]
                else:
                    new_ag_mod = ag_mod_node
                autocompletion_rule = Rule.from_transform(
                    model.nugget[nugget_id])
                autocompletion_rule.inject_add_node(
                    unique_kinase_region,
                    get_node(model.action_graph, unique_kinase_region))

                activity_state = "{}_activity".format(unique_kinase_region)

                autocompletion_rule.inject_add_node(
                    activity_state, {"name": "activity", "test": True})
                autocompletion_rule.inject_add_edge(
                    unique_kinase_region, enzyme)
                autocompletion_rule.inject_add_edge(
                    unique_kinase_region, mod_node)
                autocompletion_rule.inject_add_edge(
                    activity_state, unique_kinase_region)

                rhs_typing = {
                    "action_graph": {
                        unique_kinase_region: unique_kinase_region,
                        mod_node: new_ag_mod
                    }
                }
                ag_activity = model.get_activity_state(
                    unique_kinase_region)
                if ag_activity is not None:
                    rhs_typing["action_graph"][activity_state] = ag_activity

                _, rhs_nugget = model.rewrite(
                    nugget_id, autocompletion_rule,
                    instance={
                        n: n for n in autocompletion_rule.lhs.nodes()
                    },
                    rhs_typing=rhs_typing)

                enz_region = rhs_nugget[unique_kinase_region]
                phospho_semantic_rel[rhs_nugget[unique_kinase_region]] =\
                    "protein_kinase"
                for k, v in model._hierarchy.get_typing(
                        nugget_id, "action_graph").items():
                    if v == ag_activity:
                        nugget_activity = k
                phospho_semantic_rel[rhs_nugget[activity_state]] =\
                    "protein_kinase_activity"
                model._hierarchy.set_node_relation(
                    nugget_id, "mod_template", enz_region, "enz_region")
            else:
                # The repective gene in the action graph contains
                # either no or multiple kinase regions
                warnings.warn(
                    "Could not find the unique protein kinase "
                    "region associated with the gene '%s'" % ag_enzyme,
                    KamiHierarchyWarning)

        # Add a relation to the phosporylation semantic nugget
        model.add_semantic_nugget_rel(
            nugget_id,
            "phosphorylation",
            phospho_semantic_rel)
        # propagate this phospho semantics to the ag nodes
        _propagate_semantics_to_ag(
            model._hierarchy, nugget_id, "phosphorylation")


def apply_bnd_semantics(model, nugget_id):
    """Apply known binding semantics to the created nugget."""

    nugget = model.nugget[nugget_id]

    def _apply_sh2_py_semantics(region_node, region_bnd, partner_gene,
                                partner_region=None, partner_site=None):
        ag_typing = model._hierarchy.get_typing(
            nugget_id, "action_graph")

        ag_region = ag_typing[region_node]
        ag_sag_relation = model._hierarchy.get_relation(
            "action_graph",
            "semantic_action_graph")

        if ag_region in ag_sag_relation.keys() and\
           "sh2_domain" in ag_sag_relation[ag_region]:
            sh2_semantic_rel = {
                region_node: "sh2_domain",
                region_bnd: "sh2_domain_pY_bnd",
            }

            # Check if there are multiple bnd actions associated with the
            # same SH2 domain, merge them if it's the case
            ag_region_bnds = []
            for bnd in model.ag_successors_of_type(ag_region, "bnd"):
                ag_region_bnds.append(bnd)
            if len(ag_region_bnds) > 1:
                # generate a rule that merges bnds and loci
                pattern = nx.DiGraph()
                add_nodes_from(pattern, ag_region_bnds)
                bnd_merge_rule = Rule.from_transform(pattern)
                bnd_merge_rule.inject_merge_nodes(ag_region_bnds)
                _, rhs_ag = model.rewrite(
                    "action_graph", bnd_merge_rule)

            # Process/autocomplete sites and residues
            if partner_site:
                sh2_semantic_rel[partner_site] = "pY_site"
                # check if site has phosphorylated 'Y' residue
                py_residue_states = []
                for pred in nugget.predecessors(
                        partner_site):
                    ag_pred = ag_typing[pred]
                    if model.get_action_graph_typing()[ag_pred] == "residue" and\
                       "Y" in nugget.node[pred]["aa"]:
                        for residue_pred in nugget.predecessors(pred):
                            ag_residue_pred = ag_typing[residue_pred]
                            if model.get_action_graph_typing()[
                                    ag_residue_pred] == "state" and\
                               "phosphorylation" in get_node(
                                    nugget, residue_pred)["name"]:
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
                        "meta_model": {
                            "pY_residue": "residue",
                            "pY_residue_phospho": "state"
                        }
                    }
                    _, rhs_nugget = model.rewrite(
                        nugget_id, autocompletion_rule, instance={
                            n: n for n in autocompletion_rule.lhs.nodes()
                        },
                        rhs_typing=rhs_typing, strict=False)
                    # add necessary semantic rels
                    sh2_semantic_rel[rhs_nugget["pY_residue"]] = "pY_residue"
                    sh2_semantic_rel[rhs_nugget["pY_residue_phospho"]] =\
                        "phosphorylation"
                else:
                    # Update action graph by merging all the sites
                    # sharing the same residue
                    ag_gene = ag_typing[partner_gene]
                    sites = [
                        s for s in model.get_attached_sites(ag_gene)
                        if s != partner_site]

                    sites_to_merge = set()
                    for residue, state in py_residue_states:
                        sh2_semantic_rel[residue] = "pY_residue"
                        sh2_semantic_rel[state] = "phosphorylation"
                        ag_residue = ag_typing[residue]
                        for s in sites:
                            if ag_residue in model.get_attached_residues(s):
                                sites_to_merge.add(s)
                    if len(sites_to_merge) > 0:
                        sites_to_merge.add(partner_site)
                        pattern = nx.DiGraph()
                        add_nodes_from(pattern, sites_to_merge)
                        site_merging_rule = Rule.from_transform(pattern)
                        site_merging_rule.inject_merge_nodes(sites_to_merge)
                        model.rewrite("action_graph", site_merging_rule)

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
                    "meta_model": {
                        "pY_site": "site",
                        "pY_residue": "residue",
                        "pY_residue_phospho": "state"
                    }
                }

                _, rhs_nugget = model.rewrite(
                    nugget_id, autocompletion_rule,
                    rhs_typing=rhs_typing, strict=False)
                sh2_semantic_rel[rhs_nugget["pY_site"]] = "pY_site"
                sh2_semantic_rel[rhs_nugget["pY_residue"]] = "pY_residue"
                sh2_semantic_rel[rhs_nugget["pY_residue_phospho"]] =\
                    "phosphorylation"
            return sh2_semantic_rel
        return None

    template_rel = model._hierarchy.get_relation(
        "bnd_template", nugget_id)

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
            model.add_semantic_nugget_rel(
                nugget_id,
                "sh2_pY_binding",
                sh2_semantic_rel)
            _propagate_semantics_to_ag(
                model._hierarchy, nugget_id, "sh2_pY_binding")

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
            model.add_semantic_nugget_rel(
                nugget_id,
                "sh2_pY_binding",
                sh2_semantic_rel)
            _propagate_semantics_to_ag(
                model._hierarchy, nugget_id, "sh2_pY_binding")
