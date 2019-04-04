"""Collection of utils for anatomizer."""


def find_shortname(ipr_id, filepath):
    """Retreive short names."""
    result = None
    with open(filepath, "r+") as f:
        for line in f.readlines():
            print(line.split("\t"))
            row = line.split("\t")
            if row[0] == ipr_id:
                result = row[1]
                break
    return result


def _merge_overlap(f1, f2):
    """Calculate overlap ratio.

    Simple overlap ratio: number of overlapping residues /
                          total span of the two features

                -----------               -----------
    overlap     |||||||||        span  ||||||||||||||
             ------------              ------------
    """
    starts = [f1["start"], f2["start"]]
    ends = [f1["end"], f2["end"]]
    ratio = 0
    # First, check if there is an overlap at all.
    highstart = max(starts)
    lowend = min(ends)
    if highstart < lowend:
        # Compute number of overlapping residues
        overlap = lowend - highstart
        # Compute the total span
        lowstart = min(starts)
        highend = max(ends)
        span = highend - lowstart
        # Compute ratio
        ratio = float(overlap) / float(span)
    return ratio


def _nest_overlap(f1, f2):
    """Calculate overlap ratio for nesting.

    Nest overlap ratio: number of overlapping residues /
                          span of the smallest feature

                   --------                  --------
    overlap        ||||||        span        ||||||||
             ------------              ------------
    """
    ratio = 0
    # f1 is expected to be the largest feature
    if f1["length"] > f2["length"]:
        starts = [f1["start"], f2["start"]]
        ends = [f1["end"], f2["end"]]
        # First, check if there is an overlap at all.
        highstart = max(starts)
        lowend = min(ends)
        if highstart < lowend:
            # Compute number of overlapping residues.
            overlap = lowend - highstart
            # Find smallest feature span.
            span = f2["length"]
            # Compute ratio.
            ratio = float(overlap) / float(span)
    return ratio


def are_parents(frag1, frag2):
    """Return True if InterPro IDs of given fragments are identical or parents.

    Returns False otherwise.
    """
    ipr1 = frag1["ipr_id"]
    ipr2 = frag2["ipr_id"]
    answer = False

    if ("ipr_parents" in frag1 and "ipr_parents" in frag2):
        par1 = frag1["ipr_parents"]
        par2 = frag2["ipr_parents"]

        if ipr1 == ipr2:
            answer = True
        if ipr1 in par2:
            answer = True
        if ipr2 in par1:
            answer = True

    return answer


def _merge_fragments(fragments, overlap_threshold=0.7, shortest=False):
        nfeatures = len(fragments)
        ipr_overlap_threshold = 0.0001

        visited = set()
        groups = []

        for i in range(nfeatures):
            feature1 = fragments[i]
            if i not in visited:
                group = [feature1]
                visited.add(i)
                # for j in range(i + 1, nfeatures):
                j = 0
                while j < nfeatures:
                    if j not in visited:
                        feature2 = fragments[j]
                        for member in group:
                            overlap = _merge_overlap(member, feature2)
                            condition = are_parents(member, feature2)
                            if condition is True and overlap >= ipr_overlap_threshold:
                                group.append(feature2)
                                visited.add(j)
                                j = -1  # Restart from the beginning of fragments
                                break
                    j += 1
                groups.append(group)
        domains = []
        # create domains from groups
        for group in groups:
            # 1. find shortest non-empty description for a group
            domain_desc = None
            descs = dict([
                (
                    len(member["short_name"]),
                    member["short_name"]
                ) for member in group if member["short_name"]
            ])
            if len(descs) > 0:
                min_desc = min(descs.keys())
                domain_desc = descs[min_desc]

            # 2. find start/end depending on the value of parameter `shortest`
            lengths = dict([
                (member["length"], i) for i, member in enumerate(group)
            ])
            # 2.a. create domain from the shortest fragment
            if shortest:
                min_length = min(lengths.keys())
                domain_start = group[lengths[min_length]]["start"]
                domain_end = group[lengths[min_length]]["end"]
            # 2.b. create domain from the longest fragment
            else:
                # max_length = max(lengths.keys())
                # domain_start = group[lengths[max_length]]["start"]
                # domain_end = group[lengths[max_length]]["end"]
                # Take lowest start and highest end value.
                starts = [member["start"] for i, member in enumerate(group)]
                ends = [member["end"] for i, member in enumerate(group)]
                domain_start = min(starts)
                domain_end = max(ends)
            domain_length = domain_end - domain_start

            # 3. find domain names from concatenation of all fragment names
            short_name_list = [
                member["short_name"] for member in group if member["short_name"]]
            ipr_name_list = [
                member["ipr_name"] for member in group if member["ipr_name"]]
            ipr_id_list = [member["ipr_id"] for member in group if member["ipr_id"]]
            short_names = sorted(set(short_name_list),
                                 key=lambda x: short_name_list.index(x))
            ipr_names = sorted(set(ipr_name_list),
                               key=lambda x: ipr_name_list.index(x))
            ipr_ids = sorted(set(ipr_id_list),
                             key=lambda x: ipr_id_list.index(x))

            # 5. get feature type
            feature_type = group[0]["feature_type"]

            # 4. create domain dict
            domain = {
                "short_names": short_names,
                "ipr_names": ipr_names,
                "ipr_ids": ipr_ids,
                "start": domain_start,
                "end": domain_end,
                "length": domain_length,
                "feature_type": feature_type,
                "subdomains": [],
                "fragments": group
            }

            domains.append(domain)
        return domains


def _nest_domains(domains, nest_threshold=0.7, max_level=1):

    def _find_nests(elements, domains):
        visited = set()
        result_nest = dict()
        for i in elements:
            if i not in visited:
                result_nest[i] = dict()
                visited.add(i)
                for j in elements:
                    if j not in visited:
                        overlap = _nest_overlap(
                            domains[i],
                            domains[j]
                        )
                        if overlap >= nest_threshold:
                            result_nest[i][j] = dict()
                            visited.add(j)
        return result_nest

    # Recursive auxiliary function to nest domains
    def _nest(domains, current_level):
        if current_level == max_level:
            return domains
        else:
            # sort_domains by size
            sorted_domains = sorted(
                domains, key=lambda x: x["length"], reverse=True
            )

            nestsing_indices = _find_nests(
                list(range(len(sorted_domains))), sorted_domains
            )
            result_domains = []
            for domain_index, indices in nestsing_indices.items():
                next_level_domains = [sorted_domains[i] for i in indices]
                nested_domains = _nest(
                    next_level_domains, current_level + 1
                )
                for domain in nested_domains:
                    sorted_domains[domain_index]["subdomains"].append(
                        domain
                    )
                result_domains.append(sorted_domains[domain_index])
            return result_domains

    # 1. nest domains
    result_domains = _nest(domains, 0)

    return result_domains
