#!/bin/bash

# Function to kill all background processes and cleanup
cleanup() {
    echo "Stopping alembic migrations and cleaning up..."
    # Kill all background processes started by this script
    kill $(jobs -p) 2>/dev/null || true
    wait
}

# Trap SIGINT (Ctrl+C) and call cleanup function
trap cleanup SIGINT

# Main function to execute the alembic migration process
main() {
    echo "Running alembic migrations..."

    # Step 1: Generate a random migration message
    MIGRATION_ID=$(uuidgen)
    MIGRATION_MSG="Migration_$MIGRATION_ID"
    echo "Generating new migration with message: $MIGRATION_MSG"

    # Step 2: Autogenerate a new migration with the random message
    if ! alembic revision --autogenerate -m "Migration - $MIGRATION_MSG"; then
        echo "Failed to generate migration"
        exit 1
    fi

    # Step 3: Apply the migration and upgrade to the latest (head)
    echo "Upgrading the database to the latest migration..."
    if ! alembic upgrade head; then
        echo "Failed to upgrade the database. Stamping the current head to revert."
        alembic stamp head || { echo "Failed to stamp the current head."; exit 1; }
        exit 1
    fi

    echo "Alembic migrations completed successfully."
}

# Run the main function
main

# Wait for all background processes to finish (if any)
wait
