from parso.python import tree

from .rpl_block import RPLBlock


class DisabledBlock(RPLBlock):
    type = 'disabled'

    def __init__(self, node, parent, **kwargs):
        super().__init__(node, parent, **kwargs)

    @staticmethod
    def read(node, parent):
        if not isinstance(node, tree.IfStmt):
            return

        if len(node.children) > 4:
            return

        for i, c in enumerate(node.children):
            if c != 'if':
                return
            blocks = DisabledBlock._read_if(
                stmt=node.children[i + 1],
                suite=node.children[i + 3],
                parent=parent,
            )
            yield from blocks

    @staticmethod
    def _read_if(suite, parent, stmt=None):
        condition = stmt.get_code().strip()
        if condition != 'False':
            return

        children = []
        for node_child in suite.children:
            for child in parent.program.read_block(node_child, parent):
                child._disabled = True
                children.append(child)

        if len(children) == 1 or all(child.group_head for child in children):
            yield from children
