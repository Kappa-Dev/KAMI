""" Class AgentAnatomy. 

Provide the structural features of a protein based on information from 
biological knowledge databases.
"""

import os
import re
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom
import json
from collections import OrderedDict

class AgentAnatomy(object):
    """ 
    Gather structural features about a protein with given
    HGNC Gene Symbol or UniProt Accession Number
    """

    workdir = 'anatomyfiles'

    species = 'homo_sapiens'

    ensemblserv = 'http://rest.ensembl.org'

    interprofile = 'interpro.xml'

    def __init__(self, query):
        """
        Look if query matches a unique Ensembl gene.
        If so, initialize an AngentAnatomy instance. Otherwise, abort.
        """

        self.query = query
        os.makedirs(self.workdir, exist_ok=True)
        
        ensemblext = '/xrefs/symbol/%s/%s?' % (self.species, self.query)
        decoded = self._fetch_ensembl(ensemblext)
        genes = []
        for entry in decoded:
            ensid = entry['id']
            if ensid[0:4] == 'ENSG':
                genes.append(ensid)
        if len(genes) == 1:
            self.ensemblgene = genes[0]
            print('Creating instance of AgentAnatomy with Ensembl Gene ID %s.'
                  % self.ensemblgene)
        else:
            print('Could not find unique Ensembl Gene ID. Aborting.')
            exit()


    def get_proteins(self):
        self._get_hgncsymbol()
        self._get_strand()
        self._get_transcripts()
        self._get_hgnctranscr()
        self._get_uniprotids()
        self._get_uniprotdupl()
        self._get_length()
        self._get_canon()
        self._sort_ptnlist()
        #self.print_json(self.thing)

    # ------ Methods to get protein definitions -----

    def _fetch_ensembl(self,ext):
        r = requests.get(self.ensemblserv+ext,
                         headers={ "Content-Type" : "application/json"})
        if not r.ok:
            r.raise_for_status()
            sys.exit()
        return r.json()


    def _get_hgncsymbol(self):
        ensemblext = '/xrefs/id/%s?' % self.ensemblgene
        xreflist = self._fetch_ensembl(ensemblext)
        for xref in xreflist:
            if xref['db_display_name'] == 'HGNC Symbol':
                self.hgncsymbol = xref['display_id']


    def _get_strand(self):
        ensemblext = '/lookup/id/%s?' % self.ensemblgene
        lookgene = self._fetch_ensembl(ensemblext)
        self.strand = lookgene['strand']


    def _get_transcripts(self):
        ensemblext = '/overlap/id/%s?feature=cds' % self.ensemblgene
        cdslist = self._fetch_ensembl(ensemblext)
        deflist = []
        for cds in cdslist:
            if cds['strand'] == self.strand:
                deflist.append( OrderedDict([ 
                                ('Ensembl_transcr', cds['Parent']), 
                                ('Ensembl_protein', cds['protein_id']) ]) )
        # Remove duplicates (set does not work with dictionaries)
        self.ptnlist = []
        for item in deflist:
            if item not in self.ptnlist:
                self.ptnlist.append(item)


    def _get_hgnctranscr(self):
        for i in range(len(self.ptnlist)):
            enst = self.ptnlist[i]['Ensembl_transcr']
            ensemblext = '/xrefs/id/%s?' % enst
            transcrxreflist = self._fetch_ensembl(ensemblext)
            for txref in transcrxreflist:
                if txref['dbname'] == 'HGNC_trans_name':
                    self.ptnlist[i]['Transcript_name'] = txref['primary_id']


    def _get_uniprotids(self):
        for i in range(len(self.ptnlist)):
            ensp = self.ptnlist[i]['Ensembl_protein']
            ensemblext = '/xrefs/id/%s?' % ensp
            protxreflist = self._fetch_ensembl(ensemblext)
            #self.print_json(protxreflist)
            for pxref in protxreflist:
                if pxref['db_display_name'][:9] == 'UniProtKB':
                    self.ptnlist[i]['UniProt_accession'] = pxref['primary_id']
                    ## Optionally show if from Swiss-prot or TrEMBL
                    #self.ptnlist[i]['UniProt_db'] = pxref['db_display_name'][10:]


    def _fetch_uniprotxml(self,uniprotac):
        """ Retrieve UniProt entry from the web in xml format. """
        if ('uniprot%s.xml' % uniprotac) in os.listdir(self.workdir):
            xmlfile = open('%s/uniprot%s.xml' 
                           % (self.workdir, uniprotac),'r')
            uniprot = xmlfile.read()
            print('Using UniProt entry from file %s/uniprot%s.xml.\n' 
                  % (self.workdir, uniprotac))
        else:
            r = requests.get('http://www.uniprot.org/uniprot/%s.xml' 
                             % uniprotac)
            xmlparse = xml.dom.minidom.parseString(r.text) 
            uniprot = xmlparse.toprettyxml(indent="   ",newl='')
            # Write xml to file to avoid download on future uses
            savefile = open('%s/uniprot%s.xml'
                            % (self.workdir, uniprotac),'w')
            savefile.write(uniprot)
            print('Fetched file from http://www.uniprot.org/uniprot/%s.xml.\n'
                  % uniprotac)
        # Removing default namespace to simplify parsing.
        xmlnonamespace = re.sub(r'\sxmlns="[^"]+"', '', uniprot, count=1)
        root = ET.fromstring(xmlnonamespace)
        return root


    def _get_uniprotdupl(self):
        seen = []
        duplicates = set()
        for ptn in self.ptnlist:
            ac = ptn['UniProt_accession']
            if ac in seen:
                duplicates.add(ac)
            else:
                seen.append(ac)
        # Check UniProt to distinguish ENSPs that have a same UniProt AC.
        for unip in list(duplicates):
            uniprotxml = self._fetch_uniprotxml(unip)
            # Check all the ENSTs from ptnlist that have AC "unip".
            for i in range(len(self.ptnlist)):
                if self.ptnlist[i]['UniProt_accession'] == unip:
                    enst = self.ptnlist[i]['Ensembl_transcr']
                    # Sometimes, the different ENSPs are actually the same
                    # sequence, so there is no 'molecule' entry in the UniProt
                    # file. I should implement something to compare the sequences
                    # to be sure they are the same.
                    try:
                        molecule = uniprotxml.find(".//dbReference[@id='%s']/"
                                                   "molecule" % enst)
                        self.ptnlist[i]['UniProt_'
                                        'accession'] = molecule.get('id')
                    except:
                        pass


    def _get_length(self):
        for i in range(len(self.ptnlist)):
            ensp = self.ptnlist[i]['Ensembl_protein']
            ensemblext = '/lookup/id/%s?' % ensp
            lookptn = self._fetch_ensembl(ensemblext)
            self.ptnlist[i]['Length'] = lookptn['length']


    # I will have to improve detection of the principal isoform
    # by taking into account the UniProt canonical, Appris Plevel and TSL.
    # The canonical in a Uniprot file is the <isoform> with
    # <sequence type="displayed"/>
    def _get_canon(self):
        """ Get canonical (primary) transcript from APPRIS """
        r = requests.get('http://apprisws.bioinfo.cnio.es:80/rest/exporter/'
                         'id/%s/%s?methods=appris&format=json' 
                          % (self.species, self.ensemblgene) )
        appris = r.json()
        canontrancripts = []
        for isoform in appris:
            try:
                an = isoform['annotation']
                rel = isoform['reliability']
                if 'Principal Iso' or 'Possible Principal Isoform' in an:
                    if 'PRINCIPAL' in rel:
                        canontrancripts.append(isoform['transcript_id'])
            except:
                pass
        canonset = set(canontrancripts)
        if len(canonset) == 1:
            self.canontrancript = canontrancripts[0]
        else:
            #self.print_json(appris)
            print('Cannot find unique canonical (primary) transcript')
            #exit()
            # For the moment, just take the first ENST as canonical.
            self.canontrancript = self.ptnlist[0]['Ensembl_transcr']
        for i in range(len(self.ptnlist)):
            if self.ptnlist[i]['Ensembl_transcr'] == self.canontrancript:
                self.ptnlist[i]['Primary'] = 'Yes'
                self.canon = self.ptnlist[i]['Ensembl_protein']


    def _sort_ptnlist(self):
         self.sortedptns = sorted(self.ptnlist, key=lambda t: t['Transcript_name'])
         self.thing = OrderedDict([ ('HGNC_symbol', self.hgncsymbol), 
                                    ('Ensembl_gene_id', self.ensemblgene),
         #                           ('Strand', self.strand),
                                    ('Proteins', self.sortedptns) ])

    # ------ End of methods to get protein definitions -----

    # ====== Methods to get protein features ===============

    def get_features(self): 
        ensemblext = '/overlap/translation/%s?' % self.canon
        tmplist = self._fetch_ensembl(ensemblext)
        # Gene3D
        ignorelist = ['PIRSF', 'PANTHER', 'SignalP', 'Seg', 'Tmhmm', 'PRINTS']
        self.featurelist = []
        counter = 1
        for feature in tmplist:
            if feature['type'] not in ignorelist:
                self.featurelist.append({})
                self.featurelist[-1]['description'] = feature['description']
                self.featurelist[-1]['type'] = feature['type']
                self.featurelist[-1]['id'] = feature['id']
                self.featurelist[-1]['start'] = feature['start']
                self.featurelist[-1]['end'] = feature['end']
                self.featurelist[-1]['length'] = feature['end'] - feature['start']
                try:
                    self.featurelist[-1]['interpro'] = feature['interpro']
                except:
                    pass
                self.featurelist[-1]['internal_id'] = counter
                counter += 1
        #self.print_json(self.featurelist)


    def merge_features(self):
        self._find_groups()
        self._merge_groups() # Creates self.mergedfeaturelist.
        self._numerate_samename()
        #self.print_json(self.mergedfeaturelist)


    def _calc_overlap(self, f1, f2):
        """    
        Simple overlap ratio: number of overlapping residues / 
                              total span of the two features

                    -----------               -----------
        overlap     |||||||||        span  ||||||||||||||
                 ------------              ------------
        """
        starts = [ f1['start'], f2['start'] ]
        ends = [ f1['end'], f2['end'] ]
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


    def _find_groups(self):
        """ Find groups of features to be merged based on overlap. """
        overlapthreshold = 0.7
        # Get all the pairs of features that have 50% or more overlap between them.
        pairlist = []
        nfeatures = len(self.featurelist)
        for i in range(nfeatures):
            feature1 = self.featurelist[i]
            for j in range(i+1, nfeatures):
                feature2 = self.featurelist[j]
                overlap = self._calc_overlap(feature1, feature2)
                if overlap >= overlapthreshold:
                    pairlist.append([i+1,j+1])
        # Get the features that do not overlap with any other.
        paired = [item for pair in pairlist for item in pair]
        self.featuregroups = []
        for i in range(nfeatures):
            if i+1 not in paired:
                self.featuregroups.append([i+1])
        # Regroup pairs into groups.
        usedpairs = []
        for i in range(len(pairlist)):
            if i not in usedpairs:
                ref = pairlist[i]
                for j in range(i+1, len(pairlist)):
                    if pairlist[j][1] in ref:
                        ref.append(pairlist[j][0])
                        usedpairs.append(j)
                    if pairlist[j][0] in ref:
                        ref.append(pairlist[j][1])
                        usedpairs.append(j)
                group = sorted(set(ref))
                self.featuregroups.append(group)
        #print(self.featuregroups)


    def _merge_groups(self):
        """ 
        Create merged features based on the information from 
        the features in a group.
        """
        self.unsortedfeatures = []
        for group in self.featuregroups:
            # Name merged feature from the shortest 'description' in all 
            # the features regrouped under it. Also take the fewer number
            # of residues for length.
            nameslen = []
            lenghts = []
            for featid in group:
                desc = self.featurelist[featid-1]['description']
                nameslen.append( len(desc) )
                lenghts.append( int(self.featurelist[featid-1]['length']) )    
            # Find shortest 'description' and length.
            nindex = nameslen.index( min(nameslen) ) # indexes inside group.
            lindex = lenghts.index( min(lenghts) )   #
            nameindex = group[nindex] - 1
            lengthindex = group[lindex] - 1
            # Retrieve shortest 'description' and length from self.featurelist.
            name = self.featurelist[nameindex]['description']
            length = self.featurelist[lengthindex]['length']
            start = self.featurelist[lengthindex]['start']
            end = self.featurelist[lengthindex]['end']
            # Add selected information to merged feature.
            self.unsortedfeatures.append( OrderedDict([]) )
            self.unsortedfeatures[-1]['name'] = name
            self.unsortedfeatures[-1]['start'] = start
            self.unsortedfeatures[-1]['end'] = end
            self.unsortedfeatures[-1]['length'] = length
        # Sort by position on sequence
        self.mergedfeaturelist = sorted(self.unsortedfeatures, key=lambda t: t['start'])
        for i in range(len(self.mergedfeaturelist)):
            self.mergedfeaturelist[i]['merged_id'] = i+1


    def _numerate_samename(self):
        n = len(self.mergedfeaturelist)
        firstpass = {}
        for i in range(n):
            name = self.mergedfeaturelist[i]['name']
            if name not in firstpass:
                firstpass[name] = 1
            else:
                firstpass[name] = firstpass[name] + 1
        secondpass = {}
        for i in range(n):
            name = self.mergedfeaturelist[i]['name']
            if name not in secondpass:
                secondpass[name] = 1
                if firstpass[name] > 1:
                    self.mergedfeaturelist[i]['name'] = name+' #1'
            else:
                secondpass[name] = secondpass[name] + 1
                self.mergedfeaturelist[i]['name'] = name+' #%i' % secondpass[name]


    def nest_features(self):
        self._find_nesting()
        self._apply_nesting()



    def _nest_overlap(self, f1, f2):
        """    
        Nest overlap ratio: number of overlapping residues / 
                              span of the smallest feature

                       --------                  --------
        overlap        ||||||        span        ||||||||
                 ------------              ------------
        """
        ratio = 0
        # f1 is expected to be the largest feature
        if f1['length'] > f2['length']:
            starts = [ f1['start'], f2['start'] ]
            ends = [ f1['end'], f2['end'] ]
            # First, check if there is an overlap at all.
            highstart = max(starts)
            lowend = min(ends)
            if highstart < lowend:
                # Compute number of overlapping residues.
                overlap = lowend - highstart
                # Find smallest feature span.
                span = f2['length']
                # Compute ratio.
                ratio = float(overlap) / float(span)
        return ratio


    def _find_nesting(self):
        nestthreshold = 0.7
        # Sort features from smallest to largest.
        n = len(self.mergedfeaturelist)
        self.nestlist = []
        for x in range(n):
            self.nestlist.append([])
        for i in range(n):
            feature1 = self.mergedfeaturelist[i]
            for j in range(n):
                if i != j:
                    feature2 = self.mergedfeaturelist[j]
                    overlap = self._nest_overlap(feature1, feature2)
                    if overlap >= nestthreshold:
                        self.nestlist[i].append(j+1)
        #print(self.nestlist)


    def _apply_nesting(self):
        self.nestedfeaturelist = []
        donelist = []
        for i in range(len(self.nestlist)):
            if i not in donelist:
                self.nestedfeaturelist.append(self.mergedfeaturelist[i])
                subfeatlist = self.nestlist[i]
                if len(subfeatlist) > 0:
                    contained = []
                    for j in subfeatlist:
                        contained.append(self.mergedfeaturelist[j-1])
                        donelist.append(j-1)
                    self.nestedfeaturelist[-1]['contains'] = contained
        #self.print_json(self.nestedfeaturelist)


    def kami(self):
        outfile = open('%s.json' % self.hgncsymbol.lower(),'w')
        gap = 100
        n = len(self.mergedfeaturelist)
        initxpos = 400 - ( (n-1) * gap/2 )
        self.kami = OrderedDict([])
        self.kami['children'] = []
        self.kami['name'] = self.hgncsymbol

        nodes = []
        nodes.append( OrderedDict([]) )
        nodes[-1]['id'] = self.hgncsymbol
        nodes[-1]['input_constraints'] = []
        nodes[-1]['output_constraints'] = []
        nodes[-1]['type'] = 'agent'
        for feature in self.mergedfeaturelist:
            nodes.append( OrderedDict([]) )
            nodes[-1]['id'] = feature['name']
            nodes[-1]['input_constraints'] = []
            nodes[-1]['output_constraints'] = []
            nodes[-1]['type'] = 'region'

        edges = []
        for feature in self.mergedfeaturelist:
            edges.append( OrderedDict([]) )
            edges[-1]['attrs'] = {}
            edges[-1]['from'] = feature['name']
            edges[-1]['to'] = self.hgncsymbol

        positions = OrderedDict([])
        positions[self.hgncsymbol] = OrderedDict([])
        positions[self.hgncsymbol]['x'] = 400
        positions[self.hgncsymbol]['y'] = 350
        for i in range(n):
            feature = self.mergedfeaturelist[i]
            xpos = int(initxpos + gap*i+1)
            positions[feature['name']] = OrderedDict([])
            positions[feature['name']]['x'] = xpos
            positions[feature['name']]['y'] = 500

        attributes = OrderedDict([ ('positions', positions) ])
        top_graph = OrderedDict([])
        top_graph['attributes'] = attributes
        top_graph['edges'] = edges
        top_graph['nodes'] = nodes
        self.kami['top_graph'] = top_graph

        #outfile.write(self.print_json(self.kami))
        outfile.write(json.dumps(self.kami, indent=4))
        #self.print_json(self.kami)
        print('Wrote Kami agent representation '
              'to file %s\n' % self.hgncsymbol.lower() )
 
         

#    def old_apply_nesting(self):
#        self.nestedfeaturelist = self.mergedfeaturelist
#        # Find the largest number of features contained inside one.
#        largestnum = 0
#        for subfeatlist in self.nestlist:
#            l = len(subfeatlist)
#            if l > largestnum:
#                largestnum = l
#        # From the feature that contains the least subfeatures to
#        # the one that contains the most.
#        print(self.nestlist)
#        for num in range(1, largestnum+1):
#            i = 0
#            while i < len(self.nestlist):
#            #for i in range(len(self.nestlist)):
#                subfeatlist = self.nestlist[i]
#                if len(subfeatlist) == num: # Found a set of features to nest
#                    #print(subfeatlist,num)
#                    contained = []
#                    # Get the subfeatures and put them inside the proper feature
#                    for k in subfeatlist:
#                        # I have to create a new object from scratch.
#                        # Just doing contained.append(self.mergedfeaturelist[k-1])
#                        # brings a circular reference error.
#                        newobject = OrderedDict([])
#                        newobject['name'] = self.nestedfeaturelist[k-1]['name']
#                        newobject['start'] = self.nestedfeaturelist[k-1]['start']
#                        newobject['end'] = self.nestedfeaturelist[k-1]['end']
#                        newobject['length'] = self.nestedfeaturelist[k-1]['length']
#                        newobject['merged_id'] = self.nestedfeaturelist[k-1]['merged_id']
#                        contained.append(newobject)
#                    self.nestedfeaturelist[i]['contains'] = contained
#                    #self.nestedfeaturelist[i]['contains'] = contained
#                    #print(self.nestedfeaturelist[i])
#                    # Remove the subfeatures from the feature list 
#                    # (they now appear inside an other feature)
#                    for k in subfeatlist:
#                        self.nestedfeaturelist.pop(k-1)
#                    # Remove elements that take value k and
#                    # the kth value from nestlist.
#                    for k in subfeatlist:
#                        for j in range(len(self.nestlist)):
#                            if k in self.nestlist[j]:
#                                self.nestlist[j].remove(k)
#                        self.nestlist.pop(k-1)
#                    print(json.dumps(self.nestedfeaturelist, indent=4))
#                    print(self.nestlist)
#                    i = 0 # restart reading self.nestlist at the beginning after 
#                          # items were removed
#                print(len(self.nestlist), num, largestnum)
#                i += 1
#                    #break # restart the loop on self.nestlist because it changed.
#        #self.print_json(self.nestedfeaturelist)


    # ====== End of methods to get protein features ======

    def proteins(self):
        print('-----')
        print(json.dumps(self.thing, indent=4))
        print('-----')

    def features(self):
        print('-----')
        print(json.dumps(self.featurelist, indent=4))
        print('-----')

    def mergedfeatures(self):
        print('-----')
        print(json.dumps(self.mergedfeaturelist, indent=4))
        print('-----')

    def nestedfeatures(self):
        print('-----')
        print(json.dumps(self.nestedfeaturelist, indent=4))
        print('-----')


    def print_json(self,data):
        print(json.dumps(data, indent=4))
