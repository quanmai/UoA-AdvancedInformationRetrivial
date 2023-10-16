import ply.lex as lex
import re

# Define the list of tokens (URLs in this case)
tokens = ['CSS',
          'HTMLENTITY',
          'HTMLTAG',
          'HTMLCOMMENT',
          'HYPERLINK',
          'NUMBER',
          'EMAIL',
          'WORD']

def t_CSS(t):
    r'([\S^,]*,\s*)*\S+\s*{[^}]+}'

# Remove html special tokens, such as &gt; &amp;
def t_HTMLENTITY(t):
    r'\&\w+'

def t_HTMLTAG(t):
    r'<[^>]+>'

def t_HTMLCOMMENT(t):
    r'/\*.*?\*/'
    # r'/\*.*?\*/|<!--.*?-->'

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

# Error handling rule
def t_error(t):
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Test the lexer
input_text = """20 20.07 30332-0829"""
lexer.input(input_text)

for token in lexer:
    print(token.value)
