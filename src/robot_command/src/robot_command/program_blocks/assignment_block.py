from parso.python import tree

from .rpl_block import RPLBlock, mark_modified


class AssignmentBlock(RPLBlock):
    type = 'assignment'

    def __init__(
        self, node, parent, name='', operator='=', expression='', **kwargs
    ):
        super().__init__(node, parent, **kwargs)

        self._name = name
        self._operator = operator
        self._expression = expression

    @property
    def name(self):
        return self._name

    @name.setter
    @mark_modified()
    def name(self, value):
        self._name = value

    @property
    def operator(self):
        return self._operator

    @operator.setter
    @mark_modified()
    def operator(self, value):
        self._operator = value

    @property
    def expression(self):
        return self._expression

    @expression.setter
    @mark_modified()
    def expression(self, value):
        self._expression = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt':
            return
        if not (node.children and isinstance(node.children[0], tree.ExprStmt)):
            return

        expr_stmt = node.children[0]
        if len(expr_stmt.children) != 3:
            return
        if expr_stmt.children[0].type != 'name':
            return
        name = expr_stmt.children[0].value
        operator = expr_stmt.children[1].value
        expression = expr_stmt.children[2].get_code().strip()

        yield AssignmentBlock(
            node, parent, name=name, operator=operator, expression=expression
        )

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            yield '{}{} {} {}\n'.format(
                self._get_indent(), self._name, self._operator, self._expression
            )
