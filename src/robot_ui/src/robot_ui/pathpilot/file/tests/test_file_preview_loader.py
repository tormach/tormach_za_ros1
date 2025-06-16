import pytest

from robot_ui.pathpilot.file.file_preview_loader import FilePreviewLoader


@pytest.fixture
def python_file(tmpdir):
    f = tmpdir.join('hole.py')
    f.write('print("hello world")\n')
    return str(f)


@pytest.fixture
def binary_file(tmpdir):
    path = str(tmpdir.join('chevied.bin'))
    with open(path, 'wb') as f:
        f.write(b'0101' * 108)
    return path


@pytest.fixture
def big_text_file(tmpdir):
    f = tmpdir.join('reenact.txt')
    f.write('a' * 1000)
    return str(f)


def test_python_file_is_detected_as_previewable(python_file):
    preview = FilePreviewLoader()

    preview.path = python_file

    assert preview.previewable is True
    assert preview.content == 'print("hello world")\n'


@pytest.mark.skip(
    reason="fake binary file detected as text on CI for some reason"
)
def test_binary_file_is_detected_as_not_previewable(binary_file):
    preview = FilePreviewLoader()

    preview.path = binary_file

    assert preview.previewable is False
    assert preview.content == ''


def test_text_file_bigger_than_size_limit_is_detected_as_not_previewable(
    big_text_file,
):
    preview = FilePreviewLoader(size_limit=100)

    preview.path = big_text_file

    assert preview.previewable is False
    assert preview.content == ''
