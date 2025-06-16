# source: https://github.com/edreamleo/python-to-coffeescript/blob/master/py2cs.py
import ast
import token as token_module
import types


def u(s):
    # pylint: disable = undefined-variable
    return unicode(s)


def ue(s, encoding):
    # pylint: disable = undefined-variable
    return unicode(s, encoding)


def split_lines(s):
    """Split s into lines, preserving trailing newlines."""
    return s.splitlines(True) if s else []


def is_unicode(s):
    '''Return True if s is a unicode string.'''
    # pylint: disable=no-member
    return isinstance(s, types.UnicodeType)


def is_string(self, s):
    """Return True if s is any string, but not bytes."""
    # pylint: disable=no-member
    return isinstance(s, types.StringTypes)


def to_unicode(s, encoding='utf-8', report_errors=False):
    """Convert a non-unicode string with the given encoding to unicode."""
    trace = False
    if is_unicode(s):
        return s
    if not encoding:
        encoding = 'utf-8'
    # These are the only significant calls to s.decode in Leo.
    # Tracing these calls directly yields thousands of calls.
    # Never call g.trace here!
    try:
        s = s.decode(encoding, 'strict')
    except UnicodeError:
        s = s.decode(encoding, 'replace')
        if trace or report_errors:
            g.trace(g.callers())
            print(
                "to_unicode: Error converting %s... from %s encoding to unicode"
                % (s[:200], encoding)
            )
    except AttributeError:
        if trace:
            print('to_unicode: AttributeError!: %s' % s)
        # May be a QString.
        s = u(s)
    if trace and encoding == 'cp1252':
        print('to_unicode: returns %s' % s)
    return s


class ReadLinesClass:
    """A class whose next method provides a readline method for Python's tokenize module."""

    def __init__(self, s):
        self.lines = s.splitlines(True) if s else []
        # g.splitLines(s)
        self.i = 0

    def next(self):
        if self.i < len(self.lines):
            line = self.lines[self.i]
            self.i += 1
        else:
            line = ''
        # g.trace(repr(line))
        return line

    __next__ = next


class TokenSync:
    """A class to sync and remember tokens."""

    # To do: handle comments, line breaks...

    def __init__(self, s, tokens):
        """Ctor for TokenSync class."""
        assert isinstance(tokens, list)  # Not a generator.
        self.s = s
        self.first_leading_line = None
        self.lines = [z.rstrip() for z in split_lines(s)]
        # Order is important from here on...
        self.nl_token = self.make_nl_token()
        self.line_tokens = self.make_line_tokens(tokens)
        self.blank_lines = self.make_blank_lines()
        self.string_tokens = self.make_string_tokens()
        self.ignored_lines = self.make_ignored_lines()

    def make_blank_lines(self):
        """Return of list of line numbers of blank lines."""
        result = []
        for i, aList in enumerate(self.line_tokens):
            # if any([self.token_kind(z) == 'nl' for z in aList]):
            if len(aList) == 1 and self.token_kind(aList[0]) == 'nl':
                result.append(i)
        return result

    def make_ignored_lines(self):
        """
        Return a copy of line_tokens containing ignored lines,
        that is, full-line comments or blank lines.
        These are the lines returned by leading_lines().
        """
        result = []
        for i, aList in enumerate(self.line_tokens):
            for z in aList:
                if self.is_line_comment(z):
                    result.append(z)
                    break
            else:
                if i in self.blank_lines:
                    result.append(self.nl_token)
                else:
                    result.append(None)
        assert len(result) == len(self.line_tokens)
        for i, aList in enumerate(result):
            if aList:
                self.first_leading_line = i
                break
        else:
            self.first_leading_line = len(result)
        return result

    def make_line_tokens(self, tokens):
        """
        Return a list of lists of tokens for each list in self.lines.
        The strings in self.lines may end in a backslash, so care is needed.
        """
        trace = False
        n, result = len(self.lines), []
        for i in range(0, n + 1):
            result.append([])
        for token in tokens:
            t1, t2, t3, t4, t5 = token
            kind = token_module.tok_name[t1].lower()
            srow, scol = t3
            erow, ecol = t4
            line = erow - 1 if kind == 'string' else srow - 1
            result[line].append(token)
            if trace:
                g.trace(f'{line:>3} {self.dump_token(token)}')
        assert len(self.lines) + 1 == len(result), len(result)
        return result

    @staticmethod
    def make_nl_token():
        """Return a newline token with '\n' as both val and raw_val."""
        t1 = token_module.NEWLINE
        t2 = '\n'
        t3 = (0, 0)  # Not used.
        t4 = (0, 0)  # Not used.
        t5 = '\n'
        return t1, t2, t3, t4, t5

    def make_string_tokens(self):
        """Return a copy of line_tokens containing only string tokens."""
        result = []
        for aList in self.line_tokens:
            result.append([z for z in aList if self.token_kind(z) == 'string'])
        assert len(result) == len(self.line_tokens)
        return result

    def check_strings(self):
        """Check that all strings have been consumed."""
        for i, aList in enumerate(self.string_tokens):
            if aList:
                g.trace('warning: line %s. unused strings' % i)
                for z in aList:
                    print(self.dump_token(z))

    @staticmethod
    def dump_token(token, verbose=False):
        """Dump the token. It is either a string or a 5-tuple."""
        if is_string(token):
            return token
        else:
            t1, t2, t3, t4, t5 = token
            kind = to_unicode(token_module.tok_name[t1].lower())
            raw_val = to_unicode(t5)
            val = to_unicode(t2)
            if verbose:
                return f'token: {kind:>10} {val!r}'
            else:
                return val

    @staticmethod
    def is_line_comment(token):
        """Return True if the token represents a full-line comment."""
        t1, t2, t3, t4, t5 = token
        kind = token_module.tok_name[t1].lower()
        raw_val = t5
        return kind == 'comment' and raw_val.lstrip().startswith('#')

    @staticmethod
    def join(a_list, sep=','):
        """return the items of the list joined by sep string."""
        tokens = []
        for i, token in enumerate(a_list or []):
            tokens.append(token)
            if i < len(a_list) - 1:
                tokens.append(sep)
        return tokens

    def last_node(self, node):
        """Return the node of node's tree with the largest lineno field."""

        class LineWalker(ast.NodeVisitor):
            def __init__(self):
                """Ctor for LineWalker class."""
                self.node = None
                self.lineno = -1

            def visit(self, node_):
                """LineWalker.visit."""
                if hasattr(node_, 'lineno'):
                    if node_.lineno > self.lineno:
                        self.lineno = node_.lineno
                        self.node = node_
                if isinstance(node_, list):
                    for z in node_:
                        self.visit(z)
                else:
                    self.generic_visit(node_)

        w = LineWalker()
        w.visit(node)
        return w.node

    def leading_lines(self, node):
        """Return a list of the preceding comment and blank lines"""
        # This can be called on arbitrary nodes.
        trace = False
        leading = []
        if hasattr(node, 'lineno'):
            i, n = self.first_leading_line, node.lineno
            while i < n:
                token = self.ignored_lines[i]
                if token:
                    s = self.token_raw_val(token).rstrip() + '\n'
                    leading.append(s)
                    if trace:
                        g.trace(f'{i:>11}: {s.rstrip()}')
                i += 1
            self.first_leading_line = i
        return leading

    def leading_string(self, node):
        """Return a string containing all lines preceding node."""
        return ''.join(self.leading_lines(node))

    def line_at(self, node, continued_lines=True):
        """Return the lines at the node, possibly including continuation lines."""
        n = getattr(node, 'lineno', None)
        if n is None:
            return '<no line> for %s' % node.__class__.__name__
        elif continued_lines:
            a_list, n = [], n - 1
            while n < len(self.lines):
                s = self.lines[n]
                if s.endswith('\\'):
                    a_list.append(s[:-1])
                    n += 1
                else:
                    a_list.append(s)
                    break
            return ''.join(a_list)
        else:
            return self.lines[n - 1]

    def sync_string(self, node):
        """Return the spelling of the string at the given node."""
        # g.trace('%-10s %2s: %s' % (' ', node.lineno, self.line_at(node)))
        n = node.lineno
        tokens = self.string_tokens[n - 1]
        if tokens:
            token = tokens.pop(0)
            self.string_tokens[n - 1] = tokens
            return self.token_val(token)
        else:
            g.trace('===== underflow line:', n, node.s)
            return node.s

    @staticmethod
    def token_kind(token):
        """Return the token's type."""
        t1, t2, t3, t4, t5 = token
        return to_unicode(token_module.tok_name[t1].lower())

    @staticmethod
    def token_raw_val(token):
        """Return the value of the token."""
        t1, t2, t3, t4, t5 = token
        return to_unicode(t5)

    @staticmethod
    def token_val(token):
        """Return the raw value of the token."""
        t1, t2, t3, t4, t5 = token
        return to_unicode(t2)

    def tokens_for_statement(self, node):
        assert isinstance(node, ast.AST), node
        name = node.__class__.__name__
        if hasattr(node, 'lineno'):
            tokens = self.line_tokens[node.lineno - 1]
            g.trace(' '.join(self.dump_token(z) for z in tokens))
        else:
            g.trace('no lineno', name)

    def trailing_comment(self, node):
        """
        Return a string containing the trailing comment for the node, if any.
        The string always ends with a newline.
        """
        if hasattr(node, 'lineno'):
            return self.trailing_comment_at_lineno(node.lineno)
        else:
            # g.trace('no lineno', node.__class__.__name__, g.callers())
            return '\n'

    def trailing_comment_at_lineno(self, lineno):
        """Return any trailing comment at the given node.lineno."""
        trace = False
        tokens = self.line_tokens[lineno - 1]
        for token in tokens:
            if self.token_kind(token) == 'comment':
                raw_val = self.token_raw_val(token).rstrip()
                if not raw_val.strip().startswith('#'):
                    val = self.token_val(token).rstrip()
                    s = ' %s\n' % val
                    if trace:
                        g.trace(lineno, s.rstrip(), g.callers())
                    return s
        return '\n'

    def trailing_lines(self):
        """return any remaining ignored lines."""
        trace = False
        trailing = []
        i = self.first_leading_line
        while i < len(self.ignored_lines):
            token = self.ignored_lines[i]
            if token:
                s = self.token_raw_val(token).rstrip() + '\n'
                trailing.append(s)
                if trace:
                    g.trace(f'{i:>11}: {s.rstrip()}')
            i += 1
        self.first_leading_line = i
        return trailing
