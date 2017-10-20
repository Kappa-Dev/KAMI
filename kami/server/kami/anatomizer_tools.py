import anatomizer.new_anatomizer as anatomizer
import regraph.tree as tree

def anatomizer_add_agent(hie, g_id, parent_id, uniprot_id):
    anatomy = anatomizer.GeneAnatomy(
        uniprot_id,
        merge_overlap=0.8,
        nest_overlap=0.8,
        nest_level=0,
        offline=True
    )
    if anatomy.found:
        agent_id = tree.add_node(hie, g_id, parent_id, uniprot_id ,"agent", new_name=True)
        for region in anatomy.domains :
            region_id = region.short_names[0]
            region_type = region.feature_type
            if region_type == 'Domain' or region_type == 'Repeat':
                new_region_id = tree.add_node(hie, g_id, parent_id, region_id ,"region", new_name=True)
                tree.add_edge(hie, g_id, parent_id, new_region_id, agent_id)
    else:
        raise ValueError("Entry %s not found" % uniprot_id)

