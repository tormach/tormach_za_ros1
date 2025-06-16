#!/usr/bin/env python
import argparse
import os
import re
import sys
from xml.sax.saxutils import escape

XML_HEADER = '''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="{lang}">
<context>
    <name></name>
'''
XML_MESSAGE = '''\
    <message id="{id}">
        <source></source>
        <translation>{tr}</translation>
    </message>
'''
XML_FOOTER = '''\
</context>
</TS>
'''


def read_po_data(data):
    msg_re = re.compile(r'msgid\s+"(.*)"\s*\nmsgstr\s+"(.*)"')
    return msg_re.findall(data)


def write_ts_file(data, path, lang):
    with open(path, 'w') as f:
        f.write(XML_HEADER.format(lang=lang))
        for id_, tr in data:
            tr = tr.replace('\\n', '<br>')
            tr = escape(tr)  # XML escape
            f.write(XML_MESSAGE.format(id=id_, tr=tr))
        f.write(XML_FOOTER)


def convert_po_to_ts(in_path, out_path, lang):
    with open(in_path) as f:
        data = f.read()
    po_data = read_po_data(data)
    write_ts_file(po_data, out_path, lang)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Converts .po files to .ts files"
    )
    parser.add_argument("po_file", type=str)
    parser.add_argument("-l", "--language", type=str, default='en')
    args = parser.parse_args()
    in_file = args.po_file

    if not os.path.exists(in_file):
        sys.stderr.write(f"Can't read file {in_file}")
        sys.exit(1)

    path, ext = os.path.splitext(in_file)
    out_file = f'{path}.ts'

    convert_po_to_ts(in_file, out_file, lang=args.language)
