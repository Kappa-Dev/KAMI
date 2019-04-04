import json
import copy


def parent_chain(parent, ipr_signatures_root):
    """
    Build the chain of parents (as a list) from given InterPro ID
    to top of hierarchy.
    """
    parchain = []
    while parent is not None:
        if parent != 'None':
            parchain.append(parent)
        # Find the entry of that parent
        ipr_entry = ipr_signatures_root.find("interpro[@id='%s']" % parent)
        # Redefine parent as the parent of the previous parent.
        try:
            parent = ipr_entry.get('parent')
        except:
            parent = None

    return parchain


def propose_name_label(ipr_list):
    """
    Propose a consensus name for a domain
    based on InterPro IDs and trees.
    """
    # 1 Get the deepest InterPro ID and all his parents (longest branch).
    branches = []
    branch_lens = []
    for ipr_id in ipr_list:
        branch = parent_chain(ipr_id)
        branches.append(branch)
        branch_lens.append(len(branch))
    longest_index = branch_lens.index(max(branch_lens))
    longest_branch = branches[longest_index]
    # Check that all ipr_ids are from a single branch.
    # This is supposed to be so because I group fragments only if
    # they are_parents().
    single_branch = True
    for branch in branches:
        for ipr_id in branch:
            if ipr_id not in longest_branch:
                single_branch = False # Will use the longest branch anyway.

    # 2 Custom name and label for some specific InterPro IDs.
    # Right now there are 2 paterns that can be used to set proposed
    # name and label (may have to make something more detailed in the future).
    custom_found = False
    # a) InterPro ID is found anywhere in longest_branch.
    # (basically this is used to ignore deeper levels)
    anywhere_dict = {
        'IPR020635': {'name': 'Tyrosine kinase', 'label': 'Tyr_kinase'}
    }
    for ipr_id in longest_branch:
        if ipr_id in anywhere_dict.keys():
            proposed_name = anywhere_dict[ipr_id]['name']
            proposed_label = anywhere_dict[ipr_id]['label']
            custom_found = True

    # b) InterPro ID is found as tip of longest_branch.
    tip_dict = {
        'IPR001245': {'name': 'Ser-thr/tyr kinase', 'label':'STY_kin'},
        'IPR000719': {'name': 'Protein kinase', 'label':'Prot_kin'}
    }
    tip_of_branch = longest_branch[0]
    if tip_of_branch in tip_dict.keys():
        proposed_name = tip_dict[tip_of_branch]['name']
        proposed_label = tip_dict[tip_of_branch]['label']
        custom_found = True

    # 3 Default behavior if no custom name was specified for given InterPro ID.
    if custom_found is False:
        # Take the root of the InterPro branch.
        interpro_id = longest_branch[-1]
        ipr_entry = ipr_signatures_root.find("interpro[@id='%s']" % interpro_id)
        ipr_short_name = ipr_entry.get('short_name')
        ipr_name = ipr_entry.get('name')
        # List of strings to remove from names.
        name_rm_strings = [" domain", "-domain"]
        tmp_name = ipr_name
        for name_rm_string in name_rm_strings:
            tmp_name = tmp_name.replace(name_rm_string, "")
        proposed_name = tmp_name
        # List of strings to remove from short names.
        short_rm_strings = ["_domain", "_cat_dom", "_dom", "-dom", "_like", "-like"]
        tmp_label = ipr_short_name
        for short_rm_string in short_rm_strings:
            tmp_label = tmp_label.replace(short_rm_string, "")
        proposed_label = tmp_label

    # Print a message if different InterPro branches were present.
    if single_branch is False:
        print('Domain "%s" made up of distinct InterPro branches, '
              'its naming might be inconsistent.' % proposed_name)

    return [proposed_name, proposed_label]


class DomainAnatomy:
    """Class implements anatomy of a domain."""

    def __init__(self, short_names, ipr_names, ipr_ids, start, end,
                 length, feature_type, subdomains=None, fragments=None):
        self.short_names = short_names
        self.ipr_names = ipr_names
        self.ipr_ids = ipr_ids
        self.start = start
        self.end = end
        self.length = length
        self.feature_type = feature_type

        self.prop_name, self.prop_label = propose_name_label(self.ipr_ids)

        if subdomains:
            self.subdomains = subdomains
        else:
            self.subdomains = list()
        if fragments:
            self.fragments = fragments
        else:
            self.fragments = list()

        return

    @classmethod
    def from_fragment(cls, fragment):
        domain = cls(
            fragment.start,
            fragment.end,
            subdomains=None,
            fragments=[copy.deepcopy(fragment)],
            names=[fragment.name],
            desc=fragment.description
        )
        return domain

    def is_protein_kinase(self):
        """Dummy is_kinase function.

        If name or description of domain mentions
        one of the key words, return True.
        """
        key_iprs = ["IPR000719"]
        stop_iprs = []
        for key_ipr in key_iprs:
            for ipr_id in self.ipr_ids:
                if ipr_id and key_ipr in ipr_id:
                    # check for stop InterPro IDs
                    for stop_ipr in stop_iprs:
                        if stop_ipr in ipr_id:
                            return False
                    # no stop IDs were found
                    return True
        return False

    def get_semantics(self):
        """ Domain semantics based on InterPro IDs. """
        semantics = []
        # Test if protein kinase region
        prot_kinase = False
        key_iprs = ["IPR000719"]
        stop_iprs = []
        for key_ipr in key_iprs:
            for ipr_id in self.ipr_ids:
                if ipr_id and key_ipr in ipr_id:
                    # check for stop InterPro IDs
                    for stop_ipr in stop_iprs:
                        if stop_ipr in ipr_id:
                            break
                    # no stop IDs were found
                    else:
                        prot_kinase = True
        if prot_kinase:
            semantics.append("kinase")
            semantics.append("protein kinase")

        # Test if serine-threonine/tyrosine protein kinase region
        sty_kinase = False
        key_iprs = ["IPR001245"]
        stop_iprs = []
        for key_ipr in key_iprs:
            for ipr_id in self.ipr_ids:
                if ipr_id and key_ipr in ipr_id:
                    # check for stop InterPro IDs
                    for stop_ipr in stop_iprs:
                        if stop_ipr in ipr_id:
                            break
                    # no stop IDs were found
                    else:
                        sty_kinase = True
        if sty_kinase:
            semantics.append("ser-thr/tyr kinase")

        # Test if tyrosine protein kinase region
        tyr_kinase = False
        key_iprs = ["IPR020635"]
        stop_iprs = []
        for key_ipr in key_iprs:
            for ipr_id in self.ipr_ids:
                if ipr_id and key_ipr in ipr_id:
                    # check for stop InterPro IDs
                    for stop_ipr in stop_iprs:
                        if stop_ipr in ipr_id:
                            break
                    # no stop IDs were found
                    else:
                        tyr_kinase = True
        if tyr_kinase:
            semantics.append("tyrosine kinase")

        # Test if SH2 region
        sh2 = False
        key_iprs = ["IPR000980"]
        stop_iprs = []
        for key_ipr in key_iprs:
            for ipr_id in self.ipr_ids:
                if ipr_id and key_ipr in ipr_id:
                    # check for stop InterPro IDs
                    for stop_ipr in stop_iprs:
                        if stop_ipr in ipr_id:
                            break
                    # no stop IDs were found
                    else:
                        sh2 = True
        if sh2:
            semantics.append("sh2")
        return semantics

    def to_dict(self):
        anatomy = dict()
        anatomy["short_names"] = self.short_names
        anatomy["ipr_names"] = self.ipr_names
        anatomy["ipr_ids"] = self.ipr_ids
        anatomy["start"] = self.start
        anatomy["end"] = self.end
        anatomy["length"] = self.length
        anatomy["feature_type"] = self.feature_type

        anatomy["subdomains"] = []
        for sd in self.subdomains:
            anatomy["subdomains"].append(sd.to_dict())

        anatomy["fragments"] = []
        for fr in self.fragments:
            anatomy["fragments"].append(fr.to_dict())

        return anatomy

    def to_json(self):
        anatomy = self.to_dict()
        return json.dumps(anatomy, indent=4)

    def print_summary(self, fragments=True, level=0):
        if self.feature_type == 'Domain' or self.feature_type == 'Repeat':
            prefix = ""
            for i in range(level):
                prefix += "\t"

            if len(self.short_names) == 0:
                shorts = "None"
            else:
                shorts = ", ".join(self.short_names)
            if len(self.ipr_names) == 0:
                names = "None"
            else:
                names = '"%s"' % '", "'.join(self.ipr_names)
            if len(self.ipr_ids) == 0:
                ids = "None"
            else:
                ids = ", ".join(self.ipr_ids)

            print(prefix, "         ---> %s <---" % self.feature_type)
            print(prefix, "  Proposed Label: %s" % self.prop_label)
            print(prefix, "   Proposed Name: %s" % self.prop_name)
            print(prefix, "     Short Names: %s" % shorts)
            print(prefix, "  InterPro Names: %s" % names)
            print(prefix, "    InterPro IDs: %s" % ids)
            print(prefix, "           Start: %s" % self.start)
            print(prefix, "             End: %s" % self.end)
            if fragments:
                if len(self.fragments) > 0:
                    print(prefix, "Source fragments: ")
                    for fragment in self.fragments:
                        fragment.print_summary(level + 3)
                        print()
            if len(self.subdomains) > 0:
                sorted_subdomains = sorted(
                    self.subdomains, key=lambda x: x.start)
                print(prefix, "      Subdomains:")
                for domain in sorted_subdomains:
                    domain.print_summary(fragments, level=level + 2)
            return


class Fragment:
    """Class implementing raw domain fragment."""

    def __init__(self, internal_id, xname, xid, xdatabase,
                 start, end, length, short_name, ipr_name,
                 ipr_id, feature_type, ipr_parents):
        """Initilize raw fragment."""
        self.internal_id = internal_id
        self.xname = xname
        self.xid = xid
        self.xdatabase = xdatabase
        self.start = start
        self.end = end
        self.length = length
        self.short_name = short_name
        self.ipr_name = ipr_name
        self.ipr_id = ipr_id
        self.feature_type = feature_type
        self.ipr_parents = ipr_parents
        return

    def to_dict(self):
        fragment_dict = {}
        fragment_dict["internal_id"] = self.internal_id
        fragment_dict["xname"] = self.xname
        fragment_dict["xid"] = self.xid
        fragment_dict["xdatabase"] = self.xdatabase
        fragment_dict["start"] = self.start
        fragment_dict["end"] = self.end
        fragment_dict["length"] = self.length
        fragment_dict["short_name"] = self.short_name
        fragment_dict["ipr_name"] = self.ipr_name
        fragment_dict["ipr_id"] = self.ipr_id
        fragment_dict["feature_type"] = self.feature_type
        fragment_dict["ipr_parents"] = self.ipr_parents

        return fragment_dict

    def print_summary(self, level=0):
        prefix = ""
        for i in range(level):
            prefix += "\t"

        if len(self.xname) > 45:
            fragname = self.xname[0:45] + "..."
        else:
            fragname = self.xname

        print(
            prefix,
            # "  Fragment %2i: %s" % (self.internal_id,fragname)
            "     Fragment: %s" % (fragname)
        )
        print(
            prefix,
            "    Start-End: %i-%i" % (self.start, self.end)
        )
        print(
            prefix,
            "   References: %s: %s" % (self.xdatabase, self.xid)
        )

        return
