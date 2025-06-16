import re
import shutil
import subprocess
import tempfile
import argparse
import contextlib
import rospy
import pydot
from std_msgs.msg import String

from robot_command.program_interpreter.fsm import FSM


def draw_fsm(highlight_tuples=[]):
    def format_state(state):
        return state.replace('_', '\n')

    def interpolate_color(base_color, target_color, opacity):
        """Interpolate between base_color and target_color based on opacity."""
        return tuple(
            int(base * (1 - opacity) + target * opacity)
            for base, target in zip(base_color, target_color)
        )

    def create_state_node(name, width=1.5, height=1.2, highlight_opacity=None):
        if highlight_opacity is not None:
            # Interpolate between white (255, 255, 255) and yellow (255, 255, 0)
            color = interpolate_color(
                (255, 255, 255), (255, 255, 0), highlight_opacity
            )
            fillcolor = "#{:02x}{:02x}{:02x}".format(*color)
            return pydot.Node(
                format_state(name),
                shape='rectangle',
                width=str(width),
                height=str(height),
                style='"filled,rounded"',
                fillcolor=fillcolor,
            )
        else:
            return pydot.Node(
                format_state(name),
                shape='rectangle',
                width=str(width),
                height=str(height),
                style='rounded',
            )

    def create_event_edge(src, dst, name, highlight_opacity=None):
        if highlight_opacity is not None:
            # Interpolate between black (0, 0, 0) and red (255, 0, 0)
            color = interpolate_color((0, 0, 0), (255, 0, 0), highlight_opacity)
            edge_color = "#{:02x}{:02x}{:02x}".format(*color)
            return pydot.Edge(
                format_state(src),
                format_state(dst),
                label=name,
                color=edge_color,
            )
        else:
            return pydot.Edge(format_state(src), format_state(dst), label=name)

    # Create the graph object
    graph = pydot.Dot(graph_type='digraph', splines='true', rankdir='TB')

    # create initial node
    graph.add_node(pydot.Node('initial', shape='point'))
    graph.add_edge(
        create_event_edge(
            'initial',
            FSM.fsm['initial']['state'],
            FSM.fsm['initial']['event'],
        )
    )

    # Extract highlighted states and their opacities from the tuples
    highlighted_states_opacity = {
        dst: opacity for _, _, dst, opacity in highlight_tuples
    }
    highlighted_events_opacity = {
        (name, src, dst): opacity
        for name, src, dst, opacity in highlight_tuples
    }

    # Add nodes to the graph for each state
    for event in FSM.fsm['events']:
        src = event['src']
        dst = event['dst']
        name = event['name']
        if isinstance(src, list):
            for s in src:
                graph.add_node(
                    create_state_node(
                        s,
                        highlight_opacity=highlighted_states_opacity.get(s),
                    )
                )
                graph.add_edge(
                    create_event_edge(
                        s,
                        dst,
                        name,
                        highlighted_events_opacity.get((name, s, dst)),
                    )
                )
        else:
            graph.add_node(
                create_state_node(
                    src,
                    highlight_opacity=highlighted_states_opacity.get(src),
                )
            )
            if isinstance(dst, list):
                for d in dst:
                    graph.add_node(
                        create_state_node(
                            d,
                            highlight_opacity=highlighted_states_opacity.get(d),
                        )
                    )
                    graph.add_edge(
                        create_event_edge(
                            src,
                            d,
                            name,
                            highlighted_events_opacity.get((name, src, d)),
                        )
                    )
            else:
                graph.add_node(
                    create_state_node(
                        dst,
                        highlight_opacity=highlighted_states_opacity.get(dst),
                    )
                )
                graph.add_edge(
                    create_event_edge(
                        src,
                        dst,
                        name,
                        highlighted_events_opacity.get((name, src, dst)),
                    )
                )

    return graph


def write_graph():
    graph = draw_fsm()

    # write the graph to a file and show it
    with tempfile.TemporaryDirectory() as path:
        if shutil.which('xdot'):
            graph.write(f'{path}/fsm.dot')
            subprocess.call(['xdot', f'{path}/fsm.dot'])
        else:
            graph.write_png(f'{path}/fsm.png')
            subprocess.call(['xdg-open', f'{path}/fsm.png'])


class FSMVisualizer:
    FSM_STATE_TOPIC = '/robot_command/debug/fsm_state'
    MAX_EVENT_HISTORY = 4

    def __init__(self):
        import xdot
        from gi.repository import Gtk

        self._state_sub = None
        self._events = ['stop']
        self.window = xdot.DotWindow()
        # self.window.resize(800, 600)
        self.window.connect('destroy', Gtk.main_quit)
        self._show_fsm()

    def start(self):
        self._state_sub = rospy.Subscriber(
            self.FSM_STATE_TOPIC, String, self._on_state_received
        )

    def spin(self):
        from gi.repository import Gtk

        Gtk.main()

    @staticmethod
    def _extract_data(s):
        pattern = r"(.*?):\s*(.*?)\s*->\s*(.*)"
        if match := re.match(pattern, s):
            event, source, destination = match.groups()
            return event, source, destination
        else:
            return None

    def _on_state_received(self, msg):
        event, source, destination = self._extract_data(msg.data)
        self._events.append((event, source, destination, 1.0))
        if len(self._events) > self.MAX_EVENT_HISTORY:
            self._events.pop(0)
        # change the opacity of the older events
        for i in range(len(self._events) - 1):
            self._events[i] = (
                *self._events[i][:3],
                (i + 1) / len(self._events),
            )
        self._show_fsm(highlight_tuples=self._events)

    def _show_fsm(self, highlight_tuples=[]):
        xdot_data = draw_fsm(highlight_tuples=highlight_tuples)
        self.window.set_dotcode(xdot_data.create(prog='dot', format='xdot'))
        self.window.show_all()

    def stop(self):
        self._state_sub.unregister()


if __name__ == '__main__':
    # use argparse to fetch the -d --dynamic option, default true
    # if true, then subscribe to the FSM state topic
    parser = argparse.ArgumentParser(description="FSM state visualizer")
    parser.add_argument(
        '-s',
        '--static',
        action='store_true',
        default=False,
        help="Draw the FSM and exit.",
    )
    args = parser.parse_args()

    if not args.static:
        rospy.init_node('fsm_visualizer', anonymous=True)
        rospy.loginfo("Starting the FSM visualizer...")

        rospy.loginfo("  enabling robot_command debug mode")
        rospy.set_param('/robot_command/debug', True)

        rospy.loginfo("  and subscribing to the FSM state topic")
        rospy.loginfo(
            "  you may need to restart the robot_command interpreter for the debug mode to take effect"
        )

        fsm_visualizer = FSMVisualizer()
        fsm_visualizer.start()
        with contextlib.suppress(KeyboardInterrupt):
            fsm_visualizer.spin()
        fsm_visualizer.stop()

    else:
        print("Drawing the FSM...")
        write_graph()
