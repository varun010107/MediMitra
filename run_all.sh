#!/usr/bin/env bash
# Starts MediMitra API (8001), TrustSkin-AI API (8000) and the shared frontend (3000).
# Set TRUSTSKIN_DIR if the TrustSkin-AI checkout lives elsewhere.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
TRUSTSKIN_DIR="${TRUSTSKIN_DIR:-$ROOT/../TrustSkin-AI}"
trap 'kill 0' EXIT
(cd "$ROOT" && .venv/bin/python -m uvicorn backend.main:app --port 8001) &
(cd "$TRUSTSKIN_DIR" && "${TRUSTSKIN_PYTHON:-python3}" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000) &
(cd "$ROOT/frontend" && npm run dev) &
wait
