from invertedfile import (MyLexer,
                          NUM_FILES,
                          KEYS,
                          STOPWORDS,
                          POSTFILE,
                          DICTFILE,
                          MAPPFILE,
                          STEMMER)
from lconstant import *
import sys
import heapq
import os
import time, timeit
import argparse


DFILE_BYTE = LWORD + LTAB + LNUMDOC + LTAB + LSTART + LNEWLINE # word \t numdoc \t start \n
PFILE_BYTE = LDOCID + LTAB + LTFIDF + LNEWLINE # docid \t tfidf \n
MFILE_BYTE = LDOCID + LTAB + LFILENAME + 1 + 4 + LNEWLINE # docid \t filename .html \n
TOPK = 10

class AccumulatorDict():
    def __init__(self, topk, mapping_file):
        self._dict = {}
        self._mapping_file = mapping_file
        self._topk = topk

    def insert(self, key, value):
        if key in self._dict:
            self._dict[key] += value
        else:
            self._dict[key] = value

    def print(self):
        tmp = [(v, k) for k, v in self._dict.items()]
        tmp.sort(reverse=True)
        with open(self._mapping_file, 'r') as file:
            for w, docid  in tmp[:self._topk]:
                file.seek(docid * MFILE_BYTE)
                line = file.read(MFILE_BYTE)
                doc_id, filename = (
                    line[:LDOCID].strip(),
                    line[LDOCID + 1:].strip()
                )
                print('{} {:.4f}'.format(filename, w))
                # print(f"docid: {doc_id}, document name: {filename}, weight: {w}")
        file.close()


def hash(key):
    sum = 0
    for k in key:
        sum = (sum * 19) + ord(k)
    return sum

def query(dict_file, post_file, mapping_file, query_terms, lexer):
    # print(PFILE_BYTE)
    nrows = NUM_FILES * KEYS * 3
    lexer.input(query_terms)
    terms = []
    for i, term in enumerate(lexer):
        tok = term.value
        if len(tok) > 1 and tok not in STOPWORDS:
            tok = STEMMER.stem(tok)
            terms.append(tok)
        else:
            # print("")
            return
        # elif len(tok) == 1:
        #     print(f"Query '{term.value}' only has 1 character. No results.")
        # else:
        #     print(f"Query '{term.value}' is in stopwords list. No results.")
    if len(terms) == 0:
        # print("")
        # print("No query to process, please input query having more than 1 character and not in stopwords list")
        return
    accumulator = AccumulatorDict(TOPK, mapping_file)
    # read files
    with open(dict_file, 'rb') as file:
        for target_word in terms:
            start_line = hash(target_word) % nrows
            current_line = start_line
            start_byte = start_line * DFILE_BYTE
            file.seek(start_byte)

            keep_searching = True
            while keep_searching:
                line = file.read(DFILE_BYTE)
                if not line:
                    # Reached the end of the file, wrap around to the beginning
                    current_line = 0
                    file.seek(0)
                    continue

                words, numdoc, start = (
                    line[:LWORD].decode('utf-8').strip(),
                    line[LWORD + 1: LWORD + 1 + LNUMDOC].decode('utf-8').strip(),
                    line[LWORD + 1 + LNUMDOC + 1:].decode('utf-8').strip()
                )
                numdoc, start = int(numdoc), int(start)
                if target_word[:LWORD] == words:
                    # print(f"Find {target_word} at line {current_line}")
                    with open(post_file, 'rb') as pf:
                        for i in range(numdoc):
                            go_to_line = (start + i) * PFILE_BYTE
                            pf.seek(go_to_line)
                            pline = pf.read(PFILE_BYTE)
                            docid, weight = (
                                pline[:LDOCID].decode('utf-8').strip(),
                                pline[LDOCID + 1:].decode('utf-8').strip() #13
                            )
                            docid, weight = int(docid), float(weight)
                            accumulator.insert(docid, weight)
                    keep_searching = False
                if int(numdoc) == -1: # hit empty row, stop searching
                    # print(f"No document contains {target_word} \n")
                    # print("")
                    keep_searching = False
                else:
                    current_line += 1
                    file.seek(current_line * DFILE_BYTE)
                    if current_line == start_line:
                        # searched all rows, stop searching
                        # print(f"No document contains {target_word} \n")
                        # print("")
                        keep_searching = False
    file.close()
    accumulator.print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Argument list parser")
    parser.add_argument('args', nargs='+', help='List of strings as arguments')
    args = parser.parse_args()
    query_words = args.args

    query_words = ' '.join(query_words)
    lexer = MyLexer()
    output_dir = '/home/quanmai/workspace/courses/AIR/hw3/output'
    dict_path = os.path.join(output_dir, DICTFILE)
    post_path = os.path.join(output_dir, POSTFILE)
    mapp_path = os.path.join(output_dir, MAPPFILE)
    query(dict_path, post_path, mapp_path, query_words, lexer)
