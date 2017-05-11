"""Collection of utils for id generation in kami."""


def _generate_new_id(graph, base_name):
    i = 1
    new_base_name = str(base_name) + "_" + str(i)
    while new_base_name in graph.nodes():
        i += 1
        new_base_name = str(base_name) + "_" + str(i)
    return new_base_name


def get_nugget_agent_id(nugget, agent):
    """Generate agent id for an input nugget."""
    agent_id = agent.uniprotid
    if agent_id in nugget.nodes():
        agent_id = _generate_new_id(nugget, agent_id)
    return agent_id


def get_nugget_region_id(nugget, region, father):
    """Generate region id for an input nugget."""
    region_id = str(father) + "_" + str(region)
    if region_id in nugget.nodes():
        region_id = _generate_new_id(nugget, region_id)
    return region_id


def get_nugget_residue_id(nugget, residue, father):
    """Generate residue id for an input nugget."""
    residue_id = str(father) + "_" + str(residue)
    if residue_id in nugget.nodes():
        residue_id = _generate_new_id(nugget, residue_id)
    return residue_id


def get_nugget_state_id(nugget, state, father):
    """Generate residue id for an input nugget."""
    state_id = str(father) + "_" + str(state)
    if state_id in nugget.nodes():
        state_id = _generate_new_id(nugget, state_id)
    return state_id


def get_nugget_locus_id(nugget, agent, binding_id):
    """Generate locus id."""
    locus_id = "%s_locus_%s" % (agent, binding_id)
    if locus_id in nugget.nodes():
        locus_id = _generate_new_id(nugget, locus_id)
    return locus_id


def get_nugget_is_bnd_id(nugget, agent_1, agent_2):
    """Generate is_bnd node id."""
    is_bnd_id = "%s_is_bnd_%s" % (agent_1, agent_2)
    if is_bnd_id in nugget.nodes():
        is_bnd_id = _generate_new_id(nugget, is_bnd_id)
    return is_bnd_id


def get_nugget_bnd_id(nugget, left, right):
    """Generate bnd node id."""
    bnd_id = "%s_bnd_%s" % (left, right)
    if bnd_id in nugget.nodes():
        bnd_id = _generate_new_id(nugget, bnd_id)
    return bnd_id


def get_nugget_is_free_id(nugget, agent_1, agent_2):
    """Generate is_free node id."""
    is_free_id = "%s_is_free_%s" % (agent_1, agent_2)
    if is_free_id in nugget.nodes():
        is_free_id = _generate_new_id(nugget, is_free_id)
    return is_free_id
