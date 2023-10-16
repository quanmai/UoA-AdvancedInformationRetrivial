import ply.lex as lex
import re

# list of TOKENS (required)
tokens =[
    # 'CSS',
    'HTMLTAG',
    'HYPERLINK',
    'EMAIL',
    'NUMBER',
    'HTML_ENTITY',
    'WORD',
]

# def t_CSS(T):
#     r'([\S^,]*,\s*)*\S+\s*{[^}]+}'

def t_HTMLTAG(t):
    # r'<(![^>]+|\/?\w+((\s*[^\s=>])+=(\s*[^\s=>])+)*\s*\/?)>'
    r'<[^>]+>'

def t_HYPERLINK(t):
    r'(htt(p|ps):\/\/|www.)[^\s<\/]+'
    t.value = t.value.lower()
    t.value = re.sub(r'(https://|http://|www|\.)', '', t.value)
    return t

def t_EMAIL(t):
    r'\S+@\S+\.[^<\s,?!.\xa0\x85]+'
    t.value = re.sub('(@.*|<[^>]+>)', '', t.value)
    return t

def t_NUMBER(t):
    r'[1-9](\d|,|\.|-)*'
    t.value = re.sub('(,|-|\.\S*)', '', t.value)
    return t

def t_HTML_ENTITY(t):
    r'\&\w+'

def t_WORD(t):
    r'[A-z](\w|\'|-|\.\w|<[^>]+>)*'
    t.value = t.value.lower()
    t.value = re.sub('(\.|-|\'|<[^>]+>)', '', t.value)
    return t

t_ignore  = ' []+$|=%*{}/0-"#>();:!?.,\t\xa0\x85\xe2\x00'

def t_error(t):
    t.lexer.skip(1)

lexer = lex.lex()

# Test the lexer
html_string = "<b>sgauch</b>@uark.edu www.quanmai.github.io"
lexer.input(html_string)

result = ""
while True:
    token = lexer.token()
    if not token:
        break
    # if token.type == 'EMAIL':
    result += token.value
print(result)
