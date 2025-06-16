#!/usr/bin/env bash
if [ ! "$BASH_VERSION" ]; then
    echo "Warning: this script should be executed with bash"
    exec /bin/bash "$0"
fi
cd "$(dirname "${BASH_SOURCE[0]}")" || exit

cd ../robot_ui/icons/ || exit

for i in svg/*; do
    input="$i"
    output="png/$(basename "${i%.*}").png"
    echo "converting $input to $output"
    rsvg-convert $input -o $output
done
