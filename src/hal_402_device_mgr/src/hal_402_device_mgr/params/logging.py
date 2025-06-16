import rospy
import logging
import rosgraph


class Logging:
    # Flexibly use `logging` or `rospy` loggers so that the utilities
    # can be used when ROS isn't running

    # Dispatchers for logging methods
    _dispatcher = {
        True: dict(  # master online:  `rospy` module methods
            debug='logdebug',
            info='loginfo',
            warn='logwarn',
            err='logerr',
            fatal='logfatal',
        ),
        False: dict(  # master NOT online:  `logging` instance methods
            debug='debug',
            info='info',
            warn='warning',
            err='error',
            fatal='critical',
        ),
    }

    _logging_levels = dict(
        DEBUG='DEBUG',
        INFO='INFO',
        WARN='WARNING',
        ERR='ERROR',
        FATAL='CRITICAL',
    )

    def __init__(self, name='root', level='INFO'):
        self.name = name
        self.master_online = rosgraph.is_master_online()
        self.level = getattr(self, level)

    def _get_logger(self):
        if hasattr(self, '_logger'):
            return self._logger
        if self.master_online:
            logger = rospy
        else:
            logger = logging.getLogger(self.name)
            if hasattr(logger, 'setFormatter'):  # RospyLogger doesn't
                formatter = logging.Formatter(
                    '%(name)s:%(levelname)s: %(message)s'
                )
                logger.setFormatter(formatter)
            logger.setLevel(self.level)
            # The ROS environment causes `logging.getLogger()` to
            # return `<RospyLogger hal_402_device_mgr.params.commands (level)>`
            # objects, which don't work without the following line.
            # :P
            logging.basicConfig(level=self.level)
        self._logger = logger
        return logger

    def setLevel(self, level):
        if not self.master_online:
            # (rospy log level set externally)
            logging_level = self._logging_levels[level]
            self.logger.setLevel(logging_level)

    def __getattr__(self, name):
        if name == 'logger':
            return self._get_logger()
        if name in self._dispatcher[True]:
            return getattr(
                self.logger, self._dispatcher[self.master_online][name]
            )
        if name in self._logging_levels:
            # Don't worry about rospy log level, set externally
            return self._logging_levels[name]
        raise AttributeError(f"'Logging' object has no attribute '{name}'")

    @classmethod
    def getLogger(cls, name):
        # Look like Python Logging.getLogger()
        return cls(name)
