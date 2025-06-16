import copy
import itertools

from uuid import uuid4

INDENTATION_SPACES = 4


class mark_modified:
    """Helper decorator for modified command logic."""

    def __init__(self):
        pass

    def __call__(self, f):
        def wrapped_f(obj, *args, **kwargs):
            f(obj, *args, **kwargs)
            obj._modified = True

        return wrapped_f


class RPLBlock:
    """
    Represents a block in a robot program. A block is not necessarily the same
    as a node in the Python AST, but can be something more complex such as a
    movement command for example.
    """

    type = ''

    def __init__(
        self, node, parent, program=None, type_='', uuid=None, modified=False
    ):
        """
        :type program: robot_command.RobotProgram
        :type node: Optional[parso.python.tree.PythonNode]
        :type parent: Optional[RPLBlock]
        """
        self.program = program or parent.program
        if type_:  # overwrite type only when necessary
            self.type = type_
        self._modified = modified
        self.children = []
        self.node = node
        self.parent = parent
        self.uuid = uuid or str(uuid4())

        self._disabled = False

        self.group_links = []
        self.group_target = None
        self.group_fixed = False  # marks block as not movable, e.g. else

    @property
    def disabled(self):
        return self._disabled or bool(self.parent and self.parent.disabled)

    @disabled.setter
    @mark_modified()
    def disabled(self, value):
        self._disabled = value

    @property
    def level(self):
        return (self.parent.level + 1) if self.parent else 0

    @property
    def code(self):
        return self.node.get_code() if self.node else ''

    @property
    def modified(self):
        return self._modified

    @staticmethod
    def read(node, parent):
        """
        Try to read a Python node and convert it to a RPL block.

        :rtype: Optional[RPLBlock]
        :type parent: RPLBlock
        :type node: PythonNode
        """
        raise NotImplementedError()

    def _write_disabled(self):
        if self._disabled and (
            not self.in_group or self is self.group_head
        ):  # only write when group head
            yield f'{self._get_indent(add=-1)}if False:\n'

    def _needs_rewrite(self):
        return any(
            n.modified
            for n in itertools.chain(
                RPLBlockWalker(self), RPLBlockRootWalker(self)
            )
        )

    def write(self):
        """
        Yields generated code for this block and every child, line by line.
        :rtype: Generator[str]
        """
        yield self.node.get_code() if self.node else ''

    def add_child(self, block, modify=True):
        self.children.append(block)
        block.parent = self
        if modify:
            self._modified = True
        return block

    def remove_child(self, block, modify=True):
        index = self.children.index(block)
        del self.children[index]
        if modify:
            self._modified = True

    def take_child(self, block, modify=True):
        index = self.children.index(block)
        if modify:
            self._modified = True
        return self.children.pop(index)

    def insert_child(self, block, target_block, modify=True, before=True):
        index = self.children.index(target_block)
        if not before:
            index += 1
        self.children.insert(index, block)
        block.parent = self
        if modify:
            self._modified = True
            block._modified = True

    def add_to_group(self, block):
        self.group_links.append(block)
        block.group_target = self

    def insert_into_group(self, block, target, before):
        if block in self.group_links:
            self.group_links.remove(block)
        if target is not self:
            index = self.group_links.index(target)
            if not before:
                index += 1
        else:
            index = 0
        self.group_links.insert(index, block)
        block.group_target = self

    def remove_from_group(self, block):
        if block not in self.group_links:
            return
        self.group_links.remove(block)
        block.group_target = None

    @property
    def group_head(self):
        if self.in_group:
            return self.group_target or self
        else:
            return None

    @property
    def group_tail(self):
        if self.in_group:
            if self.group_target:
                return self.group_target.group_links[-1]
            else:
                return self.group_links[-1]
        else:
            return None

    @property
    def in_group(self):
        return self.group_links or self.group_target is not None

    def copy(self):
        new_block = copy.copy(self)

        children, new_block.children = new_block.children, []
        for child in children:
            new_block.add_child(child.copy())

        return new_block

    def _get_indent(self, add=0):
        total_disabled = sum(
            int(
                block._disabled
                or bool(block.group_head and block.group_head.disabled)
            )
            for block in RPLBlockRootWalker(self)
        )
        return (
            ' ' * INDENTATION_SPACES * (self.level - 1 + total_disabled + add)
        )

    def _get_next_indent(self):
        return self._get_indent() + INDENTATION_SPACES * ' '

    def __str__(self):
        return f'RPLBlock <{self.type}>'

    def __deepcopy__(self, memo):
        deepcopy_method = self.__deepcopy__
        self.__deepcopy__ = None
        memo[id(self.program)] = self.program  # prevent deepcopy of program
        cp = copy.deepcopy(self, memo)
        self.__deepcopy__ = deepcopy_method
        cp.__deepcopy__ = deepcopy_method
        return cp


class RPLBlockWalker:
    """
    The walker performs a breath first search on the given block. The behavior
    can be changed by supplying the optional dfs parameter to depth first search.
    """

    def __init__(self, block, dfs=False):
        self.block = block
        self.dfs = dfs

    @staticmethod
    def _walk(block, dfs):
        if not block:
            return
        if not dfs:
            yield block
        for child in block.children:
            yield from RPLBlockWalker._walk(child, dfs)
        if dfs:
            yield block

    def __iter__(self):
        return RPLBlockWalker._walk(self.block, self.dfs)


class RPLBlockRootWalker:
    """
    The walker iterates over the root of a tree starting from the given block.
    The iterator starts from the innermost block and goes up to the trees root block.
    """

    def __init__(self, block):
        self.block = block

    @staticmethod
    def _walk(block):
        if not block:
            return
        yield block
        yield from RPLBlockRootWalker._walk(block.parent)

    def __iter__(self):
        return RPLBlockRootWalker._walk(self.block)


class RPLBlockScopeWalker:
    """
    The walker iterates over all scopes of the given block.
    The iterator starts from the innermost scope and goes up the parent scopes.
    """

    def __init__(self, block, reverse=False):
        self.block = block
        self.reversed = reverse

    @staticmethod
    def _walk(block, ref, reverse):
        if not block:
            yield ref
            return

        children = []
        for child in block.children:
            children.append(child)
            if child is ref:
                break
        if reverse:
            children = reversed(children)
        yield from children
        yield from RPLBlockScopeWalker._walk(block.parent, block, reverse)

    def __iter__(self):
        return RPLBlockScopeWalker._walk(
            self.block.parent, self.block, self.reversed
        )
