import ast
import tokenize
from tokensync import ReadLinesClass, TokenSync


class ReadProgramVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()


class ReadProgramTraverser:
    """Convert Python programs to internal model representation."""

    def __init__(self):
        # Redirection. Set in format.
        self.sync = None
        self.level = 0
        self.sync_string = None
        self.last_node = None
        self.leading_lines = None
        self.leading_string = None
        self.tokens_for_statement = None
        self.trailing_comment = None
        self.trailing_comment_at_lineno = None

    def read(self, node, code, tokens):
        """read the node (or list of nodes) and its descendants"""
        # Create aliases here for convenience.
        self.sync = sync = TokenSync(code, tokens)
        self.level = 0
        self.sync_string = sync.sync_string
        self.last_node = sync.last_node
        self.leading_lines = sync.leading_lines
        self.leading_string = sync.leading_string
        self.tokens_for_statement = sync.tokens_for_statement
        self.trailing_comment = sync.trailing_comment
        self.trailing_comment_at_lineno = sync.trailing_comment_at_lineno
        # Compute the result.
        val = self.visit(node)
        sync.check_strings()
        # if isinstance(val, list): # testing:
        # val = ' '.join(val)
        val += ''.join(sync.trailing_lines())
        return val or ''

    def visit(self, node):
        """Return the formatted version of an AST node, or list of AST nodes."""


# readlines = ReadLinesClass(self._source_code).next
# tokens = list(tokenize.generate_tokens(readlines))
# node = ast.parse(self._source_code, filename=path, mode='exec')
