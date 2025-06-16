from enum import IntEnum
from parso.python import tree

from .parse_helpers import ParseException, convert_string, prepare_string
from .rpl_block import RPLBlock, mark_modified

from movej_ik_server.arm_configs import ArmConfigType


arm_config_type_strings = [str(config) for config in ArmConfigType]


class TargetType(IntEnum):
    Pose = 0
    Joints = 1


def detect_target_type(power):
    if power.children[0].type != 'name':
        return None
    prefix = power.children[0].value
    return {'p': TargetType.Pose, 'j': TargetType.Joints}.get(prefix, None)


def parse_target(power, type_):
    frame = ''
    arm_config = None
    rev_count = None

    pose_or_joints = {TargetType.Pose: 'p', TargetType.Joints: 'j'}
    if power.children[0].value != pose_or_joints.get(type_, None):
        return None
    p_trailer = power.children[1]

    # read numbers
    list_node = p_trailer.children[1]

    def get_value(node_):
        if node_.type == 'factor':
            value_string = ''.join(c.value for c in node_.children)
        else:
            value_string = node_.value
        return float(value_string)

    max_length = 12 if type_ == TargetType.Joints else 18
    if not 10 < len(list_node.children) < max_length:
        raise ParseException('Pose list has incorrect size.')

    # if there is other data than numbers, it must be a frame or arm config with rev count
    if len(list_node.children) > 12:
        frame_or_arm_config_node_candidate = list_node.children[12]

        if frame_or_arm_config_node_candidate.type == 'string':
            frame, _ = convert_string(frame_or_arm_config_node_candidate.value)

            if len(list_node.children) >= 16:
                arm_config_node_candidate = list_node.children[14]
                rev_count_node_candidate = list_node.children[16]

                if (
                    arm_config_node_candidate.type == 'name'
                    and rev_count_node_candidate.type == 'number'
                    and rev_count_node_candidate.value.isdigit()
                ):
                    if (
                        arm_config_node_candidate.value
                        in arm_config_type_strings
                    ):
                        arm_config = ArmConfigType[
                            arm_config_node_candidate.value
                        ]
                    else:
                        raise ParseException(
                            'Arm Config must be one of the valid arm configs.'
                        )

                    rev_count = int(rev_count_node_candidate.value)

        elif frame_or_arm_config_node_candidate.type == 'name':
            # if parameter list too short, e.g. rev_count missing
            if len(list_node.children) <= 14:
                raise ParseException(
                    'Arm Config must be specified with revolution count.'
                )

            if (
                frame_or_arm_config_node_candidate.value
                in arm_config_type_strings
            ):
                frame = ''
                arm_config = ArmConfigType[
                    frame_or_arm_config_node_candidate.value
                ]
            else:
                raise ParseException(
                    'Arm Config must be one of the valid arm configs.'
                )

            rev_count_candidate = list_node.children[14]
            if (
                rev_count_candidate.type == 'number'
                and rev_count_candidate.value.isdigit()
            ):
                rev_count = int(rev_count_candidate.value)
            else:
                raise ParseException('Rev count must be a number.')
        else:
            raise ParseException(
                'Argument for Frame/Arm Config must be a String or Config Type.'
            )

    try:
        data = [
            get_value(child)
            for i, child in enumerate(list_node.children[:11])
            if i % 2 == 0
        ]
    except (ValueError, AttributeError):
        raise ParseException('Error converting number.')
    return data, frame, arm_config, rev_count


class WaypointBlock(RPLBlock):
    type = 'waypoint'

    def __init__(
        self,
        node,
        parent,
        target=None,
        name='',
        frame='',
        arm_config=None,
        rev_count=None,
        target_type=TargetType.Pose,
        **kwargs,
    ):
        super().__init__(node, parent, **kwargs)
        if target is None:
            target = [0, 0, 0, 0, 0, 0]

        self._target = target
        self._target_type = target_type
        self._name = name
        self._frame = frame
        self._arm_config = arm_config
        self._rev_count = rev_count

    @property
    def target(self):
        return self._target

    @target.setter
    @mark_modified()
    def target(self, value):
        self._target = value

    @property
    def name(self):
        return self._name

    @name.setter
    @mark_modified()
    def name(self, value):
        self._name = value

    @property
    def frame(self):
        return self._frame

    @frame.setter
    @mark_modified()
    def frame(self, value):
        self._frame = value

    @property
    def arm_config(self):
        return self._arm_config

    @arm_config.setter
    @mark_modified()
    def arm_config(self, value):
        self._arm_config = value

    @property
    def rev_count(self):
        return self._rev_count

    @rev_count.setter
    @mark_modified()
    def rev_count(self, value):
        self._rev_count = value

    @property
    def target_type(self):
        return self._target_type

    @target_type.setter
    @mark_modified()
    def target_type(self, value):
        self._target_type = value

    @staticmethod
    def read(node, parent):
        if node.type != 'simple_stmt':
            return
        if not (
            any(node.children) and isinstance(node.children[0], tree.ExprStmt)
        ):
            return

        expr_stmt = node.children[0]
        if len(expr_stmt.children) != 3:
            return
        if expr_stmt.children[0].type != 'name':
            return
        name = expr_stmt.children[0].value
        if expr_stmt.children[2].type not in ('power', 'atom_expr'):
            return
        power = expr_stmt.children[2]
        type_ = detect_target_type(power)
        if type_ is None:
            return
        try:
            target, frame, arm_config, rev_count = parse_target(power, type_)
        except ParseException:
            return

        yield WaypointBlock(
            node,
            parent,
            target=target,
            target_type=type_,
            name=name,
            frame=frame,
            arm_config=arm_config,
            rev_count=rev_count,
        )

    def write(self):
        yield from self._write_disabled()
        if not self._needs_rewrite() and self.node:
            yield self.node.get_code()
        else:
            pose_or_joints = {TargetType.Pose: 'p', TargetType.Joints: 'j'}
            values = []
            for i, n in enumerate(self.target):
                decimals = (
                    self.program.linear_unit_decimals
                    if i < 3
                    else self.program.angular_unit_decimals
                )
                values.append(format(n, f'.{decimals}f'))
            target = ', '.join(values)
            if self._target_type == TargetType.Pose and self._frame:
                target += f', {prepare_string(self._frame)}'
            if self._target_type == TargetType.Pose and self._arm_config:
                target += f', {self._arm_config}'
            if self._target_type == TargetType.Pose and isinstance(
                self._rev_count, int
            ):
                target += f', {self._rev_count}'
            yield '{}{} = {}[{}]\n'.format(
                self._get_indent(),
                self._name,
                pose_or_joints[self._target_type],
                target,
            )
