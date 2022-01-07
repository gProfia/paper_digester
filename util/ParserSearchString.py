from util.ScrapErrors import *
import re
from typing import NamedTuple

class Token(NamedTuple):
    type: str
    value: str
    pos: int

class NodeT(NamedTuple):
    rule : str
    t : Token 
    children : 'list[NodeT]'

def print_tree(n : 'NodeT') -> None:

    q : 'list[list]'=[[n]]
    def traversal(node : 'NodeT', depth : int):
        if (len(q) - 1) < depth:
            q.append([])            
        for n in node.children:
            q[depth].append(n)
            traversal(n, depth + 1)

    traversal(n, 1)

    for f in q:
        for nx in f:
            if nx.rule != '':
                print(nx.rule, end='\t')
            else:
                print(('W' if nx.t.type == 'WORD' else ('S' if nx.t.type == 'SPACE' else ('(' if nx.t.type == 'OPEN_PARENTHESIS' else ( ')' if nx.t.type == 'CLOSE_PARENTHESIS' else 'l')))), end='\t')
        print('')

def tokenize(query:str)->'list[Token]':    
    res : list[Token] = []
    token_specification = [
        ('OPEN_PARENTHESIS', r'[(]'),
        ('CLOSE_PARENTHESIS', r'[)]'),
        ('SPACE', r' +'),
        ('LOGIC_OP', r'(?<=[ )])([Aa][Nn][Dd]|[Oo][Rr])(?=[ (])'),        
        ('WORD', r'\w+[-]?(\w+)?'),
        ('MISMATCH', r'.')
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

    col = 0
    for mo in re.finditer(tok_regex, query):
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
    
def GLC(tokens : 'list[Token]') -> 'NodeT':

    def U(stack : 'list[NodeT]') -> 'NodeT':
        inner_stack : 'list[NodeT]' = []
        if len(stack) > 0:
            if stack[len(stack) - 1].t.type == 'WORD':
                inner_stack.append(stack.pop())
                if len(stack) > 0:
                    if stack[len(stack) - 1].t.type == 'SPACE':
                        inner_stack.append(stack.pop())
                        if not len(stack) > 0:
                                raise GLCEmptyStackError("U->ws?")                    
                        elif stack[len(stack) - 1].t.type == 'WORD':                            
                            inner_stack.append(U(stack))
                            return NodeT(rule = 'U', t = None, children=inner_stack)                            
                        else:                                  
                            raise GLCError(stack[len(stack) - 1].t.type + " at col " + str(stack[len(stack) - 1].t.pos) +" U->ws?")                                            
                    else:
                        return NodeT(rule = 'U', t = None, children=inner_stack)                            
                else:
                    return NodeT(rule = 'U', t = None, children=inner_stack)
            else:                      
                raise GLCError(stack[len(stack) - 1].t.type + " at col " + str(stack[len(stack) - 1].t.pos) +" U->?")                                                                
        else:
            raise GLCEmptyStackError("U")     

    def F(stack : 'list[NodeT]') -> 'NodeT':
        inner_stack : 'list[NodeT]' = []
        if len(stack) > 0:
            if stack[len(stack) - 1].t.type == 'OPEN_PARENTHESIS':
                inner_stack.append(stack.pop())
                if len(stack) > 0:
                    inner_stack.append(S(stack))
                else:
                    raise GLCEmptyStackError("F->(?")     
                if len(stack) > 0:
                    if stack[len(stack) - 1].t.type == 'CLOSE_PARENTHESIS':
                        inner_stack.append(stack.pop())
                        return NodeT(rule = 'F', t = None, children=inner_stack)
                    else:                              
                        raise GLCError(stack[len(stack) - 1].t.type + " at col " + str(stack[len(stack) - 1].t.pos) +" F->(S?")                                
                else:
                    raise GLCEmptyStackError("F->(S?")     
        else:
            raise GLCEmptyStackError("F")   

    def S(stack : 'list[NodeT]') -> 'NodeT':
        inner_stack : 'list[NodeT]' = []
        if len(stack) > 0:
            
            if stack[len(stack) - 1].t.type == 'WORD':
                inner_stack.append(U(stack))
                if len(stack) > 0:
                    if stack[len(stack) - 1].t.type == 'LOGIC_OP':                            
                            inner_stack.append(stack.pop())
                            if len(stack) > 0:
                                inner_stack.append(S(stack))
                                #->UlS
                                return NodeT(rule = 'S', t = None, children=inner_stack)
                            else:
                                raise GLCEmptyStackError("S->Ul?")                    
                    else:
                        #->U
                        return NodeT(rule = 'S', t = None, children=inner_stack)
                else:
                    #->U
                    return NodeT(rule = 'S', t = None, children=inner_stack)
            
            elif stack[len(stack) - 1].t.type == 'OPEN_PARENTHESIS':
                inner_stack.append(F(stack))
                if len(stack) > 0:
                    if stack[len(stack) - 1].t.type == 'LOGIC_OP':
                            inner_stack.append(stack.pop())
                            if len(stack) > 0:
                                inner_stack.append(S(stack))
                                #->FlS
                                return NodeT(rule = 'S', t = None, children=inner_stack)
                            else:
                                raise GLCEmptyStackError("S->Fl?")                    
                    else:
                        #->F
                       return NodeT(rule = 'S', t = None, children=inner_stack)
                else:
                    #->F
                    return NodeT(rule = 'S', t = None, children=inner_stack)                
            else:
                raise GLCError(stack[len(stack) - 1].t.type + " at col " + str(stack[len(stack) - 1].t.pos) +" S->?")                        
        else:
            raise GLCEmptyStackError("S")

    def clean_unused_spaces(stack : 'list[Token]') -> 'list[Token]':
        st = stack.copy()
        st_out : 'list[Token]' =[]
        i : int = 0
        while i < len(st):
            if st[i].type == 'WORD':
                flag_inner_loop : bool = False
                while i < len(st) and st[i].type == 'WORD':
                    st_out.append(st[i])
                    i = i + 1
                    if i < len(st) and st[i].type == 'SPACE':
                        if (i+1) < len(st) and st[i + 1].type == 'WORD':
                            st_out.append(st[i])
                            i = i + 1
                            continue
                        else:
                            flag_inner_loop = True
                            break
                if flag_inner_loop:
                    i = i + 1
                    continue    
                
            elif st[i].type == 'SPACE':
                i = i + 1
                continue
            else:
                st_out.append(st[i])
                i = i + 1
        return st_out
    
    sc_tokens : 'list[Token]' = clean_unused_spaces(tokens)
    stack : 'list[NodeT]' = [NodeT(rule='', t=t, children=[]) for  t in sc_tokens.copy()]
    stack.reverse()

    root : 'NodeT' = S(stack)
    #print(root)
    #print_tree(root)
    return root

def change_chars(t : 'list[Token]', p_open : str, p_close : str, space : str , d_quotes : str) -> str:
    result : str = ''    
    for token in t:
        if token.type == 'WORD':
            result = result + token.value
        elif token.type == 'LOGIC_OP':
            result = result + token.value.upper()
        elif token.type == 'OPEN_PARENTHESIS':
            result = result + p_open
        elif token.type == 'CLOSE_PARENTHESIS':            
            result = result + p_close
        elif token.type == 'SPACE':  
            result = result + space                      
        else:
            raise ParseError(token.type)
    return result

def parse_search_query(base : str, query : str,
     p_open : str, p_close : str, space : str , d_quotes : str)-> 'list[str]': #para elsevier = lista, para outros = lista c 1 unidade
    
    try:
        if base == 'springer' :
            #validate query
            t : 'list[Token]' = tokenize(query)
            GLC(t)
            r_query : str =  change_chars(t, p_open, p_close, space, d_quotes)
            return [r_query]
        elif base == 'acm' :
            t : 'list[Token]' = tokenize(query)
            GLC(t)
            r_query : str =  change_chars(t, p_open, p_close, space, d_quotes)
            return [r_query]            
        elif base == 'ieeex':
            pass
        elif base == 'elsevier':
            pass
        else:
            raise BaseUndefinedError(base)
    except Error as err:        
        print(err.message)
    print("wtf")
    return None
