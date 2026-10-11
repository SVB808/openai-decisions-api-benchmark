#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo 'Python 3 required: sudo apt update && sudo apt install -y python3 python3-venv'; exit 1; }
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -q -r requirements.txt
if [ -z "${OPENAI_API_KEY:-}" ]; then
  read -r -s -p 'Paste OpenAI API key (hidden): ' OPENAI_API_KEY; echo
  export OPENAI_API_KEY
fi
[ -n "$OPENAI_API_KEY" ] || { echo 'API key missing'; exit 1; }
echo 'Running a small paid API check...'
.venv/bin/python benchmark.py --limit 2 --runs 1 --out smoke_results.csv
.venv/bin/python - <<'PY'
import csv
with open('smoke_results.csv',newline='') as f: rows=list(csv.DictReader(f))
if len(rows)!=4 or any(r['error'] for r in rows):
    raise SystemExit('Smoke test failed; full paid benchmark cancelled. Share errors without your API key.')
PY
echo 'Smoke test passed; running full benchmark...'
.venv/bin/python benchmark.py --runs 3
echo 'Complete. Upload results.csv for analysis.'
