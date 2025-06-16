import pytest
from pytest_mock import mocker  # noqa F401

from robot_ui.pathpilot.controls import tool_tip_manager
from robot_ui.pathpilot.controls import ToolTipInfo


@pytest.fixture  # noqa F811
def patch_tool_tip_manager(mocker):  # noqa F811
    tool_tip_manager.ToolTipManager._instance = None
    mocker.patch.object(tool_tip_manager, '_ToolTipManager')
    return tool_tip_manager._ToolTipManager()


@pytest.fixture
def info(patch_tool_tip_manager):
    info = ToolTipInfo()
    info.itemId = 'foo'
    info._data = tool_tip_manager.ToolTipData(
        longtext_id='PY0HJ', images=["collery.jpg", "conia.png"]
    )
    return info


def test_prepare_body_text_replaces_img_with_id_by_url(info):
    raw_text = 'Foo bar<br><img>1</img>\n< img>2</img>'

    text = info.prepareBodyText(raw_text)

    assert (
        text
        == "Foo bar<br><img src=\"image://toolTipImageProvider/collery.jpg\"></img>\n"
        "<img src=\"image://toolTipImageProvider/conia.png\"></img>"
    )


def test_prepare_body_text_with_img_id_which_does_not_exist_returns_string_as_is(
    info,
):
    raw_text = 'band guess<br>< img>3</img> '

    text = info.prepareBodyText(raw_text)

    assert text == 'band guess<br>< img>3</img> '


def test_prepare_body_text_replace_double_at_with_short_text(info):
    raw_text = '<b>@@</b> ditch'

    text = info.prepareBodyText(raw_text, "probable")

    assert text == '<b>probable</b> ditch'
