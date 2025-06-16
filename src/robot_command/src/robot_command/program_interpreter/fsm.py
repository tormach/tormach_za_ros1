class FSM:
    """
    Finite State Machine (FSM) implementation of the program interpreter.

    For visualizing the FSM, see fsm_visualizer.py.
    """

    __slots__ = ()
    # states
    stopped_state = 'stopped'  # program loaded, but not running
    idle_state = 'idle'  # no program loaded
    running_state = 'running'  # program running
    running_step_state = 'running_step'  # program running single step
    preparing_on_paused_state = 'preparing_on_paused'  # state preparing state between running and paused
    running_on_paused_state = (
        'running_on_paused'  # state between running and paused
    )
    preparing_on_paused_active_state = 'preparing_on_paused_active'  # state preparing state between running and paused active
    running_on_paused_active_state = (
        'running_on_paused_active'  # state between running and paused active
    )
    preparing_on_stopped_state = 'preparing_on_stopped'  # state preparing state between running and stopped
    running_on_stopped_state = (
        'running_on_stopped'  # state between running and stopped
    )
    preparing_on_errored_state = 'preparing_on_errored'  # state preparing state between running and errored
    running_on_errored_state = (
        'running_on_errored'  # state between running and errored
    )
    paused_state = 'paused'  # program paused, no jogging
    paused_active_state = 'paused_active'  # program paused, jog allowed
    mdi_paused_in_idle_state = 'mdi_paused_in_idle'
    mdi_paused_in_stopped_state = 'mdi_paused_in_stopped'
    mdi_running_in_idle_state = 'mdi_running_in_idle'
    mdi_running_in_stopped_state = 'mdi_running_in_stopped'
    errored_state = 'errored'
    errored_in_idle_state = 'errored_in_idle'
    error_while_loading_state = 'errored_while_loading'
    paused_states = (
        paused_state,
        paused_active_state,
        mdi_paused_in_idle_state,
        mdi_paused_in_stopped_state,
    )
    pre_paused_states = (
        preparing_on_paused_state,
        preparing_on_paused_active_state,
    )
    # events
    init_event = 'init'
    load_event = 'load'
    unload_event = 'unload'
    start_event = 'start'
    stop_event = 'stop'
    pause_event = 'pause'
    pause_active_event = 'pause_active'
    next_event = 'next'
    update_event = 'update'
    cont_event = 'cont'
    mdi_event = 'mdi'
    runtime_error_event = 'runtime_error'
    load_error_event = 'load_error'
    step_event = 'step'
    reload_check_event = 'reload_check'
    # fsm
    fsm = dict(
        initial={'state': idle_state, 'event': init_event, 'defer': True},
        # fmt: off
        events=[
            {'name': load_event, 'src': [idle_state, stopped_state, error_while_loading_state], 'dst': stopped_state},
            {'name': unload_event, 'src': [stopped_state, error_while_loading_state], 'dst': idle_state},
            {'name': start_event, 'src': stopped_state, 'dst': running_state},
            {'name': stop_event, 'src': [running_state, running_step_state, paused_state, paused_active_state,
                                         running_on_paused_state, running_on_paused_active_state], 'dst': preparing_on_stopped_state},
            {'name': stop_event, 'src': [mdi_running_in_stopped_state, mdi_paused_in_stopped_state], 'dst': stopped_state},
            {'name': stop_event, 'src': [errored_state, running_on_stopped_state], 'dst': stopped_state},
            {'name': stop_event, 'src': running_on_errored_state, 'dst': errored_state},
            {'name': stop_event, 'src': [mdi_running_in_idle_state, mdi_paused_in_idle_state, error_while_loading_state], 'dst': idle_state},
            {'name': stop_event, 'src': errored_in_idle_state, 'dst': idle_state},
            {'name': next_event, 'src': preparing_on_stopped_state, 'dst': running_on_stopped_state},
            {'name': next_event, 'src': running_on_stopped_state, 'dst': stopped_state},
            {'name': next_event, 'src': preparing_on_errored_state, 'dst': running_on_errored_state},
            {'name': next_event, 'src': running_on_errored_state, 'dst': errored_state},
            {'name': next_event, 'src': preparing_on_paused_state, 'dst': running_on_paused_state},
            {'name': next_event, 'src': running_on_paused_state, 'dst': paused_state},
            {'name': next_event, 'src': preparing_on_paused_active_state, 'dst': running_on_paused_active_state},
            {'name': next_event, 'src': running_on_paused_active_state, 'dst': paused_active_state},
            {'name': pause_event, 'src': [running_state, running_step_state], 'dst': preparing_on_paused_state},
            {'name': pause_event, 'src': mdi_running_in_idle_state, 'dst': mdi_paused_in_idle_state},
            {'name': pause_event, 'src': mdi_running_in_stopped_state, 'dst': mdi_paused_in_stopped_state},
            {'name': pause_active_event, 'src': [running_state, running_step_state], 'dst': preparing_on_paused_active_state},
            {'name': cont_event, 'src': [paused_state, paused_active_state], 'dst': running_state},
            {'name': cont_event, 'src': mdi_paused_in_idle_state, 'dst': mdi_running_in_idle_state},
            {'name': cont_event, 'src': mdi_paused_in_stopped_state, 'dst': mdi_running_in_stopped_state},
            {'name': step_event, 'src': [paused_state, paused_active_state, running_state], 'dst': running_step_state},
            {'name': update_event, 'src': running_state, 'dst': running_state},
            {'name': update_event, 'src': running_step_state, 'dst': running_step_state},
            {'name': update_event, 'src': mdi_running_in_idle_state, 'dst': mdi_running_in_idle_state},
            {'name': update_event, 'src': mdi_running_in_stopped_state, 'dst': mdi_running_in_stopped_state},
            {'name': update_event, 'src': running_on_paused_state, 'dst': running_on_paused_state},
            {'name': update_event, 'src': running_on_paused_active_state, 'dst': running_on_paused_active_state},
            {'name': update_event, 'src': running_on_stopped_state, 'dst': running_on_stopped_state},
            {'name': update_event, 'src': running_on_errored_state, 'dst': running_on_errored_state},
            {'name': mdi_event, 'src': idle_state, 'dst': mdi_running_in_idle_state},
            {'name': mdi_event, 'src': stopped_state, 'dst': mdi_running_in_stopped_state},
            {'name': runtime_error_event, 'src': [running_state, running_step_state, running_on_paused_state,
                                                  running_on_paused_active_state], 'dst': preparing_on_errored_state},
            {'name': runtime_error_event, 'src': [mdi_running_in_stopped_state, running_on_errored_state,
                                                  running_on_stopped_state], 'dst': errored_state},
            {'name': runtime_error_event, 'src': [mdi_running_in_idle_state], 'dst': errored_in_idle_state},
            {'name': load_error_event, 'src': [idle_state, stopped_state], 'dst': error_while_loading_state},
            {'name': reload_check_event, 'src': idle_state, 'dst': idle_state},
            {'name': reload_check_event, 'src': stopped_state, 'dst': stopped_state},
        ],
        # fmt: on
    )
