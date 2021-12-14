from util.ScrapErrors import *
import re
from typing import NamedTuple

class Token(NamedTuple):
    type: str
    value: str
    pos: int

def tokenize(query:str)->'list[Token]':    
    res : list[Token] = []
    token_specification = [
        ('OPEN_PARENTHESIS', r'[(]'),
        ('CLOSE_PARENTHESIS', r'[)]'),
        ('SPACE', r' +'),
        ('LOGIC_OP', r'(?<=[ )])([Aa][Nn][Dd]|[Oo][Rr])(?=[ (])'),        
        ('WORD', r'\w+'),
        ('MISMATCH', r'.')
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    print(tok_regex)
    print(query)
    col = 0
    for mo in re.finditer(tok_regex, query):
        print(mo)
        kind = mo.lastgroup
        value = mo.group()
        col = mo.start()
        if kind == 'OPEN_PARENTHESIS':
            value = '('
        elif kind == 'CLOSE_PARENTHESIS':
            value = ')'
        elif kind == 'SPACE':
            value = ' '
        elif kind == 'LOGIC_OP':
            value = value.upper()
        elif kind == 'WORD':
            pass
        elif kind == 'MISMATCH':
            raise ParseError(value)
        res.append(Token(kind, value, col))
    return res

def check_parenthesis(query : str):
    stack = []
    for char in query:
        if char == '(':
            stack.append(char)
        if char == ')':
            if len(stack) == 0:
                raise ParseParenthesisError(")")
            stack.pop()
    if stack:
        raise ParseParenthesisError("(")                            

def parse_search_query(base : str, query : str,
     p_open : str, p_close : str, space : str , d_quotes : str)-> 'list[str]':
    
    try:
        check_parenthesis(query)
        if base == 'springer' :
            for t in tokenize(query):
                print(t)
            pass
        elif base == 'acm' :
            pass
        elif base == 'ieeex':
            pass
        elif base == 'elsevier':
            pass
        else:
            raise BaseUndefinedError(base)
    except Error as err:
        print(err.message)

    return None
