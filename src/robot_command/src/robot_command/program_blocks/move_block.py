from parso.python import tree

from robot_command.program_blocks.parse_helpers import (
    FunctionParser,
    Argument,
    ParseException,
)
from .rpl_block import RPLBlock, mark_modified


class MoveBlock(RPLBlock):
    type = 'movel'

    MOVEJ_DEFAULT_VELOCITY_SCALE = 1.0
    DEFAULT_PROBE_MODE = 0
    MOVE_TYPES = ['movel', 'movej', 'movef']

    def __init__(
        self,
        node,
        parent,
        waypoint=None,
        velocity=None,
        velocity_scale=None,
        acceleration=None,
        acceleration_scale=None,
        duration=None,
        strict_limits=False,
        probe_mode=DEFAULT_PROBE_MODE,
        type_='movel',
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)
        if waypoint is None:
            waypoint = [0, 0, 0, 0, 0, 0]
        if velocity_scale is None and type_ == 'movej':
            velocity_scale = self.MOVEJ_DEFAULT_VELOCITY_SCALE
        self._waypoint = waypoint
        self._velocity = velocity
        self._velocity_scale = velocity_scale
        self._acceleration = acceleration
        self._acceleration_scale = acceleration_scale
        self._duration = duration
        self._probe_mode = probe_mode
        self._strict_limits = strict_limits
        self.type = type_

    @property
    def waypoint(self):
        return self._waypoint

    @waypoint.setter
    @mark_modified()
    def waypoint(self, value):
        self._waypoint = value

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    @mark_modified()
    def velocity(self, value):
        self._velocity = value

    @property
    def acceleration(self):
        return self._acceleration

    @acceleration.setter
    @mark_modified()
    def acceleration(self, value):
        self._acceleration = value

    @property
    def duration(self):
        return self._duration

    @duration.setter
    @mark_modified()
    def duration(self, value):
        self._duration = value

    @property
    def velocity_scale(self):
        return self._velocity_scale

    @velocity_scale.setter
    @mark_modified()
    def velocity_scale(self, value):
        self._velocity_scale = value

    @property
    def acceleration_scale(self):
        return self._acceleration_scale

    @acceleration_scale.setter
    @mark_modified()
    def acceleration_scale(self, value):
        self._acceleration_scale = value

    @property
    def probe_mode(self):
        return self._probe_mode

    @probe_mode.setter
    @mark_modified()
    def probe_mode(self, value):
        self._probe_mode = value

    @property
    def strict_limits(self):
        return self._strict_limits

    @strict_limits.setter
    @mark_modified()
    def strict_limits(self, value):
        self._strict_limits = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt' or not node.children:
            return

        # parse movel functions
        parser = FunctionParser(
            name='movel',
            args=[
                Argument(name='target', parsefunct=MoveBlock._parse_waypoint),
                Argument(name='accel_scale', type=float, optional=True),
                Argument(
                    name='velocity',
                    type=float,
                    parsefunct=MoveBlock._parse_type_with_units,
                    optional=True,
                ),
                Argument(name='accel', type=float, optional=True),
                Argument(name='duration', type=float, optional=True),
                Argument(name='strict_limits', type=bool, optional=True),
                Argument(name='probe', type=int, optional=True),
            ],
        )
        success, args = parser.parse(node.children[0])

        if success:
            yield MoveBlock(
                node,
                parent,
                waypoint=args.get('target'),
                velocity=args.get('velocity', None),
                acceleration=args.get('accel', None),
                acceleration_scale=args.get('accel_scale', None),
                strict_limits=args.get('strict_limits', None),
                duration=args.get('duration', None),
                probe_mode=args.get('probe', MoveBlock.DEFAULT_PROBE_MODE),
                type_='movel',
            )
            return

        # parse movej functions
        parser = FunctionParser(
            name='movej',
            args=[
                Argument(name='target', parsefunct=MoveBlock._parse_waypoint),
                Argument(name='velocity_scale', type=float, optional=True),
                Argument(name='probe', type=int, optional=True),
            ],
        )
        success, args = parser.parse(node.children[0])

        if success:
            yield MoveBlock(
                node,
                parent,
                waypoint=args.get('target'),
                velocity_scale=args.get(
                    'velocity_scale', MoveBlock.MOVEJ_DEFAULT_VELOCITY_SCALE
                ),
                probe_mode=args.get('probe', MoveBlock.DEFAULT_PROBE_MODE),
                type_='movej',
            )
            return

        # parse movef functions
        parser = FunctionParser(
            name='movef',
            args=[
                Argument(name='waypoint', parsefunct=MoveBlock._parse_waypoint),
            ],
        )
        success, args = parser.parse(node.children[0])

        if success:
            yield MoveBlock(
                node, parent, waypoint=args.get('waypoint'), type_='movef'
            )
            return

    @staticmethod
    def _parse_waypoint(node, _target_type):
        if isinstance(node, (tree.Name, tree.String)):
            return node.value
        else:
            raise ParseException('Could not read waypoint')

    @staticmethod
    def _parse_type_with_units(node, _target_type):
        pass  # TODO

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            args = [self._waypoint]
            if self.type == 'movel':
                if self._velocity is not None:
                    args.append(f'velocity={self._velocity}')
                if self._acceleration is not None:
                    args.append(f'accel={self._acceleration}')
                elif self._acceleration_scale is not None:
                    args.append(f'accel_scale={self._acceleration_scale}')
                if self._duration is not None:
                    args.append(f'duration={self._duration}')
                if self._strict_limits:
                    args.append(f'strict_limits={self._strict_limits}')
                if self._probe_mode != self.DEFAULT_PROBE_MODE:
                    args.append(f'probe={self._probe_mode}')
            elif self.type == 'movej':
                if self._velocity_scale is not None:
                    args.append(f'velocity_scale={self._velocity_scale}')
                if self._probe_mode != self.DEFAULT_PROBE_MODE:
                    args.append(f'probe={self._probe_mode}')
            yield '{}{}({args})\n'.format(
                self._get_indent(), self.type, args=', '.join(args)
            )
