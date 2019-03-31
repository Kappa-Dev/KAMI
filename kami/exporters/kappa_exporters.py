# class Kappa4Exporter(object):
#   """Exporter to Kappa v4 script."""
#   def __init__(self):
#       pass


def generate_kappa(self, model, concentations=None):
    """Generate Kappa script from KAMI model."""
    if concentations is None:
        concentations = []

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
            isoforms[uniprot_id][0] = {
                protein: variant_name
            }
            isoforms[uniprot_id][1] = hgnc_symbol

    agents = {}
    for isoform, (proteins, hgnc) in isoforms.items():
        if hgnc is not None:
            agent_name = hgnc
        else:
            agent_name = isoform
        agents[agent_name] = {}
        variant_names = []
        for node, name in proteins.items():
            i = 1
            if name is not None:
                variant_names.append(name)
            else:
                variant_names.append("variant_" + i)
                i += 1
        agents[agent_name]["variants"] = variant_names
    print(agents)

    # Generate sites

    # Generate states

    # Generate rules
    return agents
