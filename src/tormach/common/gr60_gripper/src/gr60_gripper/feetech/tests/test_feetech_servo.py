import pytest
from unittest.mock import Mock

from gr60_gripper.feetech import CommunicationError
from gr60_gripper.feetech.feetech_servo import FeetechServo


@pytest.fixture
def mock_feetech_device():
    return Mock()


@pytest.fixture
def servo(mock_feetech_device):
    return FeetechServo(mock_feetech_device, 1)


# fmt: off
@pytest.mark.parametrize("data,expected_result", [
    ((bytes([b]) for b in b'\xff\x01\x03\x00\x06\xf5\x00\x00\x00'), (b'\xf5', 0)),
    ((bytes([b]) for b in b'\xff\xff\x01\x03\x00\x06\xf5\x00\x00\x00'), (b'\xf5', 0)),
    ((b'\x01\xff\x03\x00\x06\xf5\x00\x00\x00',), None),
    ((bytes([b]) for b in b'\x00\xff\x01\x03\x00\x06\xf5\x00\x00\x00'), (b'\xf5', 0)),
    ((bytes([b]) for b in b'\x00\xff\x01\x03\x00\x06\xf4\x00\x00\x00'), None),
    ((bytes([b]) for b in b'\x00\xff\x01\x03\x00\x06\xaa\x00\x00\x00'), None),
    ((bytes([b]) for b in b'\x00\xff\x01\x03\x00\x06\xf5'), (b'\xf5', 0)),
])
# fmt: on
def test_receive_reply(data, expected_result):
    if expected_result is None:
        with pytest.raises(CommunicationError):
            FeetechServo._receive_reply(data, servo_id=1, timeout=0)
    else:
        result = FeetechServo._receive_reply(data, servo_id=1, timeout=0)
        assert result == expected_result
