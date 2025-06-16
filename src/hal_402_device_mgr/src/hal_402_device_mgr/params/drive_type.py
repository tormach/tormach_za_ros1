import re
from hal_402_device_mgr.params.commands import EtherCATSlaves


def drive_type():
    slave_name_re = re.compile(r'Order number: (?:Ino)?(.*)$', flags=re.M)
    try:
        slaves_cmd = EtherCATSlaves()
        res = slaves_cmd.run(master=0, position=0, verbose=True)
        match = slave_name_re.search(res.decode())
        if match:
            return match.group(1)
    except Exception:
        pass  # No EtherCAT drives detected
    return ""
