""" Class AgentAnatomy. 

Provide the structural features of a protein based on information from 
biological knowledge databases.
"""

import urllib.request
import json
import re
from collections import OrderedDict

class AgentAnatomy(object):
    """ 
    Gather structural information about protein with given UniProt 
    Accession Number or HGNC Gene Symbol.
    """
    # Feature Types: 1.topo 2.domain 3.repeat 4.motif 5.ptnbind 6.orgbind 
    # 7.activesite 8.phospho 9.mutation 10.glyco 11.other
    features = OrderedDict([ ('topology', []), ('domains', []) ])
    
    def __init__(self, query):
        self.query = query
        pass


    # /////////// Gene Symbols /////////////

    # This section deals with entries that are
    # HGNC Gene Symbols rather that UniProt ACs.
    def possible_acs(self, gene, organism, reviewed):
        """ 
        Obtain UniProt accessions associated with a gene symbol for 
        given organism. 
        """
        # Format a UniProt query with input gene name.
        queryline = '?query=gene:%s&sort=score&format=txt&fil=' % gene
        if organism != 0:
            queryline = queryline + 'organism%%3A\"%s\"' % organism
            if reviewed != 0:
                queryline = queryline + '+AND+'
        if reviewed != 0:
            queryline = queryline + 'reviewed%%3A%s' % reviewed    
        # Fetch from UniProt.
        try:
            queryfile = urllib.request.urlopen('http://www.uniprot.org/uniprot/'
                                               '%s' % queryline)
        except:
            print('\nCannot connect to UniProt. Network may be down.\n')
            exit()
        readquery = queryfile.read().decode("utf-8")
        entries = readquery.splitlines()
        # Search output for UniProt entries with GN Name or Synonyms that
        # exactly match the searched gene (case insensitive).
        nentries = 0 # Number of entries before filtering for exact gene name.
        aclist = []
        for i in range(len(entries)):
            line = entries[i]
            # Get UniProt ID and Accession number.
            if line[0:5] == 'ID   ':
                nentries += 1
                tokens = line.split()
                uniprotid = tokens[1]
                nextline = entries[i+1]
                nexttokens = nextline.split()
                uniprotac = nexttokens[1][:-1]
                entry = [uniprotid, uniprotac]
            # Check if the gene name really matches.
            if line[0:5] == 'GN   ':
                names = line[5:]
                if re.search('[= /]%s[,;/ ]' % gene.lower(), names.lower()):
                    entry.append(names)
                    aclist.append(entry)
        return aclist
    
    def getac_from_gene(self, genesymbol):
        """ Obtain UniProt AD assuming the user searches human genes. """
        organism = 'human'
        # Get UniProt accession numbers matching with input gene name (all species).
        allspecies = self.possible_acs(genesymbol, 0, 'yes')
        nall = len(allspecies)
        # Get UniProt accession numbers matching with input gene name (defined species).
        defspecies = self.possible_acs(genesymbol, organism, 'yes')
        ndef = len(defspecies)
        # Print results and suggestions to the user.
        print('\nQuery does not match any UniProt entry.\n')
        print('Treating query as a HGNC Gene Symbol. ' 
              'Trying to get UniProt AC for gene "%s"\n' %genesymbol)
        print('%i reviewed (SwissProt) UniProt ACs correspond to gene ' 
              'symbol or synonym "%s".' % (nall, genesymbol) )
        if nall > 0:
            print('List1 =', end="")
            for entry in allspecies:
                print(' %s' % entry[1], end="")
            print('')
        print('')
        if nall > 0:
            print('%i reviewed (SwissProt) UniProt ACs '
                  'from organism "%s".' % (ndef, organism) )
            if ndef > 0:
                print('List2 =', end="")
                for entry in defspecies:
                    print(' %s' % entry[1], end="")
                print('')
            print('')
        if nall == 0:
            print('No match found. Please check if gene symbol or '
                  'UniProt AC as correctly entered.\n')
        if nall > 0 and ndef == 0:
            print('No match found for organism "%s". You may '
                  'want to check ACs from List1, if any.\n' % org)
        if ndef == 1:
            print('Running AgentAnatomy with UniProt AC : %s \n' % defspecies[0][1] )
            return defspecies[0][1]
        if ndef > 1:
            print('Many possible choices. The AC you are looking '
                  'for is most likely in List2.')
            print('Please review ACs from List2 on UniProt '
                  'to choose the proper AC and rerun')
            print('AgentAnatomy with the chosen AC.\n')
        if nall == 0 or ndef != 1:
            print('Aborting. No instance of AgentAnatomy was created.\n')
            exit()

    # //////////////////////////////////////


    # +++++++++++++ UniProt ++++++++++++++++

    def get_uniprot(self):
        """ Retrieve UniProt entry from the web. """
        try:
            fetchfile = urllib.request.urlopen('http://www.uniprot.org/'
                                               'uniprot/%s.txt' % self.query)
            self.uniprotac = self.query
            print('\nUniProt entry found. Creating instance of AgentAnatomy.\n')
        except:
            self.uniprotac = self.getac_from_gene(self.query)
            fetchfile = urllib.request.urlopen('http://www.uniprot.org/'
                                               'uniprot/%s.txt' % self.uniprotac)
        readfile = fetchfile.read().decode("utf-8")
        self.entry = readfile.splitlines()
        #print(readfile)  # Print web page for debugging

  
    def find_uniprot(self):
        """ Alternatively, find UniProt entry in provided uniprot file. """
        uniprotfile = open('../uniprot_sprot_human.dat','r').read()
        uniprotlines = uniprotfile.splitlines()
        #print(uniprotfile)  # Print web page for debugging
  
        l = len(uniprotlines)
        for i in range(l):
            linei = uniprotlines[i]
            if linei[0:2] == 'AC' and self.uniprotac in linei:
                # Move upward to find beginning of entry.
                for j in range(i, 0, -1):
                    linej = uniprotlines[j]
                    if linej[0:2] == '//':
                        start = j+1
                        break 
                # Move downward to find end of entry.
                for j in range(i, l):
                    linej = uniprotlines[j]
                    if linej[0:2] == '//':
                        end = j
                        break
                break
        self.entry = uniprotlines[start:end]
  

    def format_uniprot(self):
        """ Extract and format feature lines from UniProt entry. """
        ftlist = []
        counter = 1
        for line in self.entry:
            #print(line[2:6])
            if line[0:2] == 'FT' and line[5] != " ":
                feature = line[5:]
                # Put a carriage return at then end of previous feature.
                if counter > 1:
                    ftlist[-1] = ftlist[-1]+'\n'
                # Add feature to list.
                ftlist.append("%3i  %s" % (counter, feature))
                counter += 1        
                # Keep track of whether the line ends with a dash. If so, do 
                # not put a space while adding info during next if statement.
                prevdash = 0
                if feature[-1] == '-':
                    prevdash = 1
            if line[0:2] == 'FT' and line[5] == " ":
                addedinfo = line[34:]
                # Add a space if previous line ended with a period or coma.
                if prevdash == 0:
                    ftlist[-1] = ftlist[-1] + ' ' + addedinfo
                else:
                    ftlist[-1] = ftlist[-1] + addedinfo
                # Keep track of dashes here too.
                prevdash = 0
                if addedinfo[-1] == '-':
                    prevdash = 1
        ftlist[-1] = ftlist[-1]+'\n'
        self.ftlines = ftlist
  

    def fill_uniprot(self):
        """ 
        Fill the data structure (the ordered dictionary) with 
        data from UniProt. 
        """
        for line in self.ftlines:
            tokens = line.split()
            # Topological domains
            if 'TOPO_DOM' in tokens[1] and 'Extracellular' in tokens[4]:
                start, end = int(tokens[2]), int(tokens[3])
                newentry = OrderedDict([ ('name', 'extracellular'), 
                                         ('beg', start), ('end', end), 
                                         ('database', 'UniProt') ]) 
                self.features['topology'].append(newentry)
            if 'TOPO_DOM' in tokens[1] and 'Cytoplasmic' in tokens[4]:
                start, end = int(tokens[2]), int(tokens[3])
                newentry = OrderedDict([ ('name', 'cytoplasmic'), 
                                         ('beg', start), ('end', end), 
                                         ('database', 'UniProt') ])
                self.features['topology'].append(newentry)
            if 'TRANSMEM' in tokens[1]:
                start, end = int(tokens[2]), int(tokens[3])
                start, end = int(tokens[2]), int(tokens[3])
                newentry = OrderedDict([ ('name', 'transmembrane'),  
                                         ('beg', start), ('end', end),
                                         ('database', 'UniProt') ])
                self.features['topology'].append(newentry)
            # Domains
            if 'DOMAIN' in tokens[1]:
                # Find the first '.' in domain description
                for i in range(34,len(line)):
                  if line[i] == '.':
                    break
                name = line[34:i]
                start, end = int(tokens[2]), int(tokens[3])
                newentry = OrderedDict([ ('name', name), 
                                         ('beg', start), ('end', end), 
                                         ('database', 'UniProt') ])
                self.features['domains'].append(newentry)

    # ++++++++++++++++++++++++++++++++++++++++++++++
    

    # ~~~~~~~~~~~~~~ Pfam ~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_pfam(self):
        """ Retrieve Pfam entry from the web. """
        fetchfile = urllib.request.urlopen('http://pfam.xfam.org/protein/'
                                           '%s' % self.uniprotac)
        readfile = fetchfile.read().decode("utf-8")
        self.pfam = readfile.splitlines()
        #print(readfile)  # Print web page for debugging
    

    def fill_pfam(self):
        """ 
        Fill the data structure (the ordered dictionary) with 
        data from Pfam.
        """
        ndom = len(self.features['domains'])
        self.pfamidlist = []
        l = len(self.pfam)
        for i in range(l):
            line = self.pfam[i].lstrip()
            # Domains with a definite family
            if 'class="pfama' in line:
                pfam = line[17:24]
                linename = self.pfam[i+1].lstrip()
                # The name is located after the "greater than" symbol
                gt = linename[7:].index('>') + 7
                name = linename[gt+1:-9]
                linestart = self.pfam[i+2].lstrip()
                lineend = self.pfam[i+3].lstrip()
                start, end = int(linestart[4:-5]), int(lineend[4:-5])
                newentry = OrderedDict([ ('name', name), 
                                         ('beg', start), ('end', end), 
                                         ('database', 'Pfam'), 
                                         ('family', pfam) ])
                self.features['domains'].append(newentry)
                # Keep a separate list of the Pfam families that were found.
                # Used in method fill_ipfam
                self.pfamidlist.append([pfam, ndom])
                ndom += 1
            # Transmembrane topological domain
            if 'class="domain"' in line and 'transmembrane' in line:
                linestart = self.pfam[i+2].lstrip()
                lineend = self.pfam[i+3].lstrip()
                start, end = int(linestart[4:-5]), int(lineend[4:-5])
                newentry = OrderedDict([ ('name', 'transmembrane'), 
                                         ('beg', start), ('end', end), 
                                         ('database', 'Pfam') ])
                self.features['topology'].append(newentry)
#            # Domains without a Pfam family (Ignore?)
#            if 'class="domain"' in line and 'transmembrane' not in line:
#                name = line[19:-5]
#                linestart = self.pfam[i+2].lstrip()
#                lineend = self.pfam[i+3].lstrip()
#                start, end = int(linestart[4:-5]), int(lineend[4:-5])
#                newentry = OrderedDict([ ('name', name), 
#                                         ('beg', start), ('end', end), 
#                                         ('database', 'Pfam') ])
#                self.features['domains'].append(newentry) 

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  
    # ////////////// iPfam /////////////////////////

    def get_ipfam(self, pfamdomain):
        """ Retrieve Pfam entry from the web. """
        fetchfile = urllib.request.urlopen('http://ipfam.org/family/'
                                           '%s/fam_int' % pfamdomain[0])
        readfile = fetchfile.read().decode("utf-8")
        self.ipfam = readfile.splitlines()
        #print(readfile)  # Print web page for debugging
  

    def fill_ipfam(self, pfamdomain):
        """ 
        Fill the data structure (the ordered dictionary) with 
        data from iPfam. 
        """
        # First, find which domain entry of self.features corresponds
        # to the member of self.pfamidlist.
        d = pfamdomain[1]
        self.features['domains'][d]['iPfam interaction'] = []    
        # Then, add the interacting Pfam IDs to the domain entry.
        l = len(self.ipfam)
        for i in range(l):
            line = self.ipfam[i].lstrip()
            if "<td><a href='/family/" in line:
                inter = line[21:28]
                self.features['domains'][d]['iPfam interaction'].append(inter)

  
    def add_ipfam(self):
        """ 
        Add all the Pfam interaction by looping 
        methods get_ipfam and fill_ipfam.
        """
        for dom in self.pfamidlist:
            self.get_ipfam(dom)
            self.fill_ipfam(dom)

    # //////////////////////////////////////////////

  
    # ------------- Display methods ----------------

    def displayfeatures(self):
        """ Print FT lines from UniProt entry. """
        for element in self.ftlines:
            print(element, end='')

  
    def featuresjson(self):
        """ Print the agent's features in JSON format. """
        return json.dumps(self.features, indent=4)

    # ----------------------------------------------
  

    # Default usage

    def getfeatures(self):
        """ Query information from the web and outputs to JSON. """
        # UniProt
        self.get_uniprot()
        self.format_uniprot()
        self.fill_uniprot()
        # Pfam
        self.get_pfam()
        self.fill_pfam()
        # iPfam
        self.add_ipfam()
        
        return json.dumps(self.features, indent=4)
 
