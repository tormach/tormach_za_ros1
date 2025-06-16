from abc import ABCMeta

from ..rpl import Command, Pose, Joints


class Move(Command):
    __metaclass__ = ABCMeta
    name = 'move'

    def _check_target(self, target):
        if isinstance(target, (Pose, Joints) + (str,)):
            return target
        elif isinstance(target, list):
            return Pose(*target)
        else:
            raise TypeError(
                '{} requires Pose or Joints type as target argument'.format(
                    self.name
                )
            )

    def _check_move_params(self, a, v):
        if not (isinstance(a, (float, int)) and 0.0 < a <= 1.0):
            raise TypeError(
                '{} a parameter must be a number between 0.0 and 1.0'.format(
                    self.name
                )
            )

        if not (isinstance(v, (float, int)) and 0.0 < v <= 1.0):
            raise TypeError(
                '{} v parameter must be a number between 0.0 and 1.0'.format(
                    self.name
                )
            )
