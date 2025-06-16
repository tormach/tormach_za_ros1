from robot_ui.pathpilot.robot.program import MdiHistory


def test_append_command_appends_command_to_mdi_history():
    history = MdiHistory()

    history.appendCommand("QvAL")

    assert history.mdiHistory[-1] == "QvAL"


def test_new_command_is_only_added_once():
    history = MdiHistory(mdi_history=["h2aQOUX", "Ol5So0J2"])

    history.appendCommand("h2aQOUX")

    assert history.mdiHistory.count("h2aQOUX") == 1


def test_new_command_is_added_at_the_end_of_recent_files():
    history = MdiHistory(mdi_history=["napg8", "2PBMw6", "QAtWVxW"])

    history.appendCommand("2PBMw6")

    assert history.mdiHistory[-1] == "2PBMw6"


def test_mdi_history_never_grows_bigger_than_maximum_size_oldest_is_discarded():
    history = MdiHistory(maximum_count=2, mdi_history=["z173K8", "5V09qkB8"])

    history.appendCommand("19gFE")

    assert len(history.mdiHistory) == 2
    assert history.mdiHistory[-1] == "19gFE"


def test_mdi_history_is_cleared_correctly():
    history = MdiHistory(mdi_history=["bJ99", "v4z"])

    history.clear()

    assert len(history.mdiHistory) == 0


def test_empty_command_is_ignored():
    history = MdiHistory()

    history.appendCommand("lKJ")
    history.appendCommand("")

    assert len(history.mdiHistory) == 1
