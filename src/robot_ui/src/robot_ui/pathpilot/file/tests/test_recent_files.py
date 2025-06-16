from robot_ui.pathpilot.file import RecentFiles


def test_items_saves_current_file_in_recent_files():
    recenf = RecentFiles()

    recenf.currentPath = '/tmp/foo.py'

    assert '/tmp/foo.py' in recenf.recentPaths


def test_new_path_is_only_added_once():
    recentf = RecentFiles(recent_paths=['/tmp/bar.py', '/home/fred/goo.py'])

    recentf.currentPath = '/tmp/bar.py'

    assert recentf.recentPaths.count('/tmp/bar.py') == 1


def test_new_path_is_added_at_end_of_recent_files():
    recentf = RecentFiles(
        recent_paths=[
            'first_program.py',
            'second_program.py',
            'third_program.py',
        ]
    )

    recentf.currentPath = 'second_program.py'

    assert recentf.recentPaths[-1] == 'second_program.py'


def test_recentf_never_grows_bigger_than_maximum_size_oldest_is_discarded():
    recentf = RecentFiles(
        maximum_count=2, recent_paths=['first_program.py', 'second_program.py']
    )

    recentf.currentPath = 'third_program.py'

    assert len(recentf.recentPaths) == 2
    assert recentf.recentPaths[-1] == 'third_program.py'


def test_recentf_is_cleared_correctly():
    recentf = RecentFiles(recent_paths=['second.py', 'third.py'])

    recentf.clear()

    assert len(recentf.recentPaths) == 0


def test_empty_path_is_ignored():
    recentf = RecentFiles()

    recentf.currentPath = 'first.py'
    recentf.currentPath = ''

    assert len(recentf.recentPaths) == 1


def test_path_outside_of_home_path_is_ignored():
    recentf = RecentFiles()
    recentf.homePath = '/foo/bar'

    recentf.currentPath = '/foo/bar/space.py'
    recentf.currentPath = '/foo/bi/bla.py'

    assert len(recentf.recentPaths) == 1
    assert recentf.recentPaths[0] == '/foo/bar/space.py'


def test_filenames_are_extracted_from_recent_paths():
    recentf = RecentFiles(
        recent_paths=[
            '/tmp/foo/program1.py',
            '/home/alex/code.py',
            'move_home.py',
        ]
    )

    assert recentf.recentFiles == ['program1.py', 'code.py', 'move_home.py']


def test_non_existent_files_are_removed_when_setting_recent_paths(tmpdir):
    recentf = RecentFiles()
    program1 = tmpdir.join('goof.py')
    program1.write('0PZ02')
    program2 = tmpdir.join('hgwy.py')
    program2.write('AJ016BW')
    paths = [str(program1), '/MG6YC76/ZF6E9', str(program2)]

    recentf.recentPaths = paths

    assert len(recentf.recentPaths) == 2
    assert recentf.recentPaths == [str(program1), str(program2)]
