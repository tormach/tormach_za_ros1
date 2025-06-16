from enum import IntEnum
from parso.python import tree

from .rpl_block import RPLBlock, mark_modified


class LoopType(IntEnum):
    WhileLoop = 0
    ForRangeLoop = 1


class LoopBlock(RPLBlock):
    type = 'loop'

    def __init__(
        self,
        node,
        parent,
        loop_type=LoopType.WhileLoop,
        condition='',
        variable='',
        count=0,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._loop_type = loop_type
        self._condition = condition
        self._variable = variable
        self._count = count

    @property
    def loop_type(self):
        return self._loop_type

    @loop_type.setter
    @mark_modified()
    def loop_type(self, value):
        self._loop_type = value

    @property
    def condition(self):
        return self._condition

    @condition.setter
    @mark_modified()
    def condition(self, value):
        self._condition = value

    @property
    def variable(self):
        return self._variable

    @variable.setter
    @mark_modified()
    def variable(self, value):
        self._variable = value

    @property
    def count(self):
        return self._count

    @count.setter
    @mark_modified()
    def count(self, value):
        self._count = value

    @staticmethod
    def read(node, parent):
        if isinstance(node, tree.WhileStmt):
            stmt = node.children[1]
            suite = node.children[3]
            yield from LoopBlock._read_while(node, parent, suite, stmt)
        elif isinstance(node, tree.ForStmt):
            name = node.children[1]
            power = node.children[3]
            suite = node.children[5]
            yield from LoopBlock._read_for(node, parent, name, power, suite)

    @staticmethod
    def _read_while(node, parent, suite, stmt):
        block = LoopBlock(
            node,
            parent,
            loop_type=LoopType.WhileLoop,
            condition=stmt.get_code().strip(),
        )
        for node_child in suite.children:
            for child in block.program.read_block(node_child, block):
                block.add_child(child, modify=False)
        yield block

    @staticmethod
    def _read_for(node, parent, name, power, suite):
        if power.type not in ('power', 'atom_expr'):
            return
        if power.children[0].value != 'range':
            return
        count = power.children[1].children[1]
        if count.type != 'number':
            return
        block = LoopBlock(
            node,
            parent,
            loop_type=LoopType.ForRangeLoop,
            variable=str(name.value),
            count=int(count.value),
        )
        for node_child in suite.children:
            for child in block.program.read_block(node_child, block):
                block.add_child(child, modify=False)
        yield block

    def write(self):
        yield from self._write_disabled()

        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
            return

        if self._loop_type == LoopType.WhileLoop:
            yield f'{self._get_indent()}while {self.condition}:\n'
        elif self._loop_type == LoopType.ForRangeLoop:
            yield '{}for {} in range({}):\n'.format(
                self._get_indent(), self.variable, int(self.count)
            )
        for child in self.children:
            yield from child.write()
