import pytest

from PySide6.QtGui import QFont, QColor

from robot_ui.pathpilot.controls.tool_tip_manager import (
    _ToolTipManager,
    ToolTipData,
)


@pytest.fixture
def simple_tooltips_json(tmpdir):
    data = '''\
{
    "std_header_font" : "font_desc=\\"Roboto Condensed 12\\" foreground=\\"black\\"",
    "std_body_font" : "font_desc=\\"Roboto Condensed 10\\" foreground=\\"black\\"",
    "std_long_width": 250,
    "std_bk_color" : "#FFFFFF",
    "common" : {
        "loftsmen": {
            "shorttext_id": "A7JD0",
            "longtext_id": "Z9W8",
            "long_width": 569,
            "bk_color": "#ABCDEF",
            "images": ["mazier.jpg", "ricket.png"]
        },
        "exempted": {
            "shorttext_id": "HSLEKPY",
            "longtext_id": "50WIAFLI"
        }
    }
}
'''
    f = tmpdir.join('tooltips.json')
    f.write(data)
    return str(f)


def test_loading_default_tool_tip_data_works(simple_tooltips_json):
    manager = _ToolTipManager(source_file=simple_tooltips_json)

    data = manager.get_item_data(id_='')
    assert data == ToolTipData(
        body_font=QFont('Roboto Condensed', 10),
        body_color=QColor('black'),
        header_font=QFont('Roboto Condensed', 12),
        header_color=QColor('black'),
        background_color=QColor('white'),
        long_width=250,
        images=[],
        shorttext_id="",
        longtext_id="",
    )


def test_loading_tool_tip_containing_all_fields_returns_complete_entry(
    simple_tooltips_json,
):
    manager = _ToolTipManager(source_file=simple_tooltips_json)

    data = manager.get_item_data(id_='loftsmen')
    assert data == ToolTipData(
        body_font=QFont('Roboto Condensed', 10),
        body_color=QColor('black'),
        header_font=QFont('Roboto Condensed', 12),
        header_color=QColor('black'),
        background_color=QColor('#ABCDEF'),
        long_width=569,
        images=["mazier.jpg", "ricket.png"],
        shorttext_id="A7JD0",
        longtext_id="Z9W8",
    )


def test_loading_tool_tip_containing_only_text_ids_returns_entry_with_defaults(
    simple_tooltips_json,
):
    manager = _ToolTipManager(source_file=simple_tooltips_json)

    data = manager.get_item_data(id_='exempted')
    assert data == ToolTipData(
        body_font=QFont('Roboto Condensed', 10),
        body_color=QColor('black'),
        header_font=QFont('Roboto Condensed', 12),
        header_color=QColor('black'),
        background_color=QColor('white'),
        long_width=250,
        images=[],
        shorttext_id="HSLEKPY",
        longtext_id="50WIAFLI",
    )
