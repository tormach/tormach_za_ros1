from ..rpl import Command


class SetUnits(Command):
    name = 'set_units'

    def __init__(self, linear, angular, time):
        super().__init__()
        self.linear_unit = linear
        self.angular_unit = angular
        self.time_unit = time

    def execute(self):
        print(
            f'executing {self.name}: linear={self.linear_unit}, '
            f'angular={self.angular_unit}, time={self.time_unit}'
        )

    def __str__(self):
        return (
            f'{self.name}: '
            f'{self.linear_unit} {self.angular_unit} {self.time_unit}'
        )
