#!/usr/bin/env bash
# Capture tank data, then upload it. Runs both steps with the project venv.
set -e

cd "$(dirname "$0")"

PY="./.venv/bin/python3"
if [ ! -x "$PY" ]; then
    # Fall back to system python if the venv is missing
    PY="python3"
fi

"$PY" capture.py
sleep 10
"$PY" upload.py
