"""Handler functions for processing the instances of pathpilot_versions
module objects in the PathPilot Robot Launcher code

This should limit the exposure of the Version type
"""

from pp_ros_launch.image.pathpilot_versions import Version
from PySide6.QtCore import QObject, QLocale


def get_version(v: Version, qobject: QObject) -> str:
    if getattr(v, 'version', None) is None:
        return qobject.tr('Unknown version')
    _version = str(v.version)
    if v.codename is None:
        _version = f'{_version}+{v.git_revision if v.git_revision is not None else qobject.tr("Unknown SHA")}'
    return str(_version)


def get_codename(v: Version, qobject: QObject) -> str:
    if getattr(v, 'codename', None) is None:
        return qobject.tr('Unofficial release')
    return str(v.codename)


def get_description(v: Version, qobject: QObject) -> str:
    if getattr(v, 'description', None) is None:
        return qobject.tr('No description provided')
    return str(v.description)


def get_creation_date(v: Version, qobject: QObject) -> str:
    if getattr(v, 'publish_time', None) is None:
        return qobject.tr('No creation date provided')
    # TODO: How this will intervene with different Qtranslators loaded at
    #       at runtime and can I somehow get the QTranslator.language()
    #       statically to use in place of QLocale.system().name()?
    return QLocale.system().toString(v.publish_time.date())


def get_changelog(v: Version, qobject: QObject) -> str:
    if getattr(v, 'changelog', None) is None:
        return qobject.tr('Version has no public changelog')
    return str(v.changelog)


def get_eula(v: Version, qobject: QObject) -> str:
    if getattr(v, 'eula', None) is None:
        return qobject.tr(
            'This is internal developer version. No EULA is provided!'
        )
    return str(v.eula)


def get_channel_name(version: Version) -> str:
    if getattr(version, 'channel_name', None) is None:
        raise RuntimeError('Invalid PathPilot Version object!')
    return str(version.channel_name)
