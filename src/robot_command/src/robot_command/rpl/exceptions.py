class RobotProgramError(Exception):
    pass


class MoveError(RobotProgramError):
    pass


class MovePlanningError(MoveError):
    pass


class MoveExecutionError(MoveError):
    def __init__(self, message=None, error_code=None):
        # Pass the formatted message up the chain, or provide a generic one here
        if message is None:
            message = "Motion failed during execution (no error context provided, see warnings for details)"
        super().__init__(message)
        self.error_code = error_code


class PathToleranceError(MoveExecutionError):
    def __init__(self, error_code=None):
        super().__init__(
            "Path tolerance exceeded (try running move slower or increasing allowed path tolerance)",
            error_code,
        )


class GoalToleranceError(MoveExecutionError):
    def __init__(self, error_code=None):
        super().__init__(
            "Goal position was not reached the allowed goal time (after trajectory completion)",
            error_code,
        )


class ProbeError(MoveExecutionError):
    pass


class ProbeUnexpectedContactError(ProbeError):
    def __init__(self, error_code=None):
        message = "Unexpected probe contact (rising edge) during motion."
        super().__init__(message, error_code)


class ProbeContactAtStartError(ProbeError):
    def __init__(self, error_code=None):
        message = "Cannot start a non-probe motion with probe active (must be in probe mode 4,5 or 6)"
        super().__init__(message, error_code)


class ProbeFailedError(ProbeError):
    def __init__(self, error_code=None):
        message = "Probe failed to detect contact during motion"
        super().__init__(message, error_code)


class PathPilotError(RobotProgramError):
    def __init__(self, message: str, instance: str):
        super().__init__(message)
        self.instance = instance


class PathPilotInstanceNotConnectedError(PathPilotError):
    pass


class PathPilotInstanceNotFoundError(PathPilotError):
    pass


class ActuateGripperError(RobotProgramError):
    pass
