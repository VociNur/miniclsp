#!/bin/sh
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
exec "$DIR/.venv/bin/python" "$DIR/MiniCLsp.py" "$@"

