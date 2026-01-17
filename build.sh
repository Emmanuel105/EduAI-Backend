#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create cache table for sessions (if using database sessions)
python manage.py createcachetable || true
