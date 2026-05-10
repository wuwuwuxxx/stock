#!/usr/bin/env bash
set -Eeuo pipefail

LOG_DIR="data"
FAILED_FILE="${LOG_DIR}/update_failed.txt"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log "FATAL: update.sh exited with code $exit_code on line $BASH_LINENO"
    fi
    exec 2>&-
    exit $exit_code
}

trap cleanup EXIT ERR

log "Starting stock update pipeline"

if ! python3 -u stock_update.py; then
    log "WARNING: stock_update.py exited non-zero, continuing"
    echo "update_failure: stock_update.py at $(date)" >> "$FAILED_FILE"
fi

if ! python3 -u stock_analysis.py; then
    log "WARNING: stock_analysis.py exited non-zero, continuing"
    echo "analysis_failure: stock_analysis.py at $(date)" >> "$FAILED_FILE"
fi

log "Stock update pipeline completed"
