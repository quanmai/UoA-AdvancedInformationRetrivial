#----------------------------------------
# Filename:  extract_tokens.py
# To run:    python3 extract_tokens.py <infile>
# e.g:       python3 extract_tokens.py input.txt > output.txt
#----------------------------------------

import os.path
import ply.lex as lex
import sys
import glob
import collections
from ply.lex import TOKEN
from timeit import default_timer
import subprocess

# list of TOKENS (required)
tokens =[
    'EMAIL',
    'URL',
    'HTML',
    'PHD',
    'PHONE_NUMBER',
    'WHITESPACE',
    'DOWNCASE',
    'REMOVE_COMMENT',
    'REMOVE_HTML_TAG',
    'COLOR',
    'PIXEL',
    'NUMBER',
    'NUMBER2',
    'CHAR_NUM',
]
DIGITS  = r'[0-9]+'
# # Regular expression for the HTML special characters
# t_HTML = r'&lt;|&gt;'

def MyLexer():
    # Special case 
    def t_PHD(t):
        r'Ph\.D\.'
        t.value = 'phd'
        return t
    
    # Email
    def t_EMAIL(t):
        r'\S+@\S+'
        t.value = 'zzzemail'
        return t
    
    # URL
    def t_URL(t):
        r'(?:(?:https?://|www\.)\S+|\b\w+\.\w+\b)'
        t.value = 'zzzurl'
        return t
    
    # Handle the HTML special characters
    def t_HTML(t):
        r'&lt;|&gt;'
        if t.value == '&lt;':
            t.value = 'zzzlessthan'
        elif t.value == '&gt;':
            t.value = 'zzzgreaterthan'
        return t
    
    # Match phone number (e.g., 123-456-7890)
    # an replace the matched phone number with 'zzzphonenumber'
    def t_PHONE_NUMBER(t):
        r'\d{3}-\d{3}-\d{4}'  
        t.value = 'zzzphonenumber'  
        return t
    
    # Match number formatted as 1,000,000 to 'zzznumber'
    def t_NUMBER2(t):
        r'\d+[,\d+]+'
        t.value = "zzznumber"
        return t
    
    # Match number to 'zzznumber'
    # Must be defined after rules that also contains digits
    @TOKEN(DIGITS)
    def t_NUMBER(t):
        t.value = "zzznumber"
        return t

    # Regular expression rule to match and discard /* ... */ comments
    def t_REMOVE_COMMENT(t):
        r'/\*.*?\*/'
        pass

    # This rule captures and discards anything enclosed in angle brackets
    # i.e. remove content in HTML tags
    def t_REMOVE_HTML_TAG(t):
        r'<[^>]+>'
        pass
    
    # Replace [digits]px to 'zzzpixel' 
    def t_PIXEL(t):
        r'\d+px'
        t.value = 'zzzpixel'
        return t
    
    # Downcase
    def t_DOWNCASE(t):
        r'[A-Za-z]+'
        t.value = t.value.lower()
        return t
    
    # Match remaining strings that contain both characters and digits to 'zzzcharnum'
    # Must define after t_PIXEL()
    def t_CHAR_NUM(t):
        r'[a-zA-Z0-9]+'
        t.value = 'zzzcharnum'
        return t
    
    # Replace color code (e.g. #333, #FFF)to 'zzzcolor'
    def t_COLOR(t):
        r'\#[0-9A-Za-z]+'
        t.value = 'zzzcolor'
        return t
    
    # Regular expression rule to match and discard whitespace characters
    def t_WHITESPACE(t):
        r'\n\t\s+ '
        pass
    
    def t_error(t):
        t.lexer.skip(1)

    # Ignore whitespace
    # t_ignore = ''

    return lex.lex()

# global_dict: list((doc_id, rfreq))
def read_one_file(global_dict: dict, lexer: callable, 
                  file_name: str, doc_id: int, raw_freq: bool = True):
    dict = collections.defaultdict(list)
    num_tokens = 0
    with open(file_name, 'r') as rf:
        # print("Process file: ", file_name)
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
        global_dict[k].append((doc_id, freq))
    del(dict) 
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
    POSTFILE = "post_file.txt"
    DICTFILE = "dict_file.txt"
    MAPPFILE = "mapping_file.txt"

    lexer = MyLexer()
    inputDir = sys.argv[1]
    outputDir = sys.argv[2]
    if not os.path.exists(inputDir) or not os.path.exists(outputDir):
        print("Path not valid \n Enter valid path ")
        quit()

    # to ensure files are ordered by name   
    sort_files_command = f"ls {inputDir} | cut -d. -f1 | sort -V"
    result = subprocess.run(sort_files_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        sorted_files = result.stdout.split('\n')
        # sorted_files = [file for file in sorted_files if file.strip()]
    else:
        print("Error:", result.stderr)
    list_of_files = [os.path.join(inputDir, file + ".html") for file in sorted_files if file.strip()]
    ###

    globaldict = collections.defaultdict(list)
    corpora_size = 0
    number_of_file = 1750
    start = default_timer()
    f = open(os.path.join(outputDir, MAPPFILE), 'w') # write to mapping file
    f.write("DOCID \t FREQUENCY")
    for i, file_name in enumerate(list_of_files[:number_of_file]):
        f.write("\n{} \t {}".format(i, os.path.basename(file_name)))
        corpora_size += read_one_file(globaldict, lexer, file_name, i, True)
    f.close()

    # write to dict file
    f = open(os.path.join(outputDir, DICTFILE), 'w') # write to mapping file
    f.write("TERM \t NUMDOC \t START")
    output_dict = collections.defaultdict(tuple)
    start = 0
    for k, v in globaldict.items():
        num_docs = len(globaldict[k])
        start += num_docs
        output_dict[k] = (num_docs, start)
        f.write("\n{}\t{}\t{}".format(k, num_docs, start))
    print(globaldict.get("function"))
    my_list = list(globaldict.keys())
    print(my_list[0])
    # write to post file
    f = open(os.path.join(outputDir, POSTFILE), 'w')
    f.write("DOCID \t FREQUENCY")
    for v in globaldict.values():
        for doc_id, freq in v:
            f.write("\n{} \t {}".format(doc_id, freq))
    f.close()
    print('Time run for {} files: {}'.format(number_of_file, default_timer() - start))
