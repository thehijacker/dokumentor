#!/bin/bash
set -e

# Create directories if they don't exist
mkdir -p data documents watch_folder logs uploads

# Initialize database
python -c "from backend.database import init_db; init_db()"

# Execute the main command
exec "$@"
