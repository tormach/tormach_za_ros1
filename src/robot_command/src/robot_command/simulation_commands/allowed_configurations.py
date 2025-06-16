from ..rpl import Command


class AllowedConfigurations(Command):
    name = 'allowed_configurations'

    def __init__(self, config_names):
        if not isinstance(config_names, list):
            raise TypeError("Argument must be a list of strings")

        super().__init__()
        self.config_names = config_names

    def execute(self) -> None:
        print(f'executing {self.name}: {self.config_names}')

    def __str__(self):
        return f'{self.name}: {self.config_names}'
