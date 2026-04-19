#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"
cd src/api
uvicorn servidor:app --host 0.0.0.0 --port ${PORT:-8000}
