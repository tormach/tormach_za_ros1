#!/usr/bin/env bash
if [ ! "$BASH_VERSION" ]; then
    echo "Warning: this script should be executed with bash"
    exec /bin/bash "$0"
fi
cd "$(dirname "${BASH_SOURCE[0]}")" || exit
cd ../robot_ui || exit

find . -name "*.pyc" -type f -delete
find . -name "*.qmlc" -type f -delete
find . -name "*.jsc" -type f -delete
find . -name "__pycache__" -type d -delete
