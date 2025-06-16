from parso.python import tree

from .rpl_block import RPLBlock, mark_modified


class IfBlock(RPLBlock):
    type = 'if'

    def __init__(self, node, parent, condition='', type_='if', **kwargs):
        super().__init__(node, parent, **kwargs)

        self._condition = condition
        self.type = type_

    @property
    def condition(self):
        return self._condition

    @condition.setter
    @mark_modified()
    def condition(self, value):
        self._condition = value

    @property
    def has_else(self):
        if self.type == 'else':
            return True
        head = self.group_head
        return any(block.type == 'else' for block in head.group_links)

    @staticmethod
    def read(node, parent):
        if not isinstance(node, tree.IfStmt):
            return

        head = None
        for i, c in enumerate(node.children):
            if_node = None
            if c in ('if', 'elif'):
                if_node = IfBlock._read_if(
                    node=node,
                    stmt=node.children[i + 1],
                    suite=node.children[i + 3],
                    parent=parent,
                    type_=str(c.value),
                )
            elif c == 'else':
                if_node = IfBlock._read_if(
                    node=node,
                    suite=node.children[i + 2],
                    parent=parent,
                    type_=str(c.value),
                )
                if_node.group_fixed = True

            if if_node:
                if not head:
                    head = if_node
                else:
                    head.add_to_group(if_node)
                yield if_node

    @staticmethod
    def _read_if(node, suite, parent, type_, stmt=None):
        block = IfBlock(
            node,
            parent,
            type_=type_,
            condition=stmt.get_code().strip() if type_ != 'else' else '',
        )
        for node_child in suite.children:
            for child in block.program.read_block(node_child, block):
                block.add_child(child, modify=False)
        return block

    def write(self):
        yield from self._write_disabled()
        if self.type in ('if', 'elif'):
            yield '{}{} {}:\n'.format(
                self._get_indent(), self.type, self.condition
            )
        else:
            yield f'{self._get_indent()}else:\n'
        for child in self.children:
            yield from child.write()
