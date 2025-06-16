from uuid import uuid4

from .program_blocks.waypoint_block import (
    WaypointBlock,
    TargetType,
)


class Waypoint:
    """
    Represents a waypoint in a robot program. This waypoint object is meant to
    be simpler to construct and to work with compared to the corresponding
    WaypointBlock.
    """

    def __init__(
        self,
        name='',
        target=None,
        target_type=TargetType.Pose,
        frame='',
        uuid=None,
        node=None,
        arm_config=None,
        rev_count=None,
    ):
        self._name = name
        self._target = target or [0, 0, 0, 0, 0, 0]
        self._target_type = target_type
        self._frame = frame
        self._arm_config = arm_config
        self._rev_count = rev_count
        self.uuid = uuid or str(uuid4())
        self.node = node
        self._modified = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self._modified = True

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value
        self._modified = True

    @property
    def target_type(self):
        return self._target_type

    @target_type.setter
    def target_type(self, value):
        self._target_type = value
        self._modified = True

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, value):
        self._frame = value
        self._modified = True

    @property
    def arm_config(self):
        return self._arm_config

    @arm_config.setter
    def arm_config(self, value):
        self._arm_config = value

    @property
    def rev_count(self):
        return self._rev_count

    @rev_count.setter
    def rev_count(self, value):
        self._rev_count = value

    @property
    def modified(self):
        return self._modified

    @staticmethod
    def from_waypoint_block(block):
        """
        :type block: WaypointBlock
        """
        return Waypoint(
            name=block.name,
            target=block.target[:],
            target_type=block.target_type,
            frame=block.frame,
            node=block.node,
            arm_config=block.arm_config,
            rev_count=block.rev_count,
        )

    def to_waypoint_block(self, parent):
        block = WaypointBlock(
            self.node,
            parent,
            name=self.name,
            target=self.target[:],
            target_type=self.target_type,
            frame=self.frame,
            arm_config=self.arm_config,
            rev_count=self.rev_count,
        )
        block._modified = self._modified
        return block
