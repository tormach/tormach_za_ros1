import re
from .params_base import EtherCATParamsBase
from .commands import (
    EtherCATUpload,
    EtherCATDownload,
    EtherCATSlaves,
    EtherCATException,
)
from crcmod import mkCrcFun
from uuid import uuid4
import time
import rospy


class EtherCATDriveParams(EtherCATParamsBase):
    slave_name_re = re.compile(r'Order number: (?:Ino)?(.*)$', flags=re.M)
    slave_vendor_re = re.compile(r'Vendor Id: +(.*)$', flags=re.M)
    slave_product_code_re = re.compile(r'Product code: +(.*)$', flags=re.M)

    def __init__(self, xml_fname, *args, **kwargs):
        self.xml_fname = xml_fname
        super().__init__(*args, **kwargs)

    def read(self):
        self.setup(self.query_device_type())

        self.read_xml(self.xml_fname)

        for sdo in self.sdos.values():
            # May be fewer entries on drive than in schema (e.g. PDO
            # mapping); skip these
            if sdo.subindex > 0 and self.get(sdo.index, 0)[0] < sdo.subindex:
                continue

            vals = list()
            for p in self.positions:
                try:
                    val = self.upload(sdo, p - 1)
                    vals.append(val)
                except Exception:
                    vals.append(None)
            self.set(sdo, vals)

    _commands = dict(
        upload=EtherCATUpload(),
        download=EtherCATDownload(),
        slaves=EtherCATSlaves(),
    )

    def write(self, params=None, dry_run=False):
        if params is not None:
            params = [self.sdos.from_str(p) for p in params]
        for sdo in self._params:
            for p in self.positions:
                if params is not None and sdo not in params:
                    continue
                val = self.get(sdo, positions=p)[0]
                # Verify param needs writing first
                if self.upload(sdo, p) == val:
                    continue
                self.download(sdo, p, val, dry_run=dry_run)

    def upload(self, sdo, position):
        res_raw = self._commands['upload'].run(
            sdo.index,
            sdo.subindex,
            master=self.master,
            position=position,
            type=sdo.data_type.igh_type,
        )
        return sdo.data_type(res_raw)

    def download(self, sdo, position, val, dry_run=False):
        # Check value before setting to go easy on NVRAM
        res_raw = self._commands['upload'].run(
            sdo.index,
            sdo.subindex,
            master=self.master,
            position=position,
            type=sdo.data_type.igh_type,
        )
        if sdo.data_type(res_raw) == val:
            # Nothing to do
            return
        self._commands['download'].run(
            sdo.index,
            sdo.subindex,
            val,
            master=self.master,
            position=position,
            type=sdo.data_type.igh_type,
            dry_run=dry_run,
        )

    def query_device_type(self):
        res_raw = self._commands['slaves'].run(
            master=self.master, position=self.positions[0], verbose=True
        )
        res = res_raw.decode()
        vid = int(self.slave_vendor_re.search(res).group(1), 16)
        pc = int(self.slave_product_code_re.search(res).group(1), 16)
        return (vid, pc)

    @property
    def nv_params_sdo(self):
        if self.model_id == (0x00100000, 0x000C0108):  # IS620N
            sdo_str = '200C-0Eh'
        elif self.model_id == (0x00100000, 0x000C010D):  # SV660N
            sdo_str = '200E-02h'
        else:
            raise RuntimeError(f"Unknown model ID:  {self.model_id}")
        return self.get_sdo(sdo_str)

    nv_params_on = 3  # Drive params non-volatile
    nv_params_off = 0  # Drive params volatile

    def set_params_nv(self, position, off=False, dry_run=False):
        sdo = self.nv_params_sdo
        val = self.nv_params_off if off else self.nv_params_on
        self.download(sdo, position, val, dry_run=dry_run)

    def get_params_nv(self, position):
        sdo = self.nv_params_sdo
        val = self.upload(sdo, position)
        if val not in (self.nv_params_on, self.nv_params_off):
            return None
        else:
            return val == self.nv_params_on

    # GUIDs
    # https://stackoverflow.com/questions/35205702

    # Disallow defaults for used IS620N params
    bad_vals = {100000, 10000, 1000, 10, 0}

    @property
    def guid_sdos(self):
        if self.model_id == (0x00100000, 0x000C0108):  # IS620N
            return '200F-05h', '200F-09h', '200F-0Eh'
        if self.model_id == (0x00100000, 0x000C010D):  # SV660N
            # 2019h "Target position parameters" suggested by Raul
            return '2019-01h', '2019-04h', '2019-07h'
        raise RuntimeError(f"Unknown model ID:  {self.model_id}")

    @property
    def crc16(self):
        return mkCrcFun(0x18005, rev=False, initCrc=0xFFFF, xorOut=0x0000)

    def get_guid(self, position):
        uid0_sdo, uid1_sdo, crc_sdo = self.guid_sdos
        uid0 = self.upload(self.get_sdo(uid0_sdo), position)
        uid1 = self.upload(self.get_sdo(uid1_sdo), position)
        crc_drv = self.upload(self.get_sdo(crc_sdo), position)
        uid = (uid0 << 24) + uid1
        crc16 = mkCrcFun(0x18005, rev=False, initCrc=0xFFFF, xorOut=0x0000)
        crc_calc = crc16(uid.to_bytes(6, 'big'))
        return uid if crc_drv == crc_calc else None

    def set_guid(self, position, force=False, dry_run=False):
        if not force and self.get_guid(position) is not None:
            return  # Already set
        # Generate random UUID; split out two 24-bit chunks & generate CRC
        while True:
            uid = uuid4()
            uid0 = (uid.int >> 104) & 0xFFFFFF  # First 24 bits
            uid1 = (uid.int >> 80) & 0xFFFFFF  # Second 24 bits
            crc = self.crc16(uid.bytes[0:6])  # crc16 of first 48 bits
            if (
                uid0 in self.bad_vals
                or uid1 in self.bad_vals
                or crc in self.bad_vals
            ):
                continue  # Reject any values that look like drive defaults
            break  # Values look good

        # Turn on non-volatile param mode, write values and turn off
        uid0_sdo, uid1_sdo, crc_sdo = self.guid_sdos
        old_nv_off = not self.get_params_nv(position)
        self.set_params_nv(position, off=False, dry_run=dry_run)
        sdo = self.get_sdo(uid0_sdo)
        self.download(sdo, position, uid0, dry_run=dry_run)
        sdo = self.get_sdo(uid1_sdo)
        self.download(sdo, position, uid1, dry_run=dry_run)
        sdo = self.get_sdo(crc_sdo)
        self.download(sdo, position, crc, dry_run=dry_run)
        self.set_params_nv(position, off=old_nv_off, dry_run=dry_run)

    @property
    def brake_func_sdos(self):
        if self.model_id == (0x00100000, 0x000C0108):  # IS620N
            sdos = ('2004-01h', '2004-03h')  # 2004-01h:  Rob's robot
        elif self.model_id == (0x00100000, 0x000C010D):  # SV660N
            sdos = ('2004-05h',)
        else:
            raise RuntimeError(f"Unknown model ID:  {self.model_id}")
        return (self.get_sdo(s) for s in sdos)

    brake_func_on = 0x0009
    brake_func_off = 0x0000

    def set_brake_func(self, position, on, dry_run=False):
        val = self.brake_func_on if on else self.brake_func_off
        for sdo in self.brake_func_sdos:
            self.download(sdo, position, val, dry_run=dry_run)

    def clear_encoder_multiturn_data(self, position, dry_run=False):
        if self.model_id == (0x00100000, 0x000C0108):  # IS620N
            # FIXME Running this causes Er. 136 on IS620N; skip for now
            rospy.loginfo(
                f"  NOT resetting multiturn data for IS620N drive {position}"
            )
            return
        sdo = self.get_sdo("200D-15h")
        self.download(sdo, position, 2, dry_run=dry_run)
        time.sleep(1)  # This takes a while on SV660 drives
        self.reset_drive(position, dry_run=dry_run)

    def zero_home_offset(self, position, dry_run=False):
        # Zero difference between mechanical zero & motor home; normally in
        # ethercat_drive_params.yaml, this param is set here to compensate for
        # early models homed with J3 in non-zero vertical position
        sdo = self.get_sdo("607C-00h")
        self.download(sdo, position, 0, dry_run=dry_run)

    # How long to wait for drive to reset (us. ~15 seconds)
    drive_reset_timeout = 30.0

    def reset_drive(self, position, dry_run=False):
        # Reset or "reboot" the drive from software; wait for drive to reenter
        # PREOP state before proceeding, because downstream drives will be
        # disconnected for a few seconds

        # 0x200d 0x01 -t uint16 0x0001
        sdo = self.get_sdo("200D-01h")
        # Set timeout for entire operation
        timeout = time.time() + self.drive_reset_timeout
        # Issue reset command & wait for drive leave operational state
        old_state = None
        state = self.query_slave_state(position)
        while state == "OP":
            if time.time() > timeout:
                raise RuntimeError(f"Drive {position} failed to leave OP state")
            try:
                self.download(sdo, position, 1, dry_run=dry_run)
            except EtherCATException:
                pass  # Ignore; drive maybe went offline
            time.sleep(0.4)
            old_state = state
            state = self.query_slave_state(position)
        rospy.loginfo(f"  Drive {position} state {old_state} -> {state}")
        # Wait for drive to reenter OP state
        while state != "OP":
            if time.time() > timeout:
                raise RuntimeError(
                    f"Drive {position} failed to reenter OP state"
                )
            time.sleep(0.2)
            old_state = state
            state = self.query_slave_state(position)
            if old_state != state:
                rospy.loginfo(
                    f"  Drive {position} state {old_state} -> {state}"
                )
        # Now wait another moment to be sure drive state is stable and check
        # once more
        timeout = time.time() + 2
        while time.time() < timeout:
            time.sleep(0.2)
            old_state = state
            state = self.query_slave_state(position)
            if old_state != state:
                rospy.loginfo(
                    f"  Drive {position} state {old_state} -> {state}"
                )
        if self.query_slave_state(position) != "OP":
            raise RuntimeError(
                f"Drive {position} failed to stabilize after reset"
            )
        rospy.loginfo(f"  Drive {position} reentered OP state after reset")

    slave_state_re = re.compile(r'State: (.*)$', flags=re.M)

    def query_slave_state(self, position):
        try:
            res_raw = self._commands['slaves'].run(
                master=self.master, position=position, verbose=True
            )
        except EtherCATException:
            return None
        match = self.slave_state_re.search(res_raw.decode())
        return match.group(1) if match else None
