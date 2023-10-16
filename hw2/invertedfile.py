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

POSTFILE = "post_file.txt"
DICTFILE = "dict_file.txt"
MAPPFILE = "mapping_file.txt"
EMPTYSTR = "_empty"
KEYS = 75

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

# global_dict: list((doc_id, rfreq))
def read_one_file(global_dict: HashTable, lexer: callable, 
                  file_name: str, doc_id: int, raw_freq: bool = True):
    dict = collections.defaultdict(int)
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
                    dict[tok] = dict.get(tok, 0) + 1
                    num_tokens += 1
            except EOFError:
                break
    for k, v in dict.items():
        freq = v if raw_freq else v/num_tokens
        global_dict.insert(k, (doc_id, freq))
    return num_tokens

if __name__ == '__main__':
    """ Output Files The goal is to build a trio of files, dict, post, and map. 
        (1) The dictionary should contain one entry per unique word:
            the term 
            the number of documents that contain that term
            the location of the first record in the postings file
        (2) The postings file should contain one entry per unique word per document:
            the document id
            the raw frequency of the word in the document
        (3) The mappings file should contain one entry per document
            the document id
            the filename
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
    ###

    # time_start = timeit.default_timer()
    time_start = time.process_time()
    corpora_size = 0
    number_of_file = 1750
    globaldict = HashTable(KEYS, number_of_file) #collections.defaultdict(list)
    f = open(os.path.join(outputDir, MAPPFILE), 'w') # write to mapping file
    f.write("DOCID \t FREQUENCY")
    for i, file_name in enumerate(list_of_files[:number_of_file]):
        f.write("\n{} \t {}".format(i, os.path.basename(file_name)))
        corpora_size += read_one_file(globaldict, lexer, file_name, i, True)
    f.close()

    # write to dict file
    f = open(os.path.join(outputDir, DICTFILE), 'w') # write to mapping file
    f.write("TERM \t NUMDOC \t START")
    start = 0
    for k, v in globaldict:
        if k == globaldict.empty_str:
            n, s = v
            f.write("\n{}\t{}\t{}".format(k, n, s))
        else:
            num_docs = len(v)
            start += num_docs
            f.write("\n{}\t{}\t{}".format(k, num_docs, start))

    # write to post file
    f = open(os.path.join(outputDir, POSTFILE), 'w')
    f.write("DOCID \t FREQUENCY")
    for k, v in globaldict:
        if k != globaldict.empty_str:
            for doc_id, freq in v:
                f.write("\n{} \t {}".format(doc_id, freq))
    f.close()
    # print(globaldict.hash("commensurate"))
    print('Time run for {} files: {}'.format(number_of_file, time.process_time() - time_start))
    print(corpora_size)
