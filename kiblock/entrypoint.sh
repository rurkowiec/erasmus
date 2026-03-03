#!/bin/bash
set -e

echo "Starting KiBlock application..."

# Create data directory if it doesn't exist
mkdir -p /app/data

# Move database to persistent volume if not already there
if [ -f "/app/db.sqlite3" ] && [ ! -f "/app/data/db.sqlite3" ]; then
    echo "Moving database to persistent volume..."
    mv /app/db.sqlite3 /app/data/db.sqlite3
fi

# Create symlink to database in data volume
if [ ! -f "/app/db.sqlite3" ] && [ -f "/app/data/db.sqlite3" ]; then
    ln -s /app/data/db.sqlite3 /app/db.sqlite3
fi

# If database doesn't exist at all, create it
if [ ! -f "/app/data/db.sqlite3" ]; then
    echo "Creating new database..."
    touch /app/data/db.sqlite3
    ln -s /app/data/db.sqlite3 /app/db.sqlite3
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django development server on port ${PORT:-9025}..."
exec "$@"
