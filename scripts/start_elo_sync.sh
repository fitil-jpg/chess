#!/bin/bash
# Start script for ELO synchronization service

set -e

# Create necessary directories
mkdir -p /app/data /app/logs /app/ratings

# Set default environment variables if not provided
export LICHESS_TOKEN=${LICHESS_TOKEN:-""}
export CHESSCOM_USERNAME=${CHESSCOM_USERNAME:-""}
export CHESSCOM_PASSWORD=${CHESSCOM_PASSWORD:-""}
export RATINGS_FILE=${RATINGS_FILE:-"/app/data/ratings.json"}
export CONFIG_FILE=${CONFIG_FILE:-"/app/data/sync_config.json"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
export PORT=${PORT:-"8080"}
export HOST=${HOST:-"0.0.0.0"}

# Check if required credentials are provided
if [ -z "$LICHESS_TOKEN" ] && [ -z "$CHESSCOM_USERNAME" ]; then
    echo "Warning: No platform credentials provided. ELO sync will be limited to local operations."
fi

# Start the ELO sync service
echo "Starting ELO synchronization service..."
echo "Configuration:"
echo "  Lichess Token: ${LICHESS_TOKEN:+[PROVIDED]}"
echo "  Chess.com Username: ${CHESSCOM_USERNAME:-[NOT SET]}"
echo "  Ratings File: $RATINGS_FILE"
echo "  Config File: $CONFIG_FILE"
echo "  Log Level: $LOG_LEVEL"
echo "  Host: $HOST"
echo "  Port: $PORT"

exec python /app/scripts/elo_sync.py