#!/usr/bin/env bash
uvicorn server.main:app \
  --reload \
  --reload-dir server \
  --reload-dir core \
  --host 0.0.0.0 \
  --port 8000