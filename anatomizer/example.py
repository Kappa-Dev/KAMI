"""Example of usage of a new version of gene anatomizer."""

import new_anatomizer as anatomizer

ptnlist = ['Q9UJX6', 'EGFR', 'wrongid', 'Q6PH85']

for ptn in ptnlist:
    # Create an object containing the "anatomy" of a chosen protein.
    anatomy = anatomizer.GeneAnatomy(
        ptn,
        merge_overlap=0.8,
        nest_overlap=0.8,
        nest_level=0,
        offline=True
    )
    
    # Print a text summary of the protein and its features.
    anatomy.anatomy_summary(fragments=True)

    # Write anatomy to JSON if protein was found.
    if anatomy.found:
        print("Saving json anatomy in 'anatomy_%s.json'..." % ptn)
        with open('anatomy_%s.json' % ptn, 'w') as f:
            f.write(anatomy.to_json())

