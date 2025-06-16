#!/usr/bin/env bash
if [ ! "$BASH_VERSION" ]; then
    echo "Warning: this script should be executed with bash"
    exec /bin/bash "$0"
fi
cd "$(dirname "${BASH_SOURCE[0]}")" || exit
SCRIPT_DIR=$(pwd)
cd ../robot_ui/res || exit

python3 ${SCRIPT_DIR}/po_to_ts.py pathpilot_en.po -l en
pyside6-lrelease -idbased pathpilot_en.ts
