#!/bin/bash

# Function to kill all background processes
cleanup() {
    echo "Terminating all background processes..."
    kill $(jobs -p)  # Kill all background processes started by this script
    wait
}

# Trap SIGINT (Ctrl+C) and call cleanup function
trap cleanup SIGINT

# Set ENVIRONMENT variable
ENVIRONMENT="${ENVIRONMENT:-'production'}"

# Function to check if a service is running on a specific port
is_service_running() {
    local port=$1
    nc -z localhost "$port" >/dev/null 2>&1
    return $?  # Returns 0 if running, non-zero if not
}

# Function to prompt for a new port if the current port is in use
get_available_port() {
    local default_port=$1
    local service_name=$2
    while is_service_running "$default_port"; do
        echo "$service_name is running on port $default_port. Please enter a new port number:"
        read -r new_port
        if [[ ! "$new_port" =~ ^[0-9]+$ ]]; then
            echo "Invalid input. Please enter a valid port number."
        else
            default_port=$new_port
        fi
    done
    echo "$default_port"
}

# Function to start Redis if it's not running
check_and_start_redis() {
    echo "Checking Redis status..."
    if ! is_service_running 6379; then
        echo "Redis is not running. Starting Redis..."
        redis-server &  # Start Redis server
        sleep 5  # Wait for Redis to start
        if is_service_running 6379; then
            echo "Redis started successfully."
        else
            echo "Failed to start Redis. Please check Redis configuration."
            exit 1
        fi
    else
        echo "Redis is already running."
    fi
}

# Function to start Celery
start_celery() {
    echo "Starting Celery..."
    celery -A src.celery_tasks.celery_app worker --loglevel=INFO -E &
    sleep 5  # Wait for Celery to start
}

# Function to start Celery Beat
start_celery_beat() {
    echo "Starting Celery beat..."
    celery -A src.celery_tasks.celery_app beat --port=5555 &
    sleep 5  # Wait for Celery beat to start
}

# Function to start Celery Flower
start_celery_flower() {
    echo "Starting Celery flower..."
    celery -A src.celery_tasks.celery_app flower --port=5800 &
    sleep 5  # Wait for Celery Flower to start
}

# Function to check if PostgreSQL database exists and create it if it does not
check_postgres_db() {
    local db_name=$1
    echo "Checking if PostgreSQL database '$db_name' exists..."
    if psql -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        echo "Database $db_name exists."
    else
        echo "Database $db_name does not exist. Creating it..."
        createdb "$db_name"
    fi
}

# Function to start FastAPI server
start_fastapi() {
    local default_port=8000
    local port
    port=$(get_available_port "$default_port" "FastAPI")
    echo "Starting FastAPI server on port $port..."
    uvicorn src:app --host 0.0.0.0 --port "$port" --reload &
}

# Function to start Mailpit
start_mailpit() {
    echo "Starting Mailpit..."

    os_type=$(uname -s)  # Get the OS type using uname

    if [[ "$os_type" == "Linux" ]]; then
        # Run Mailpit for Linux
        ./mailpit-linux/mailpit &
    elif [[ "$os_type" == "MINGW32_NT"* || "$os_type" == "MINGW64_NT"* || "$os_type" == "CYGWIN_NT"* ]]; then
        # Run Mailpit for Windows
        ./mailpit/mailpit.exe &
    else
        echo "Unsupported OS: $os_type"
        ./mailpit/mailpit.exe &
    fi

    sleep 5  # Wait for Mailpit to start
}


# Main function to execute the startup process
main() {
    if [[ "$ENVIRONMENT" == "local" ]]; then
        check_postgres_db "portfolio"

        # Check if Pipenv environment is active
        if ! pipenv --venv >/dev/null 2>&1; then
            echo "Pipenv environment is not active. Activating Pipenv..."
            pipenv shell || { echo "Failed to activate Pipenv shell."; exit 1; }
        else
            echo "Pipenv environment is already active."
        fi


        # Check if Pipfile.lock exists to avoid reinstalling dependencies
        if [[ ! -f "Pipfile.lock" ]]; then
            echo "Pipfile.lock not found. Installing dependencies..."
            if pip install -r requirements/local.txt; then
                echo "Dependencies installed successfully."
            else
                echo "Failed to install dependencies. Continuing with the script..."
            fi
        else
            echo "Pipfile.lock found. Ensuring environment is up-to-date..."
            if pip install -r requirements/local.txt; then
                echo "Environment is up-to-date."
            else
                echo "Failed to sync dependencies. Continuing with the script..."
            fi
        fi

        check_and_start_redis
    else
        echo "ENVIRONMENT is in production mode."
    fi


    start_celery
    start_fastapi


    if [[ "$ENVIRONMENT" == "local" ]]; then
        # Start Celery Flower
        start_celery_flower
        # Start Mailpit server if ENVIRONMENT is local
        start_mailpit &
    else
        echo "ENVIRONMENT is in production mode. Skipping Mailpit server start and Celery Flower."
    fi
}

# Run the main function
main

# Wait for all background processes to finish
wait
