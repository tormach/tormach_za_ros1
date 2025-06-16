#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')


import threading  # noqa: E402
import cairo  # noqa: E402
from argparse import ArgumentParser  # noqa: E402
from gi.repository import Gtk  # noqa: E402
from gi.repository import Gdk  # noqa: E402
from gi.repository import GdkPixbuf  # noqa: E402

import webbrowser  # noqa: E402
import pathlib  # noqa: E402
import psutil  # noqa: E402
import secrets  # noqa: E402
import yaml  # noqa: E402


class TormachColors:
    green = "#bad363"
    dark_green = "#9ca93e"
    red = "#e02b27"
    blue = "#263746"
    gray = "#53565a"


class PathPilotSplashScreen(Gtk.Window):
    launcher_search_name = "launcher_ui"
    max_tries = 45  # Timeout in timer restarts
    timer_tick = 1  # Timer interval
    launcher_min_uptime = (
        1.5  # Interval for which the PPR Launcher has to be alive
    )
    css = f"""
    .warning {{background-image: linear-gradient(34deg, transparent 62.66%, {TormachColors.red} 62.66%);}}
    """

    def __init__(self, arguments):
        Gtk.Window.__init__(self)

        self.main_timer: threading.Timer = None
        self.launcher_process = None
        self.tries = 0
        self.failure = False

        self.report_failure = arguments.report_failure if arguments else False

        # Main GTK objects
        self.main_grid = Gtk.Grid()
        self.splash_image_event_box = Gtk.EventBox()
        self.splash_image = Gtk.Image()
        self.close_icon_eventbox = Gtk.EventBox()
        self.close_icon = Gtk.Image()
        gtk_css_provider = Gtk.CssProvider()
        gtk_style_context = Gtk.StyleContext()

        base_path = pathlib.Path(__file__).parent
        # Directory with the splash-screen base images
        # These should have transparent background and be divisible by 25
        # in both axis without remainder
        background_base = base_path / "backgrounds"
        # Each splashscreen image should have link in this document
        # in the format:
        # image_stem: link_to_webpage
        link_map = background_base / "links.yaml"
        close_icon_path = base_path / "icons" / "close.svg"

        # Center on the screen
        self.set_position(Gtk.WindowPosition.CENTER)
        # Do not show the standard window border with controls
        self.set_decorated(False)
        # Always keep on top
        self.set_keep_above(True)
        # Do not display the window in task bar
        self.set_skip_taskbar_hint(True)
        # Do not display the window in pager (virtual desktops)
        self.set_skip_pager_hint(True)
        # Do not send automatic startup notification
        self.set_auto_startup_notification(False)

        #
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.set_app_paintable(True)
        self.connect('draw', self.draw)

        gtk_style_context.add_provider_for_screen(
            screen, gtk_css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Load the CSS
        gtk_css_provider.load_from_data(PathPilotSplashScreen.css.encode())

        if not background_base.is_dir():
            raise ValueError(f"Directory {background_base} does not exist!")

        if not link_map.is_file():
            raise ValueError(f"File {link_map} does not exist!")

        backgrounds = list(background_base.glob("*.png"))

        links = dict()
        with open(link_map) as file:
            links = yaml.safe_load(file)

        splash_image_path = secrets.choice(backgrounds)

        self.splash_link = links.get(
            splash_image_path.stem, "https://tormach.com"
        )

        self.add(self.main_grid)

        self.main_grid.set_row_homogeneous(True)
        self.main_grid.set_column_homogeneous(True)

        self.splash_image_event_box.add(self.splash_image)

        self.splash_image.set_from_file(str(splash_image_path))

        # The Gtk.Grid should have a panel 25x25
        splash_image_width = self.splash_image.get_pixbuf().get_width()
        splash_image_height = self.splash_image.get_pixbuf().get_height()
        splash_image_columns = splash_image_width / 25
        splash_image_rows = splash_image_height / 25

        self.main_grid.attach(
            self.splash_image_event_box,
            0,
            0,
            splash_image_columns,
            splash_image_rows,
        )

        # Close icon a bit smaller than 2x2 panels on the grid
        close_icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(close_icon_path), -1, 40, True
        )

        self.close_icon.set_from_pixbuf(close_icon_pixbuf)

        self.close_icon_eventbox.add(self.close_icon)

        self.splash_image_event_box.connect(
            "enter-notify-event", self.mouse_enter
        )
        self.splash_image_event_box.connect(
            "leave-notify-event", self.mouse_leave_splash
        )
        self.splash_image_event_box.connect(
            "button-press-event", self.open_site
        )

        self.close_icon_eventbox.connect(
            "button-press-event", lambda *_: self.get_application().quit()
        )
        self.close_icon_eventbox.connect(
            "enter-notify-event", self.mouse_enter, True
        )

        self.main_grid.attach(
            self.close_icon_eventbox, splash_image_columns - 2, 0, 2, 2
        )

        self.set_app_paintable(True)
        self.show_all()

        # shoe_all() really shows all, but the close icon should not be
        # show at start-time
        self.close_icon_eventbox.set_visible(False)

        self.schedule_timer()

    def draw(self, widget: Gtk.Widget, context) -> None:
        context.set_source_rgba(0, 0, 0, 0)
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)

    def set_widget_cursor(
        self, widget: Gtk.Widget, type: Gdk.CursorType
    ) -> None:
        window = widget.get_window()
        if window.get_cursor() != type:
            window.set_cursor(Gdk.Cursor(type))

    def mouse_enter(self, widget, data, always: bool = False) -> None:
        if always or not self.failure:
            self.set_widget_cursor(widget, Gdk.CursorType.HAND1)

    def mouse_leave_splash(self, widget, _) -> None:
        self.set_widget_cursor(widget, Gdk.CursorType.ARROW)

    def open_site(self, *_) -> None:
        if not self.failure:
            webbrowser.open(self.splash_link, new=0, autoraise=True)

    def get_launcher_process(self) -> None:
        try:
            all_processes = psutil.process_iter(["pid", "cmdline"])
            for p in all_processes:
                for arg in p.cmdline():
                    if PathPilotSplashScreen.launcher_search_name in arg:
                        self.launcher_process = p
        except psutil.Error:
            return

    def check_launcher_process(self) -> bool:
        try:
            if (
                self.launcher_process.is_running()
                and self.launcher_process.status()
                in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]
            ):
                return True
        except psutil.Error:
            pass
        return False

    def schedule_timer(self, interval: int = None) -> None:
        self.main_timer = threading.Timer(
            (
                interval
                if interval is not None
                else PathPilotSplashScreen.timer_tick
            ),
            self.timer_expired,
        )
        self.main_timer.start()

    def signal_failure(self) -> None:
        self.failure = True
        self.mouse_leave_splash(self.splash_image_event_box, None)
        self.main_timer.cancel()
        if self.report_failure:
            self.main_grid.get_style_context().add_class("warning")
            self.close_icon_eventbox.set_visible(True)
        else:
            self.get_application().quit()

    def signal_success(self) -> None:
        self.main_timer.cancel()  # Should not be running anyway at this point in time
        self.get_application().quit()

    def timer_expired(self) -> None:
        self.tries += 1
        if self.tries < PathPilotSplashScreen.max_tries:
            if not self.launcher_process:
                self.get_launcher_process()
                self.schedule_timer(
                    PathPilotSplashScreen.launcher_min_uptime
                    if self.launcher_process is not None
                    else PathPilotSplashScreen.timer_tick
                )
            else:
                if not self.check_launcher_process():
                    self.signal_failure()
                else:
                    self.signal_success()
        else:
            self.signal_failure()


def on_activate(app, arguments):
    splash = PathPilotSplashScreen(arguments)
    splash.set_application(app)


def run():
    parser = ArgumentParser()
    parser.add_argument(
        '-f',
        '--failure-signaling',
        help='',
        action='store_true',
        default=False,
        dest='report_failure',
    )

    args = parser.parse_args()

    app = Gtk.Application(
        application_id='com.tormach.pathpilot.robot.starter.splash'
    )
    app.connect('activate', on_activate, args)
    app.run(None)


if __name__ == "__main__":
    run()
