from enum import IntEnum
from robot_command.program_blocks.parse_helpers import (
    FunctionParser,
    Argument,
    prepare_string,
)
from .rpl_block import RPLBlock, mark_modified


class NotifyType(IntEnum):
    Notification = 0
    Warning = 1
    Error = 2
    UserInput = 3


class NotifyBlock(RPLBlock):
    type = 'notify'

    def __init__(
        self,
        node,
        parent,
        message='',
        image_path='',
        notify_type=NotifyType.Notification,
        timeout=None,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)

        self._notify_type = notify_type
        self._message = message
        self._image_path = image_path

    @property
    def notify_type(self):
        return self._notify_type

    @notify_type.setter
    @mark_modified()
    def notify_type(self, value):
        self._notify_type = value

    @property
    def message(self):
        return self._message

    @message.setter
    @mark_modified()
    def message(self, value):
        self._message = value

    @property
    def image_path(self):
        return self._image_path

    @image_path.setter
    @mark_modified()
    def image_path(self, value):
        self._image_path = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt' or not node.children:
            return

        parser = FunctionParser(
            name='notify',
            args=[
                Argument(name='message', type=str),
                Argument(name='warning', type=bool, optional=True),
                Argument(name='error', type=bool, optional=True),
                Argument(name='image_path', type=str, optional=True),
                Argument(name='timeout', type=float, optional=True),
            ],
        )
        success, args = parser.parse(node.children[0])

        if not success:
            return

        if args.get('error', False):
            notify_type = NotifyType.Error
        elif args.get('warning', False):
            notify_type = NotifyType.Warning
        else:
            notify_type = NotifyType.Notification

        yield NotifyBlock(
            node,
            parent,
            message=args.get('message', ''),
            image_path=args.get('image_path', ''),
            notify_type=notify_type,
            timeout=args.get('timeout', None),
        )

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
            return

        args = [prepare_string(self._message)]
        if self._notify_type == NotifyType.Warning:
            args.append('warning=True')
        elif self._notify_type == NotifyType.Error:
            args.append('error=True')
        if self._image_path:
            args.append(f'image_path="{self._image_path}"')

        yield '{}notify({args})\n'.format(
            self._get_indent(), args=', '.join(args)
        )
