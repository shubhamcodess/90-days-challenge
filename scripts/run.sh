#!/bin/sh
# One command for routines: refresh sources -> score -> public export.
set -e
cd "$(dirname "$0")/.."
python3 scripts/collect.py
python3 scripts/score.py
python3 scripts/render_public.py
