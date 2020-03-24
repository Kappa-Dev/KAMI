"""Collection of utils for fetching data online on the fly."""
import os
import json
import requests
import ssl
from urllib import request
from urllib.error import HTTPError
from time import sleep

from anatomizer.utils import _merge_fragments, _nest_domains


INTERPRO_BASE_URL = "https://www.ebi.ac.uk:443/interpro/api/entry/InterPro/protein/UniProt/{}/?page_size=100"
RESOURCES = os.path.join(os.path.dirname(__file__), 'resources')
TYPES_SHORT_NAMES_FILE = "types_short_names.dat"


def get_uniprot_record(uniprot_ac, columns=None):
    """Get the raw UniProt record."""
    url = 'https://www.uniprot.org/uniprot/' + uniprot_ac + '.tab'
    params = None
    if columns is not None:
        params = {'columns': columns}
    data = requests.get(url, params=params)
    if data.status_code == 200:
        return data.text
    else:
        return None


def get_interpro_entries(uniprot_ac):
    """Get the raw InterPro enties."""
    # disable SSL verification to avoid config issues
    context = ssl._create_unverified_context()

    next_url = INTERPRO_BASE_URL.format(uniprot_ac)

    # json header
    results = []

    while next_url:
        try:
            req = request.Request(
                next_url, headers={"Accept": "application/json"})
            res = request.urlopen(req, context=context)
            # If the API times out due a long running query
            if res.status == 408:
                # wait just over a minute
                sleep(61)
                # then continue this loop with the same URL
                continue
            elif res.status == 204:
                # no data so leave loop
                break
            payload = json.loads(res.read().decode())
            next_url = payload["next"]
        except HTTPError as e:
            if e.code == 408:
                sleep(61)
                continue
            else:
                raise e

        for i, item in enumerate(payload["results"]):
            results.append(item)

        # Don't overload the server, give it time before asking for more
        if next_url:
            sleep(1)

    return results


def fetch_gene_meta_data(uniprot_ac):
    """Fetch gene names."""
    res = get_uniprot_record(uniprot_ac)
    record = res.split("\n")[1].split("\t")[4].split(" ")
    return record[0], record[1:]


def fetch_canonical_sequence(uniprot_ac):
    """Import canonical sequence from UniProt."""
    result = None
    if uniprot_ac is not None:
        data = get_uniprot_record(uniprot_ac, ['sequence'])
        if data is not None:
            result = data.split()[1]
    return result


def overlap(start1, end1, start2, end2):
    """Compute the ratio of overlap."""
    ratio = 0
    # First, check if there is an overlap at all.
    highstart = max(start1, start2)
    lowend = min(end1, end2)
    if highstart < lowend:
        # Compute number of overlapping residues
        overlap = lowend - highstart
        # Compute the total span
        lowstart = min(start1, start2)
        highend = max(end1, end2)
        span = highend - lowstart
        # Compute ratio
        ratio = float(overlap) / float(span)
    return ratio


def generate_canonical_name(interproids, names):
    """Generate canonical domain name."""
    PK = "IPR000719"
    PK_name = "Protein kinase"
    SH2 = "IPR000980"
    SH2_name = "SH2"
    if PK in interproids:
        return PK_name
    elif SH2 in interproids:
        return SH2_name
    else:
        if len(names) > 0:
            return names[0]


def merge_raw_domains(raw_domains, overlap_threshold=0.8):
    """Merge overlapping domains."""
    groups = {
        i: set() for i in range(len(raw_domains))
    }
    visited = set()

    for i, raw_domain1 in enumerate(raw_domains):
        if i not in visited:
            visited.add(i)
            start1 = raw_domain1["start"]
            end1 = raw_domain1["end"]
            for j, raw_domain2 in enumerate(raw_domains):
                if j not in visited:
                    start2 = raw_domain2["start"]
                    end2 = raw_domain2["end"]
                    o = overlap(start1, end1, start2, end2)
                    if o >= overlap_threshold:
                        if i in groups:
                            groups[i].add(j)
                            if j in groups:
                                del groups[j]
                        visited.add(j)
    domains = []
    for k, v in groups.items():
        domain = {}
        d0 = raw_domains[k]
        domain["interproids"] = [d0["interproid"]]
        domain["names"] = [d0["name"]]
        starts = [d0["start"]]
        ends = [d0["end"]] 
        for vv in v:
            d = raw_domains[vv]
            domain["interproids"].append(d["interproid"])
            domain["names"].append(d["name"])
            starts.append(d["start"])
            ends.append(d["end"])
        domain["end"] = min(starts)
        domain["start"] = min(ends)
        domain["canonical_name"] = generate_canonical_name(
            domain["interproids"], domain["names"])
        domains.append(domain)
    return domains


def fetch_gene_domains(uniprot_ac, merge_features=True,
                       merge_overlap=0.8):
    """Fetch all the domains from InterPro."""
    result = get_interpro_entries(uniprot_ac)
    raw_domains = []
    for r in result:
        feature_type = r["metadata"]["type"]
        if feature_type == "domain":
            for p in r["proteins"]:
                if p["accession"] == uniprot_ac.lower():
                    for location in p["entry_protein_locations"]:
                        for fragment in location["fragments"]:
                            domain = {}
                            domain["interproid"] = r["metadata"]["accession"]
                            domain["name"] = r["metadata"]["name"]
                            domain["start"] = fragment["start"]
                            domain["end"] = fragment["end"]
                            raw_domains.append(domain)
    domains = merge_raw_domains(raw_domains, merge_overlap)
    return domains
