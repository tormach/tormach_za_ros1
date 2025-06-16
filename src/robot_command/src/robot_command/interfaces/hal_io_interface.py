import rospy
from std_msgs.msg import Bool, Float64

IO_NAMESPACE = 'io'


class HalIoInterface:
    def __init__(self):
        self.on_digital_input_update_received = []
        self.on_user_io_update_received = []

        def create_pub_sub(
            topics, values, subs, handler, pubs=None, type_=Bool
        ):
            for i, topic in enumerate(topics):
                nr = i + 1
                rospy.logdebug(f'creating subscriber for {topic}')
                sub = rospy.Subscriber(topic, type_, handler, nr)
                values[nr] = False
                subs.append(sub)
                if pubs is not None:
                    rospy.logdebug(f'creating publisher for {topic}')
                    pub = rospy.Publisher(topic, type_, queue_size=1)
                    pubs[nr] = pub

        self._subs = []
        self._digital_inputs = {}
        digital_in_topics = rospy.get_param(
            f'{IO_NAMESPACE}/digital_in_topics', []
        )
        create_pub_sub(
            digital_in_topics,
            self._digital_inputs,
            self._subs,
            self._on_digital_input_update_received,
        )
        self._digital_outputs = {}
        self._digital_output_pubs = {}
        self._digital_output_subs = {}
        digital_out_topics = rospy.get_param(
            f'{IO_NAMESPACE}/digital_out_topics', []
        )
        create_pub_sub(
            digital_out_topics,
            self._digital_outputs,
            self._subs,
            self._on_digital_output_update_received,
            self._digital_output_pubs,
        )
        self._user_ios = {}
        self._user_io_subs = {}
        user_io_topics = rospy.get_param(f'{IO_NAMESPACE}/user_io_topics', [])
        create_pub_sub(
            user_io_topics,
            self._user_ios,
            self._subs,
            self._on_user_io_update_received,
            type_=Float64,
        )

    @property
    def digital_in_count(self):
        return len(self._digital_inputs)

    @property
    def digital_out_count(self):
        return len(self._digital_outputs)

    @property
    def user_io_count(self):
        return len(self._user_ios)

    def shutdown(self):
        for sub in self._subs:
            sub.unregister()
        # for pub in self._digital_output_pubs.values():
        #    pub.unregister()

    @staticmethod
    def get_digital_input_nr(name):
        return rospy.get_param(f'{IO_NAMESPACE}/digital_in_names/{name}', -1)

    @staticmethod
    def get_digital_output_nr(name):
        return rospy.get_param(f'{IO_NAMESPACE}/digital_out_names/{name}', -1)

    def get_digital_input(self, nr):
        return self._digital_inputs[nr]

    def set_digital_output(self, nr, value):
        self._digital_output_pubs[nr].publish(value)

    def get_digital_output(self, nr):
        return self._digital_outputs[nr]

    def _on_digital_input_update_received(self, msg, nr):
        self._digital_inputs[nr] = msg.data
        for fct in self.on_digital_input_update_received:
            fct(nr, msg.data)

    def _on_digital_output_update_received(self, msg, nr):
        self._digital_outputs[nr] = msg.data

    def _on_user_io_update_received(self, msg, nr):
        self._user_ios[nr] = msg.data
        for fct in self.on_user_io_update_received:
            fct(nr, msg.data)


class HalIoInterfaceSingleton:
    """
    Singleton interface class to HAL IO
    """

    _instance = None

    def __init__(self):
        if not HalIoInterfaceSingleton._instance:
            HalIoInterfaceSingleton._instance = HalIoInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)
