from ..rpl import Command


class Pause(Command):
    name = 'pause'

    OPTIONAL_STOP_PARAM = 'user_config/optional_stop'

    def __init__(self, optional=False, active=False):
        super().__init__()

        self.optional = bool(optional)
        self.active = bool(active)

    def execute(self):
        print(f'executing pause: optional={self.optional} active={self.active}')

    def __str__(self):
        return f'{self.name}: optional={self.optional} active={self.active}'
