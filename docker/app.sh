#!/bin/bash

echo "Waiting for Postgres to be ready..."
while ! nc -z db 5432; do
  sleep 3
done

echo "Postgres is ready. Applying migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI app..."
cd src
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000