#!/bin/bash -xe

cd $(dirname $0)

DRIVENUM=5                                               # Drive to capture
ROBOT_PROGRAM=~/nc_files/robot_programs/movej_flex_j6.py # Robot program to run
OUTPUT_DIR=/tmp/jitter_capture                           # Where to store HAL + ECAT pkt captures

# ROS /robot_command/run_command service values
COMMAND_START=2
COMMAND_STOP=3

# ROS device mgr state_cmd topic values
STATE_STOP=1
STATE_ENABLE=2

capture() {
    TIME=${TIME:-20}
    TAG=${TAG:-${1:-unknown}}

    # Stop program (just in case) & load program
    rosservice call -v /robot_command/run_command $COMMAND_STOP
    rosservice call /robot_command/load_program $ROBOT_PROGRAM

    # Start capturing from HAL
    ../../scripts/halsampler_decode.py \
        --time=$TIME \
        >$OUTPUT_DIR/sampler_${TAG}.csv &
    # Start capturing from EtherCAT bus
    ../../scripts/ecat_pcap_decode.py \
        --conf=../../halfiles/ethercat-za6-ver2.xml \
        --ethercat-pcap --time=$TIME \
        >$OUTPUT_DIR/ecat_${TAG}.csv &
    sleep 1

    # Enable drives, run program for 20 seconds, disable drives
    rostopic pub -1 /hal_io/state_cmd std_msgs/UInt32 $STATE_ENABLE
    rosservice call -v /robot_command/run_command $COMMAND_START
    sleep 20
    rosservice call -v /robot_command/run_command $COMMAND_STOP
    sleep 5
    rostopic pub -1 /hal_io/state_cmd std_msgs/UInt32 $STATE_STOP

    # Wait for capture to complete
    wait
}

merge() {
    TAG=$1
    python3 merge.py \
        --halsampler-csv $OUTPUT_DIR/sampler_${TAG}.csv \
        --halsampler-counter-field counter \
        --ethercat-csv $OUTPUT_DIR/ecat_${TAG}.csv \
        --ethercat-counter-field 0.${DRIVENUM}.60FF-00h.counter \
        --output-csv $OUTPUT_DIR/collated_${TAG}.csv
}

CMD=$1
shift
$CMD $*
