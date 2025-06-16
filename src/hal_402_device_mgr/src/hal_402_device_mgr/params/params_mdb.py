from .params_base import EtherCATParamsBase


class EtherCATMDBParams(EtherCATParamsBase):
    _mdb_drive_name_map = dict(
        # InoServoShop gets this wrong in generated output
        IS620P='IS620N'
    )

    def __init__(self, mdb_fname, xml_fname, master=None, positions=None):
        self.mdb_fname = mdb_fname
        self.xml_fname = xml_fname
        # .mdb files only configure one drive; arbitrarily default to 0:0
        super().__init__(master=master or 0, positions=positions or [0])

    def read(self):
        with open(self.mdb_fname, newline='') as f:
            # Read device name from first line of file
            line = f.readline().rstrip()
            fields = line.split('_')
            name = self._mdb_drive_name_map.get(fields[0], fields[0])
            self.setup(name)

            # Read XML
            self.read_xml(self.xml_fname)

            # Read param values from rest of file
            for line in f:
                line = line.rstrip()
                if len(line) == 0:
                    continue  # \r\n; `open()` universal newlines broken?
                hcode, val = line.split()
                try:
                    sdo = self.sdos.from_hcode(hcode)
                except KeyError:
                    # .mdb files seem to contain a lot of junk
                    continue
                self.set(sdo, val)
