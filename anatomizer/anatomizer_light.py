"""Collection of utils for fetching data online on the fly."""
import os
import requests
from anatomizer.utils import _merge_fragments, _nest_domains


RESOURCES = os.path.join(os.path.dirname(__file__), 'resources')
TYPES_SHORT_NAMES_FILE = "types_short_names.dat"


def get_uniprot_record(uniprot_ac, columns=None):
    url = 'https://www.uniprot.org/uniprot/' + uniprot_ac + '.tab'
    params = None
    if columns is not None:
        params = {'columns': columns}
    data = requests.get(url, params=params)
    if data.status_code == 200:
        return data.text
    else:
        return None


def get_interpro_record(ipr_id):
    url = "http://www.ebi.ac.uk/Tools/dbfetch/dbfetch/interpro/" + ipr_id + "/tab"
    data = requests.get(url)
    if data.status_code == 200:
        return data.text
    else:
        return None


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


def fetch_gene_domains(uniprot_ac, merge_features=True,
                       nest_features=True, merge_overlap=0.7, nest_overlap=0.7,
                       nest_level=1):
    """Fetch all the domains online."""
    url = "https://www.ebi.ac.uk/interpro/protein/" + uniprot_ac + "?export=tsv"
    data = requests.get(url)
    if data.status_code == 200:
        try:
            raw_tab = data.text.split("\n")[1:]
            features = []
            for row in raw_tab:
                record = row.split("\t")
                if len(record) > 1:
                    # print(record)
                    feature_dict = {}
                    feature_dict['ipr_id'] = record[11]
                    feature_dict['ipr_name'] = record[12]
                    feature_dict['xname'] = record[5]
                    feature_dict['xid'] = record[4]
                    feature_dict['xdatabase'] = record[3]

                    feature_dict['ipr_id'] = record[11]
                    feature_dict['ipr_name'] = record[12]

                    # Get type and short name
                    file = os.path.join(RESOURCES, TYPES_SHORT_NAMES_FILE)
                    short_name = None
                    feature_type = None
                    if os.path.isfile(file):
                        with open(file, "r+") as f:
                            for l in f:
                                row = l.split("\t")
                                if len(row) == 3:
                                    if row[0] == feature_dict['ipr_id']:
                                        feature_type = row[1]
                                        short_name = row[2]
                                        break
                    if short_name is None or feature_type is None:
                        data = get_interpro_record(feature_dict['ipr_id'])
                        if data is not None:
                            ipr_record = data.split("\n")[2].split("\t")
                            if len(ipr_record) > 1:
                                feature_dict["short_name"] = ipr_record[2]
                                feature_dict["feature_type"] = ipr_record[1]
                    else:
                        feature_dict['short_name'] = short_name
                        feature_dict['feature_type'] = feature_type

                    start = int(record[6])
                    end = int(record[7])
                    length = end - start
                    feature_dict['start'] = start
                    feature_dict['end'] = end
                    feature_dict['length'] = length
                    if len(feature_dict['ipr_id']) > 0 and\
                       feature_dict["feature_type"] == "Domain":
                        features.append(feature_dict)

            domains = []
            if merge_features:
                domains = _merge_fragments(
                    features, overlap_threshold=merge_overlap)
            else:
                return features

            # 4. (optional) Nest features
            if nest_features:
                domains = _nest_domains(domains, merge_overlap, max_level=nest_level)

            return domains

        except Exception as e:
            print(e)
