import json
import os
import re

import attr

from PySide6.QtGui import QColor, QFont

from ..base.resource_paths import RESOURCE_PATH

TOOLTIP_FILE_PATH = os.path.join(RESOURCE_PATH, 'tooltips.json')


@attr.s
class ToolTipData:
    body_font = attr.ib(default=QFont())
    body_color = attr.ib(default=QColor())
    header_font = attr.ib(default=QFont())
    header_color = attr.ib(default=QColor())
    long_width = attr.ib(default=100)
    background_color = attr.ib(default=QColor())
    shorttext_id = attr.ib(default='')
    longtext_id = attr.ib(default='')
    images = attr.ib(default=[])


class _ToolTipManager:
    def __init__(self, source_file):
        self._tooltip_data = {}
        self._tooltip_json_mtime = None
        self._font_re = re.compile(r'([^\s]*)="([^"]*)"')
        self._font_family_re = re.compile(r'(.+)\s(\d+)')

        self._header_color = QColor()
        self._header_font = QFont()
        self._body_color = QColor()
        self._body_font = QFont()
        self._background_color = QColor()
        self._long_width = 100

        self._load_tooltips(source_file)

    def _load_tooltips(self, source_file):
        with open(source_file) as datafile:
            self._tooltip_json_mtime = os.stat(source_file).st_mtime
            json_data = json.load(datafile)
        self._tooltip_data = json_data['common']
        self._background_color = QColor(json_data['std_bk_color'])
        self._long_width = int(json_data['std_long_width'])
        self._body_font, self._body_color = self._convert_font_description(
            json_data['std_body_font']
        )
        self._header_font, self._header_color = self._convert_font_description(
            json_data['std_header_font']
        )

    def _convert_font_description(self, string):
        matches = self._font_re.findall(string)
        font_data = {m[0]: m[1] for m in matches}
        match = self._font_family_re.match(font_data['font_desc'])
        family, size = match.group(1), match.group(2)
        return (
            QFont(family, int(size)),
            QColor(font_data.get('foreground', 'black')),
        )

    def get_item_data(self, id_):
        tooltip_data = self._tooltip_data.get(id_, dict())
        data = ToolTipData()
        data.shorttext_id = tooltip_data.get('shorttext_id', '')
        data.longtext_id = tooltip_data.get('longtext_id', '')
        data.images = tooltip_data.get('images', [])
        if 'header_font' in tooltip_data:
            (
                data.header_font,
                data.header_color,
            ) = self._convert_font_description(tooltip_data['header_font'])
        else:
            data.header_font = self._header_font
            data.header_color = self._header_color
        if 'body_font' in tooltip_data:
            data.body_font, data.body_color = self._convert_font_description(
                tooltip_data['body_font']
            )
        else:
            data.body_font = self._body_font
            data.body_color = self._body_color
        if 'bk_color' in tooltip_data:
            data.background_color = QColor(tooltip_data['bk_color'])
        else:
            data.background_color = self._background_color
        data.long_width = int(tooltip_data.get('long_width', self._long_width))
        return data


class ToolTipManager:
    """
    Singleton tooltip manager class accessed by all tool tip info objects.
    """

    _instance = None

    def __init__(self):
        if not ToolTipManager._instance:
            ToolTipManager._instance = _ToolTipManager(
                source_file=TOOLTIP_FILE_PATH
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)
