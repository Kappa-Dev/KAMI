"""Example of usage of a new version of gene anatomizer."""

from new_anatomizer import GeneAnatomy


if __name__ == '__main__':
    anatomy = GeneAnatomy(
        "EGFR",
        merge_overlap=0.8,
        nest_overlap=0.8,
        nest_level=3
    )
    anatomy.anatomy_summary(fragments=False)
    print("Saving json anatomy in 'anatomy_output.json'...")
    with open('anatomy_output.json', 'w') as f:
        f.write(anatomy.to_json())
