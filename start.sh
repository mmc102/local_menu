#!/bin/sh
set -e  # Exit immediately if a command exits with a non-zero status

# Run Alembic migrations
alembic upgrade head

# Start FastAPI
uvicorn main:app --host 0.0.0.0 --port 8010
