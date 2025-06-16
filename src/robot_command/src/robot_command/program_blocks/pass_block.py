from parso.python import tree

from .rpl_block import RPLBlock


class PassBlock(RPLBlock):
    type = 'pass'

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt':
            return
        if not (
            any(node.children) and isinstance(node.children[0], tree.Keyword)
        ):
            return

        expr_stmt = node.children[0]
        if expr_stmt.value != 'pass':
            return

        yield PassBlock(node, parent)

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            yield f'{self._get_indent()}pass\n'
