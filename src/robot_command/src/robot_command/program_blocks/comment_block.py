from enum import IntEnum
from parso.python import tree

from .parse_helpers import convert_string, prepare_string
from .rpl_block import RPLBlock, mark_modified


class CommentType(IntEnum):
    LineComment = 0
    BlockComment = 1


class CommentBlock(RPLBlock):
    type = 'comment'

    def __init__(
        self,
        node,
        parent,
        comment_type=CommentType.LineComment,
        text='',
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._comment_type = comment_type
        self._text = text

    @property
    def comment_type(self):
        return self._comment_type

    @comment_type.setter
    @mark_modified()
    def comment_type(self, value):
        self._comment_type = value

    @property
    def text(self):
        return self._text

    @text.setter
    @mark_modified()
    def text(self, value):
        self._text = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt':
            return
        if not (node.children and isinstance(node.children[0], tree.String)):
            return

        string = node.children[0]
        text, is_block = convert_string(string.value)
        type_ = (
            CommentType.BlockComment if is_block else CommentType.LineComment
        )
        yield CommentBlock(node, parent, comment_type=type_, text=text)

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            string = prepare_string(
                self._text, block=self._comment_type == CommentType.BlockComment
            )
            yield f'{self._get_indent()}{string}\n'
