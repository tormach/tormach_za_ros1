import pytest
from unittest.mock import Mock
from gr60_gripper.feetech.udp_feetech_device import (
    EthIoRs485Interface,
    ConfigurationError,
)
from gr60_gripper.feetech.exceptions import CommunicationError


@pytest.fixture
def ethio_rs485_interface():
    return EthIoRs485Interface(
        host_ip="127.0.0.1", target_ip="10.42.0.41", port=8000
    )


def test_trans_recv_raises_erro_on_invalid_buffer_type(ethio_rs485_interface):
    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv("invalid", to_read=10, wait_ms=50)


def test_trans_recv_raises_error_on_invalid_to_read(ethio_rs485_interface):
    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv(b"", to_read=-1, wait_ms=50)

    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv(b"", to_read=300, wait_ms=50)


def test_trans_recv_raises_error_on_invalid_wait_ms(ethio_rs485_interface):
    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv(b"", to_read=10, wait_ms=-1)

    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv(b"", to_read=10, wait_ms=300)


def test_trans_recv_raises_error_on_invalid_buffer_size(ethio_rs485_interface):
    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv(b"", to_read=10, wait_ms=50 * 255)

    with pytest.raises(ConfigurationError):
        ethio_rs485_interface.trans_recv(b"\x00" * 256, to_read=10, wait_ms=50)


def test_trans_recv_send_prepares_data_correctly(ethio_rs485_interface):
    ethio_rs485_interface._sock = Mock()
    ethio_rs485_interface._sock.sendto = Mock()
    ethio_rs485_interface._sock.recvfrom = Mock(
        return_value=(b"\xaa\x01\x02", ("127.0.0.1", 8000))
    )
    result = ethio_rs485_interface.trans_recv(
        b"\x01\x02", to_read=2, wait_ms=50
    )
    assert result == b"\x01\x02"
    ethio_rs485_interface._sock.sendto.assert_called_once_with(
        b"\x80\x00\x86\x05\x00\x02\x02" + b"\x01\x02" + b"\x32",
        ("10.42.0.41", 8000),
    )
    ethio_rs485_interface._sock.recvfrom.assert_called_once_with(3)


def test_trans_recv_receive_data_with_invalid_checksum_raises_error(
    ethio_rs485_interface,
):
    ethio_rs485_interface._sock = Mock()
    ethio_rs485_interface._sock.sendto = Mock()
    ethio_rs485_interface._sock.recvfrom = Mock(
        return_value=(b"\xbb\x01\x02", ("127.0.0.1", 8000))
    )
    with pytest.raises(CommunicationError):
        ethio_rs485_interface.trans_recv(b"\x01\x02", to_read=2, wait_ms=50)
