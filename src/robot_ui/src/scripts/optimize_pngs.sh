#!/usr/bin/env bash
if [ ! "$BASH_VERSION" ]; then
    echo "Warning: this script should be executed with bash"
    exec /bin/bash "$0"
fi
cd "$(dirname "${BASH_SOURCE[0]}")" || exit

cd ../robot_ui/icons/ || exit
find . -name "*.png" -type f -exec mogrify {} \+
find . -name "*.png" -type f -exec optipng {} \+
