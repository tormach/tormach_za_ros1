import re


class EtherCATSDO:
    hcode_re = re.compile(r'^h([0-9a-f]{2})([0-9]{2})$', flags=re.I)
    sdo_re = re.compile(
        r'^(?:0x)?([0-9a-f]{4})-([0-9a-f]{2})(?:h)?$', flags=re.I
    )

    def to_int(self, i):
        if not isinstance(i, str):
            # No conversion necessary (unless None)
            return i or 0
        else:
            # Convert dec or hex string
            return int(i, 0)

    def __init__(self, index, subindex, data_type, **kwargs):
        self.index = self.to_int(index)
        self.subindex = self.to_int(subindex)
        self.data_type = data_type
        self.kwargs = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def hex_index(self):
        return f'{self.index:04X}'

    @property
    def hex_subindex(self):
        return f'{self.subindex:02X}'

    @property
    def comment_name(self):
        return self.kwargs.get('Name')

    @property
    def parent_comment(self):
        return self.kwargs.get('ParentName')

    def __str__(self):
        return f'{self.hex_index}-{self.hex_subindex}h'

    def __repr__(self):
        return f'<EtherCATSDO {self.__str__()}>'

    def hcode(self):
        if self.index & 0xFF00 != 0x2000:
            raise ValueError("H codes only allowed for index in 0x2000 range")
        return f'H{self.index&0xff:02X}-{self.subindex:02d}'

    def to_ecat_value(self, value):
        return self.data_type(value)

    @classmethod
    def parse_sdo(cls, sdo_str):
        return (int(i, 16) for i in cls.sdo_re.match(sdo_str).groups())

    @classmethod
    def parse_hcode(cls, hcode):
        hpre, hsuf = cls.hcode_re.match(hcode.lower()).groups()
        index = 0x2000 + int(hpre, 16)
        subindex = int(hsuf) + 1
        return index, subindex
