import rospy
from redis_store import ConfigClient

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement, QmlUncreatable

from ..qt_helpers import ensure_cleanup

DIGITAL_IO_NAMESPACE = 'io'

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("DigitalIO cannot be created in QML")
class DigitalIO(QObject):
    nameChanged = Signal(str)

    def __init__(self, parent=None, number=0, name='', topic=''):
        super().__init__(parent)

        self._number = number
        self._name = name
        self._topic = topic

    @Property(int, constant=True)
    def number(self):
        return self._number

    @Property(str, constant=True)
    def topic(self):
        return self._topic

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == self._name:
            return
        self._name = value
        self.nameChanged.emit(value)


@QmlElement
class DigitalIOs(QObject):
    """High level access to the digital IO topics and names."""

    digitalInputsChanged = Signal()
    digitalOutputsChanged = Signal()
    digitalInputNamesChanged = Signal()
    digitalOutputNamesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigClient()

        self._digital_inputs = []
        self._digital_outputs = []

        ensure_cleanup(self._shutdown)

    @Property(list, notify=digitalInputsChanged)
    def digitalInputs(self):
        return self._digital_inputs

    @Property(list, notify=digitalInputNamesChanged)
    def digitalInputNames(self):
        return [io.name for io in self._digital_inputs if io.name != ""]

    @Property(list, notify=digitalOutputNamesChanged)
    def digitalOutputNames(self):
        return [io.name for io in self._digital_outputs if io.name != ""]

    @Property(list, notify=digitalOutputsChanged)
    def digitalOutputs(self):
        return self._digital_outputs

    def _read_digital_ios(self, name_param, topic_param):
        names = rospy.get_param(name_param, {})
        topics = rospy.get_param(topic_param, [])

        ios = []
        names_by_nr = {names[name]: name for name in names}
        for i, topic in enumerate(topics):
            nr = i + 1
            io = DigitalIO(name=names_by_nr.get(nr, ''), number=nr, topic=topic)
            ios.append(io)
        return ios

    def _write_digital_io_names(self, ios, name_param):
        io_names = {io.name: io.number for io in ios if io.name != ''}
        result = self._config.set_param(name_param, io_names)
        if not result:
            raise KeyError(f'Error setting digital ios {name_param}')

    @Slot()
    def update(self):
        digital_in_names = f'{DIGITAL_IO_NAMESPACE}/digital_in_names'
        self._digital_inputs = self._read_digital_ios(
            digital_in_names,
            f'{DIGITAL_IO_NAMESPACE}/digital_in_topics',
        )
        for io in self._digital_inputs:
            io.nameChanged.connect(
                lambda: self._write_digital_io_names(
                    self._digital_inputs, digital_in_names
                )
            )
            io.nameChanged.connect(self.digitalInputNamesChanged)
        self.digitalInputsChanged.emit()

        digital_out_names = f'{DIGITAL_IO_NAMESPACE}/digital_out_names'
        self._digital_outputs = self._read_digital_ios(
            digital_out_names,
            f'{DIGITAL_IO_NAMESPACE}/digital_out_topics',
        )
        for io in self._digital_outputs:
            io.nameChanged.connect(
                lambda: self._write_digital_io_names(
                    self._digital_outputs, digital_out_names
                )
            )
            io.nameChanged.connect(self.digitalOutputNamesChanged)
        self.digitalOutputsChanged.emit()

    @Slot()
    def _shutdown(self):
        self._config.stop()
