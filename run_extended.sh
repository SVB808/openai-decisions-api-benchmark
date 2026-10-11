#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi
if [ -z "${OPENAI_API_KEY:-}" ]; then
  read -r -s -p 'OpenAI API key (hidden): ' OPENAI_API_KEY
  echo
  export OPENAI_API_KEY
fi
printf '
This performs exactly 400 paid requests (200 examples x 2 APIs), no retries.
'
printf 'No automatic safeguards can guarantee total charges. Check your Platform balance first.
'
read -r -p 'Type RUN to authorize the 400 paid requests: ' consent
if [ "$consent" != RUN ]; then echo 'Cancelled: 0 requests sent.'; exit 0; fi
.venv/bin/python benchmark_extended.py --limit 200 --max-paid-calls 400
