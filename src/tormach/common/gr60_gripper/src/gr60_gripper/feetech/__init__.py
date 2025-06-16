import contextlib
import logging

import serial

from .exceptions import CommunicationError
from .feetech_servo import FeetechServo
from .feetech_device import FeetechDevice  # noqa: F401
from .usb_feetech_device import USB2FeetechDevice

logger = logging.getLogger(__name__)


def find_servos(device, max_id=252, print_progress=False):
    """Finds all servo IDs on the serial bus"""
    servos = []
    prev_timeout = device.servo_dev.timeout
    device.servo_dev.timeout = 0.03  # To make the scan faster
    for i in range(max_id + 1):  # 0..max_id
        with contextlib.suppress(CommunicationError):
            _ = FeetechServo(device, i, retry_count=0)
            if print_progress:
                print("FOUND A SERVO @ ID %d" % i)
            servos.append(i)
    device.servo_dev.timeout = prev_timeout
    return servos


def find_servos_on_all_ports(max_id=252, print_progress=False):
    ports = serial.tools.list_ports.comports()
    result = []
    for port in ports:
        device_name = port[0]
        if (
            'ttyUSB' in device_name
            or 'ttyACM' in device_name
            or 'COM' in device_name
        ):
            if print_progress:
                print(f"device: {device_name}")
            try:
                connection = USB2FeetechDevice(device_name)
                if servo_ids := find_servos(
                    connection, max_id=max_id, print_progress=print_progress
                ):
                    result.append((device_name, servo_ids))
            except RuntimeError as e:
                logger.warning(e)
    return result
