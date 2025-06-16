class ResponseError(Exception):
    def __init__(self, value, description):
        self.value = value
        self.description = description

    def __str__(self):
        return f"Servo error {self.value}: {self.description}"


class CommunicationError(RuntimeError):
    pass


class ConfigurationError(Exception):
    pass
