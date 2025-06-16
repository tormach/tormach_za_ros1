from .subsystem import (
    SubSystem,
    SubSystemCheck,
)

import socket

from gr60_gripper.feetech.udp_feetech_device import UDPFeetechDevice
from gr60_gripper.feetech import FeetechServo


class EthernetHM2NetworkHardware(SubSystemCheck):
    """Get state of hardware present on the line"""

    name = "ethernet_network_hardware"

    def probe_eth_io_board(self, board_ip, host_ip):
        drv_sys_add = (host_ip, 4001)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as can:
                can.bind(drv_sys_add)
                can.settimeout(1)

                # send probe
                payload = b'\x2F'
                can.sendto(payload, (board_ip, 4001))

                # receive probe response
                control_board_info = self.get_device_info(can)
                return control_board_info
        except Exception as e:
            self.log_warning(f'Error during querying of the control board: {e}')

    def get_device_info(self, canet_socket) -> dict:
        result = {}

        try:
            data, addr = canet_socket.recvfrom(24)
            fw_version = data[1:9].decode('ascii')
            hw_version = data[9:17].decode('ascii')
            try:
                release_date = data[17:25].decode('ascii')
            except UnicodeDecodeError:
                release_date = data[17:25]
            result = {
                'firmware': fw_version,
                'hardware': hw_version,
                'release': release_date,
            }
        except Exception as e:
            self.log_warning(
                f"Did not receive reply from the control board. ({e})"
            )
        finally:
            return result

    def probe_gr60_gripper(self, board_ip, host_ip) -> bool:
        try:
            device = UDPFeetechDevice(host_ip, board_ip, baudrate=115200)
            FeetechServo(device, 1, exception_on_error_response=False)
            return True
        except Exception:
            return False

    def acquire_data(self) -> dict:
        readout = self.probe_eth_io_board(
            board_ip='10.9.0.51', host_ip='10.9.0.42'
        )

        if readout is None:
            readout = {}

        if readout and self.probe_gr60_gripper(
            board_ip='10.9.0.51', host_ip='10.9.0.42'
        ):
            readout['tools'] = ["gr60_gripper"]

        return readout

    def run_check(self) -> bool:
        readout = self.acquire_data()

        self.set_cache("control_board", readout)
        self.log_info("Got info about control board on network")
        return True

    def process_data(self, data) -> dict:
        processed_data = {'board': False}
        if 'hardware' in data:
            processed_data['board'] = True
        if 'tools' in data and 'gr60_gripper' in data.get('tools'):
            processed_data['gr60_gripper'] = True
        return processed_data

    def result_data(self) -> dict():
        try:
            res = self.cached_result()
            if res:
                return self.process_data(self.get_cache("control_board", {}))
        except RuntimeError as e:
            self.log_warning(f'Cannot retrieve check data: {e}')
        return {'board': False}


class EthernetHM2(SubSystem):
    """Check the Ethernet base system and pass into the container."""

    name = "EthernetHM2"

    check_classes = [
        EthernetHM2NetworkHardware,
    ]
