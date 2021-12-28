
class Error(Exception):
    """ Base class for exceptions """
    def __init__(self, expression : str):
        self.expression = expression
        self.message = "Error: " + expression + " is undefined!"

class BaseUndefinedError(Error):
    def __init__(self, expression : str):
        super().__init__(expression)

class ContentTypeError(Error):
    def __init__(self, expression : str):
        self.expression = expression
        self.message = "Error: " + expression + " is undefined as ContentType!"    

class ContentTypeUndefinedError(Error):
    def __init__(self, expression : str):
        super().__init__(expression)

class ParseParenthesisError(Error):
    def __init__(self, expression : str):
        self.expression = expression
        self.message = "Error: parenthesis " + expression + " unmatched in search string!"    

class ParseError(Error):
    def __init__(self, expression : str):
        self.expression = expression
        self.message = "Error: invalid token \"" + expression + "\" in search string!"    

class   GLCError(ParseError):
    def __init__(self, expression : str):
        super().__init__(expression)

class   GLCEmptyStackError(ParseError):
    def __init__(self, expression : str):
        self.expression = expression
        self.message = "Error: empty token in rule \"" + expression + "\" "    


