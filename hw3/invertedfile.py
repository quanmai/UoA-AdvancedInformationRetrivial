#----------------------------------------
# Filename:  invertedfile.py
# To run:    python3 invertedfile.py <indir> <outdir>
# e.g:       python3 invertedfile.py ../input/ output/
#----------------------------------------

import os.path
import ply.lex as lex
import sys
import glob
import collections
from ply.lex import TOKEN
import time, timeit
import subprocess
from typing import NamedTuple, Tuple, List
import atexit
import re
import math
from lconstant import *
import nltk
# nltk.download('stopwords')
from nltk.corpus import stopwords

POSTFILE = "post_file.txt" # DOCID TFIDF
DICTFILE = "dict_file.txt"  # TERM NUMDOC START
MAPPFILE = "mapping_file.txt" # DOCID DOCNAME
EMPTYSTR = "_empty"
NUM_FILES = 1750
KEYS = 75
STOPWORDS = set(stopwords.words('english'))

fixed_len_word = lambda x: x[:LWORD] if len(x) >= LWORD else x + " " * (LWORD - len(x))

class StringIntPair(NamedTuple):
    key: str
    data: List[Tuple[int, int]] # doc_id, freq

class HashTable:
    def __init__(self, num_keys: int, num_files: int):
        self.empty_str = EMPTYSTR
        self.size = num_keys * num_files * 3 # save 2/3 for linear probing
        self.used = 0
        self.collisions = 0
        self.lookups = 0
        self.hashtable = [StringIntPair(self.empty_str, (-1, -1))] * self.size
        atexit.register(self.cleanup)

    def cleanup(self):
        self.hashtable.clear()

    def insert(self, key: str, data: tuple):
        index = -1
        if self.used >= self.size:
            print("The hashtable is full; cannot insert.")
        else:
            index = self.hash(key)
            if self.hashtable[index].key == self.empty_str:
                self.hashtable[index] = StringIntPair(key, [data])
            else:
                self.hashtable[index].data.append(data)
            self.used += 1

    def getData(self, key: str) -> List[Tuple]:
        self.lookups += 1
        index = self.hash(key)
        if self.hashtable[index].key == self.empty_str:
            return -1
        else:
            return self.hashtable[index].data

    def __iter__(self):
        return ((k, v) for (k, v) in self.hashtable)
    
    def hash(self, key):
        sum = 0
        # add all the characters of the key together
        for k in key:
            sum = (sum * 19) + ord(k)   # Mult sum by 19, add byte value of char
   
        index = sum % self.size

        # linear probing
        while self.hashtable[index].key != self.empty_str and self.hashtable[index].key != key:
            index = (index + 1) % self.size
            self.collisions += 1
       
        return index
    
# list of TOKENS (required)
tokens = ['CSS',
          'HTMLENTITY',
          'HTMLTAG',
          'HTMLCOMMENT',
          'HYPERLINK',
          'NUMBER',
          'EMAIL',
          'WORD']

def MyLexer():
    def t_CSS(t):
        r'([\S^,]*,\s*)*\S+\s*{[^}]+}'

    # Remove html special tokens, such as &gt; &amp;
    def t_HTMLENTITY(t):
        r'\&\w+'

    def t_HTMLTAG(t):
        r'<[^>]+>'

    def t_HTMLCOMMENT(t):
        r'/\*.*?\*/'

    # Remove the https, www part, keep the name of url
    def t_HYPERLINK(t):
        r'(htt(p|ps):\/\/|www.)[^\s<\/]+'
        t.value = t.value.lower()
        t.value = re.sub(r'(https://|http://|www\.)', '', t.value)
        return t

    def t_NUMBER(t):
        r'[1-9](\d|,|\.|-)*'
        t.value = re.sub('(,|-|\.\S*)', '', t.value)
        return t

    # Keep email unchange
    def t_EMAIL(t):
        r'\S+@\S+\.[^<\s,?!.\xa0\x85]+'
        # t.value = re.sub('(@.*|<[^>]+>)', '', t.value)
        return t

    def t_WORD(t):
        r'[A-z](\w|\'|-|\.\w|<[^>]+>)*'
        t.value = t.value.lower()
        t.value = re.sub('(\.|-|\'|<[^>]+>)', '', t.value)
        return t
    
    t_ignore  = ' []+$|=%*{}/0-"#>();:!?.,\t\xa0\x85\xe2\x00'

    def t_error(t):
        t.lexer.skip(1)

    return lex.lex()

# def pad(x, lconstant): #pad after
#     # pad to number of FIX_LEN[name] BYTES
#     return str(x) + " " * (lconstant - len(str(x)))
def pad(x, lconstant): #pad, truncate
    # normalize the string to lconstant characters
    return str(x)[:lconstant] if len(str(x)) >= lconstant else str(x) + " " * (lconstant - len(str(x)))

# global_dict: list((doc_id, rfreq))
def read_one_file(global_dict: HashTable, lexer: callable, 
                  file_name: str, doc_id: int, raw_freq: bool = True):
    dict = collections.defaultdict(int)
    valid_tokens = 0
    num_tokens = 0
    with open(file_name, 'r') as rf:
        print("Process file: ", file_name)
        lines = rf.readlines()
        for line in lines:
            try:
                corpus = str(line.strip())
                lexer.input(corpus)
                for token in lexer:
                    tok = token.value
                    # Do not write words that has only 1 character
                    # Do not include stopwords
                    if len(tok) > 1 and tok not in STOPWORDS:
                        dict[tok] += 1
                        valid_tokens += 1
                    num_tokens += 1
            except EOFError:
                break
    for k, v in dict.items():
        freq = v if raw_freq else v/num_tokens
        global_dict.insert(k, (doc_id, freq))
    return valid_tokens

if __name__ == '__main__':
    """ 
    TF-IDF
        (1) the postings file should stored length normalized term weights
        (2)create fixed length output files for the dict, post, and mapfiles
    Processing
        (1) Remove low frequency words
        (2) Remove stopwords
        (3) Remove words of length 1
    """
    lexer = MyLexer()
    inputDir = sys.argv[1]
    outputDir = sys.argv[2]
    if not os.path.exists(inputDir) or not os.path.exists(outputDir):
        print("Path not valid \n Enter valid path ")
        quit()

    # sort files by name (optional)
    sort_files_command = f"ls {inputDir} | cut -d. -f1 | sort -V"
    result = subprocess.run(sort_files_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        sorted_files = result.stdout.split('\n')
    else:
        print("Error:", result.stderr)
    list_of_files = [os.path.join(inputDir, file + ".html") for file in sorted_files if file.strip()]
    num_files = min(len(list_of_files), NUM_FILES)
    ###

    # time_start = timeit.default_timer()
    time_start = time.process_time()
    corpora_size = 0
    globaldict = HashTable(KEYS, num_files)

    # MAPPING: DOCID \t DOCNAME
    f = open(os.path.join(outputDir, MAPPFILE), 'w')
    for i, file_name in enumerate(list_of_files[:num_files]):
        ff = os.path.basename(file_name).split('.')
        name, fformat = ff[0], ff[1]
        pad_filename = " " * (LFILENAME - len(name)) + name
        pad_filename += "." + fformat
        pad_fileid = pad(i, LNUMDOC)
        f.write("{}\t{}\n".format(pad_fileid, pad_filename))
        corpora_size += read_one_file(globaldict, lexer, file_name, i, False)
    f.close()
    dictc = postc = corpora_size
    # DICTFILE: TERM \t NUMDOC \t START
    f = open(os.path.join(outputDir, DICTFILE), 'w')
    start = 0
    empty_fixed_len = pad(globaldict.empty_str, LWORD)
    for k, v in globaldict:
        fixed_len_k = fixed_len_word(k)
        if k == globaldict.empty_str: # or len(v) == 1 and v[0][1] == 1:
            n, s = -1, -1
            # f.write("{}\t{:04}\t{:08}\n".format(empty_fixed_len, n, s))
            f.write("{}\t{}\t{}\n".format(empty_fixed_len, pad(n, LNUMDOC), pad(s, LSTART)))
        else:
            num_docs = len(v)
            # If term appears only ONCE in the collection, turn it to empty entry
            # If we remove it, we cannot trace other terms as we broke the hash indexing!
            if num_docs == 1 and v[0][1] == 1:
                # f.write("{}\t{:04}\t{:08}\n".format(empty_fixed_len, -1, -1))
                f.write("{}\t{}\t{}\n".format(empty_fixed_len, pad(-1, LNUMDOC), pad(-1, LSTART)))
                start += 1
                continue
            # f.write("{}\t{:04}\t{:08}\n".format(fixed_len_k, num_docs, start))
            f.write("{}\t{}\t{}\n".format(fixed_len_k, pad(num_docs, LNUMDOC), pad(start, LSTART)))
            start += num_docs

    # POST FILE: DOCID \t TFIDF
    f = open(os.path.join(outputDir, POSTFILE), 'w')
    for k, v in globaldict:
        if k == globaldict.empty_str or (len(v) == 1 and v[0][1] == 1):
            continue
        for doc_id, freq in v:
            idf = 1 + math.log10(num_files / len(v))
            tfidf = freq * idf
            f.write("{}\t{}\n".format(pad(doc_id, LNUMDOC), pad(tfidf, LTFIDF)))
    f.close()
    print('Time run for {} files: {}'.format(num_files, time.process_time() - time_start))