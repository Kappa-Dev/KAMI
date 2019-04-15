import datetime
from kami.aggregation.identifiers import EntityIdentifier
from kami.utils.id_generators import generate_new_element_id

from regraph import get_node

# class Kappa4Exporter(object):
#   """Exporter to Kappa v4 script."""
#   def __init__(self):
#       pass


def _generate_agent_name(identifier, ag_typing, agent, ag_uniprot_id, agents):
    # Find agent name
    agent_name = agents[ag_uniprot_id]["agent_name"]

    # Find agent variant
    agent_variant_state = ""
    if len(agents[ag_uniprot_id]["variants"]) > 1:
        agent_variant_state = "variant{{{}}}".format(
            agents[ag_uniprot_id]["variants"][ag_typing[agent]])
    return agent_name, agent_variant_state


def _generate_agent_states(identifier, ag_typing, agent, ag_uniprot_id, agents,
                           to_ignore=None):
    if to_ignore is None:
        to_ignore = []
    # Find agent states
    state_repr = []
    states = identifier.get_attached_states(agent)
    for s in states:
        if s not in to_ignore:
            # get state value (True always renders to 1, False to 0)
            state_attrs = get_node(identifier.graph, s)
            value = 1 if list(state_attrs["test"])[0] else 0
            ag_state = ag_typing[s]
            state_repr.append(
                agents[ag_uniprot_id]["stateful_sites"][ag_state] + "{{{}}}".format(
                    value))
    # agent_states = ",".join(state_repr)
    return state_repr


def _generate_bnd_sites(identifier, ag_typing, template_rel, role,
                        agent, bnd, ag_uniprot_id, agents):
    """Find agent bnd sites."""
    ag_bnd = ag_typing[bnd]
    agent_bnd_sites = []
    if role + "_partner_site" in template_rel and\
       len(template_rel[role + "_partner_site"]) > 0:
        sites = identifier.get_attached_sites(agent)
        for s in sites:
            if s in template_rel[role + "_partner_site"]:
                ag_site = ag_typing[s]
                agent_bnd_sites.append(agents[ag_uniprot_id]["kami_sites"][ag_site])
    elif role + "_partner_region" in template_rel and\
            len(template_rel[role + "_partner_region"]) != 0:
        regions = identifier.get_attached_regions(agent)
        for r in regions:
            if r in template_rel[role + "_partner_region"]:
                ag_region = ag_typing[r]
                agent_bnd_sites.append(agents[ag_uniprot_id][
                    "region_bnd_sites"][(ag_region, ag_bnd)])
    else:
        agent_bnd_sites.append(agents[ag_uniprot_id][
            "direct_bnd_sites"][ag_bnd])
    return agent_bnd_sites


def _generate_bnd_partner(identifier, ag_typing, template_rel, role,
                          agent, bnd, ag_uniprot_id, agents, bnd_flag=True):

    agent_name, agent_variant_state = _generate_agent_name(
        identifier, ag_typing, agent, ag_uniprot_id, agents)
    state_repr = _generate_agent_states(
        identifier, ag_typing, agent, ag_uniprot_id, agents)
    agent_states = ""
    if len(state_repr) > 0:
        agent_states = ",".join(state_repr)

    # Find agent agent bnd sites
    agent_bnd_sites = _generate_bnd_sites(
        identifier, ag_typing, template_rel, role,
        agent, bnd, ag_uniprot_id, agents)

    immutable_part = agent_name + "("
    if len(agent_variant_state) > 0:
        immutable_part += agent_variant_state + ","
    if len(agent_states) > 0:
        immutable_part += agent_states + ","

    lhs = immutable_part + ",".join(
        "{}[.]".format(s)
        if bnd_flag is True
        else "{}[{}]".format(s, i + 1)
        for i, s in enumerate(agent_bnd_sites)) + ")"
    rhs = immutable_part + ",".join(
        "{}[{}]".format(s, i + 1)
        if bnd_flag is True
        else "{}[.]".format(s)
        for i, s in enumerate(agent_bnd_sites)) + ")"
    return lhs, rhs


def generate_kappa(model, concentations=None):
    """Generate Kappa script from KAMI model."""
    if concentations is None:
        concentations = []

    default_bnd_rate = None
    if model.default_bnd_rate is not None:
        default_bnd_rate = model.default_bnd_rate

    default_brk_rate = None
    if model.default_brk_rate is not None:
        default_brk_rate = model.default_brk_rate

    default_mod_rate = None
    if model.default_mod_rate is not None:
        default_mod_rate = model.default_mod_rate

    # Generate agents: an agent per protoform (gene)
    # each having a state specifying its variantsss
    isoforms = {}
    for protein in model.proteins():
        uniprot_id = model.get_uniprot(protein)
        variant_name = model.get_variant_name(protein)
        hgnc_symbol = model.get_hgnc_symbol(protein)
        if uniprot_id in isoforms.keys():
            isoforms[uniprot_id][0][protein] = variant_name
            if hgnc_symbol is not None:
                isoforms[uniprot_id][1] = hgnc_symbol
        else:
            isoforms[uniprot_id] = [
                {protein: variant_name},
                hgnc_symbol
            ]

    identifier = EntityIdentifier(
        model.action_graph,
        model.get_action_graph_typing(),
        immediate=False)
    agents = {}
    for isoform, (proteins, hgnc) in isoforms.items():

        if hgnc is not None:
            agent_name = hgnc
        else:
            agent_name = isoform
        agents[isoform] = {}
        variants = {}
        for node, name in proteins.items():
            i = 1
            if name is not None:
                variants[node] = name.replace(" ", "_").replace(
                    ",", "_").replace("/", "_")
            else:
                variants[node] = "variant_{}".format(i)
                i += 1
        agents[isoform]["agent_name"] = agent_name
        agents[isoform]["variants"] = variants

        # Generate state contaning sites and binding sites from KAMI sites
        agents[isoform]["stateful_sites"] = {}
        agents[isoform]["kami_sites"] = {}
        agents[isoform]["direct_bnd_sites"] = {}
        agents[isoform]["region_bnd_sites"] = {}
        for protein, variant_name in variants.items():
            prefix = ""
            if len(variants) > 1:
                prefix = variant_name + "_"
            states = identifier.get_attached_states(protein)
            for s in states:
                state_name = list(get_node(identifier.graph, s)["name"])[0]
                site_name = generate_new_element_id(
                    agents[isoform]["stateful_sites"].values(),
                    prefix + "{}".format(state_name))
                agents[isoform]["stateful_sites"][s] = site_name

            sites = identifier.get_attached_sites(protein)
            for s in sites:
                site_attrs = get_node(identifier.graph, s)
                if "name" in site_attrs.keys():
                    site_name = prefix + "site_" + list(
                        get_node(identifier.graph, s)["name"])[0].replace(
                        " ", "_").replace(",", "_").replace("/", "_")
                else:
                    site_name = generate_new_element_id(
                        agents[isoform]["kami_sites"].values(),
                        prefix + "site")
                agents[isoform]["kami_sites"][s] = site_name

            # Generate bnd sites for bnd actions
            direct_bnds = identifier.successors_of_type(protein, "bnd")
            for bnd in direct_bnds:
                bnd_name = generate_new_element_id(
                    agents[isoform]["direct_bnd_sites"].values(),
                    prefix + "site")
                agents[isoform]["direct_bnd_sites"][bnd] = bnd_name

            regions = identifier.get_attached_regions(protein)
            for r in regions:
                region_attrs = get_node(identifier.graph, r)
                if "name" in region_attrs.keys():
                    region_name = prefix + list(
                        get_node(identifier.graph, r)["name"])[0].replace(
                        " ", "_").replace(",", "_").replace("/", "_")
                else:
                    region_name = generate_new_element_id(
                        agents[isoform]["region_bnd_sites"].values(),
                        prefix + "_region")
                for bnd in identifier.successors_of_type(r, "bnd"):
                    bnd_name = generate_new_element_id(
                        agents[isoform]["region_bnd_sites"].values(),
                        region_name + "_site")
                    agents[isoform]["region_bnd_sites"][(r, bnd)] = bnd_name

    rules = []

    # Generate rules
    for n in model.nuggets():
        nugget = model.nugget[n]
        # nugget_type = model.get_nugget_type(n)
        ag_typing = model.get_nugget_typing(n)
        relations = model._hierarchy.adjacent_relations(n)

        nugget_identifier = EntityIdentifier(
            nugget,
            {
                k: model.get_action_graph_typing()[v]
                for k, v in ag_typing.items()},
            immediate=False)

        nugget_desc = ""
        if (model.get_nugget_desc(n)):
            nugget_desc = " //{}".format(model.get_nugget_desc(n).replace(
                "\n", ", "))

        rule = ""
        if "mod_template" in relations:
            template_rel = model._hierarchy.get_relation("mod_template", n)
            mod_node = list(template_rel["mod"])[0]
            if "substrate" in template_rel.keys():
                substrates = template_rel["substrate"]

                enzymes = []
                if "enzyme" in template_rel.keys():
                    enzymes = template_rel["enzyme"]
                for substrate in substrates:
                    ag_substrate = ag_typing[substrate]
                    ag_substrate_uniprot_id = model.get_uniprot(ag_substrate)

                    substrate_name, substrate_variant_state = _generate_agent_name(
                        identifier, ag_typing, substrate, ag_substrate_uniprot_id, agents)

                    states = nugget_identifier.get_attached_states(
                        substrate)
                    target_states = []
                    for s in states:
                        if s in template_rel["mod_state"]:
                            # Get site of a state
                            ag_state = ag_typing[s]
                            target_site = agents[
                                ag_substrate_uniprot_id]["stateful_sites"][
                                    ag_state]
                            # Get state value
                            mod_attrs = get_node(nugget, mod_node)
                            target_value = 1 if list(mod_attrs["value"])[0] else 0

                            target_states.append((s, target_site, target_value))

                    state_repr = _generate_agent_states(
                        identifier, ag_typing, substrate, ag_substrate_uniprot_id, agents,
                        [s[0] for s in target_states])
                    substrate_states = ",".join(state_repr)

                    if len(enzymes) > 0:
                        for enzyme in enzymes:
                            ag_enzyme = ag_typing[enzyme]
                            ag_enzyme_uniprot_id = model.get_uniprot(ag_enzyme)
                            enzyme_name, enzyme_variant_state = _generate_agent_name(
                                identifier, ag_typing, enzyme, ag_enzyme_uniprot_id, agents)
                            enzyme_states = ",".join(_generate_agent_states(
                                identifier, ag_typing, enzyme, ag_enzyme_uniprot_id, agents))

                            enzyme_bnd_sites = []
                            substrate_bnd_sites = []
                            if "bnd_template" in relations:
                                # Add binding
                                bnd_rel = model._hierarchy.get_relation(
                                    "bnd_template", n)

                                bnd = list(bnd_rel["bnd"])[0]
                                substrate_bnd_sites = _generate_bnd_sites(
                                    identifier, ag_typing, bnd_rel, "left",
                                    substrate, bnd, ag_substrate_uniprot_id, agents)
                                enzyme_bnd_sites = _generate_bnd_sites(
                                    identifier, ag_typing, bnd_rel, "right",
                                    enzyme, bnd, ag_enzyme_uniprot_id, agents)

                            substrate_lhs = substrate_name + "("
                            substrate_rhs = substrate_name + "("
                            if len(substrate_variant_state) > 0:
                                substrate_lhs += substrate_variant_state + ","
                                substrate_rhs += substrate_variant_state + ","
                            if len(substrate_states) > 0:
                                substrate_lhs += substrate_states + ","
                                substrate_rhs += substrate_states + ","
                            if len(substrate_bnd_sites) > 0:
                                substrate_lhs += ",".join(
                                    "{}[{}]".format(s, i + 1)
                                    for i, s in enumerate(substrate_bnd_sites)) + ","
                                substrate_rhs += ",".join(
                                    "{}[{}]".format(s, i + 1)
                                    for i, s in enumerate(substrate_bnd_sites)) + ","

                            substrate_lhs += ",".join([s[1] for s in target_states]) + ")"
                            substrate_rhs += ",".join(
                                "{}{{{}}}".format(s[1], s[2])
                                for s in target_states) + ")"

                            enzyme_lhs = enzyme_name + "("
                            if len(enzyme_variant_state) > 0:
                                enzyme_lhs += enzyme_variant_state + ","
                            if len(enzyme_states) > 0:
                                enzyme_lhs += enzyme_states
                            if len(enzyme_bnd_sites) > 0:
                                enzyme_lhs += ",".join(
                                    "{}[{}]".format(s, i + 1)
                                    for i, s in enumerate(enzyme_bnd_sites))
                            enzyme_lhs += ")"

                            rule = "{}, {} -> {}, {}".format(
                                enzyme_lhs, substrate_lhs, enzyme_lhs,
                                substrate_rhs)

                    else:
                        substrate_lhs = substrate_name + "("
                        substrate_rhs = substrate_name + "("
                        if len(substrate_variant_state) > 0:
                            substrate_lhs += substrate_variant_state + ","
                            substrate_rhs += substrate_variant_state + ","
                        if len(substrate_states) > 0:
                            substrate_lhs += substrate_states + ","
                            substrate_rhs += substrate_states + ","
                        substrate_lhs += ",".join([s[1] for s in target_states]) + ")"
                        substrate_rhs += ",".join(
                            "{}{{{}}}".format(s[1], s[2])
                            for s in target_states) + ")"
                        rule = "{} -> {}".format(
                            substrate_lhs, substrate_rhs)

                    rate = ""
                    mod_attrs = get_node(nugget, mod_node)
                    if "rate" in mod_attrs:
                        rate = " @ {}".format(list(mod_attrs["rate"])[0])
                    else:
                        if default_mod_rate is not None:
                            rate = " @ 'default_mod_rate'"

                    rules.append("{} {} {}".format(rule, rate, nugget_desc))

        elif "bnd_template" in relations:
            template_rel = model._hierarchy.get_relation("bnd_template", n)
            bnd_node = list(template_rel["bnd"])[0]
            bnd_attrs = get_node(nugget, bnd_node)
            bnd_flag = True
            if "test" in bnd_attrs:
                bnd_flag = list(bnd_attrs["test"])[0]

            if "left_partner" in template_rel.keys() and\
               "right_partner" in template_rel.keys():
                left_partner = template_rel["left_partner"]
                right_partner = template_rel["right_partner"]
                for left in left_partner:
                    ag_left = ag_typing[left]
                    ag_left_uniprot_id = model.get_uniprot(ag_left)

                    left_lhs, left_rhs = _generate_bnd_partner(
                        nugget_identifier, ag_typing, template_rel, "left",
                        left, bnd_node, ag_left_uniprot_id, agents, bnd_flag)

                    for right in right_partner:
                        ag_right = ag_typing[right]
                        ag_right_uniprot_id = model.get_uniprot(ag_right)

                        right_lhs, right_rhs = _generate_bnd_partner(
                            nugget_identifier, ag_typing, template_rel, "right",
                            right, bnd_node, ag_right_uniprot_id, agents, bnd_flag)

                        rate = ""
                        if "rate" in bnd_attrs:
                            rate = " @ {}".format(list(bnd_attrs["rate"])[0])
                        else:
                            if bnd_flag is True and default_bnd_rate is not None:
                                rate = " @ 'default_bnd_rate'"
                            elif bnd_flag is False and default_brk_rate is not None:
                                rate = " @ 'default_brk_rate'"
                        rules.append("{}, {} -> {}, {}{}{}".format(
                            left_lhs, right_lhs, left_rhs, right_rhs, rate, nugget_desc))

        nugget_desc = model.get_nugget_desc(n)
        if (nugget_desc):
            rate += " //{}".format(nugget_desc)

    header = "// Automatically generated from KAMI-model '{}' {}\n\n".format(
        model._id, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

    signatures = "// Signatures\n\n"
    for agent_uniprot, agent_data in agents.items():
        agent_signature = []
        if len(agent_data["variants"]) > 1:
            agent_signature.append("variant{{{}}}".format(
                " ".join(v for v in agent_data["variants"].values())))

        if len(agent_data["stateful_sites"]) > 0:
            agent_signature.append(",".join([
                "{}{{0 1}}".format(v)
                for v in agent_data["stateful_sites"].values()]))

        all_sites = list(agent_data["kami_sites"].values()) +\
            list(agent_data["direct_bnd_sites"].values()) +\
            list(agent_data["region_bnd_sites"].values())
        if len(all_sites) > 0:
            agent_signature.append(",".join(["{}".format(v) for v in all_sites]))

        signatures += "%agent: {}({})".format(
            agent_data["agent_name"],
            ",".join(agent_signature)) + "\n"

    rule_repr = "\n// Rules \n\n"

    for i, r in enumerate(rules):
        rule_repr += "'rule {}' {}\n\n".format(
            i + 1, r)

    variables = ""
    if (default_bnd_rate or default_brk_rate or default_mod_rate):
        variables = "\n// variables \n\n"

    if default_bnd_rate:
        variables += "%var: 'default_bnd_rate' {}\n".format(default_bnd_rate)
    if default_brk_rate:
        variables += "%var: 'default_brk_rate' {}\n".format(default_brk_rate)
    if default_mod_rate:
        variables += "%var: 'default_mod_rate' {}\n".format(default_mod_rate)

    return header + signatures + rule_repr + variables
