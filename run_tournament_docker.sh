#!/usr/bin/env bash
set -euo pipefail

# Run round-robin tournament across all default agents, Bo3, 3|0, print live status
# Outputs under ./output/tournaments/<timestamp> and logs to container console

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

# Build images (if needed) and run the tournament service
exec docker compose run --rm tournament
