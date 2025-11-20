#!/usr/bin/env bash

# App Entrypoint Script
# Starts PostgreSQL database, FastAPI backend, and Next.js frontend

set -e

echo "🚀 Starting App Services..."

# Fatal error function
fatal() {
    echo "❌ FATAL ERROR: $1"
    echo "🛑 Container will now exit"
    exit 1
}

# Function to initialize and start PostgreSQL database
init_database() {
    echo "🗄️ Starting PostgreSQL database..."

    # Create directories
    mkdir -p /app/APP_DATA/db/postgres_data
    chown -R postgres:postgres /app/APP_DATA/db

    # Initialize database if needed
    if [ ! -f /app/APP_DATA/db/postgres_data/PG_VERSION ]; then
        echo "📝 Initializing PostgreSQL database..."
        su postgres -c "initdb --pgdata /app/APP_DATA/db/postgres_data --auth-local trust --auth-host md5 --encoding UTF8 --locale C --no-sync"
        if [ $? -ne 0 ]; then
            fatal "PostgreSQL database initialization failed"
        fi
    fi

    # Start PostgreSQL server in background
    echo "🚀 Starting PostgreSQL server on ${POSTGRES_HOST}:${POSTGRES_PORT}"
    su postgres -c "postgres -D /app/APP_DATA/db/postgres_data -h 0.0.0.0 -p ${POSTGRES_PORT}" > /app/APP_DATA/db/postgres.log 2>&1 &
    DB_PID=$!

    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    for i in {1..30}; do
        # Check if PostgreSQL process is still running
        if ! kill -0 $DB_PID 2>/dev/null; then
            echo "❌ PostgreSQL process died unexpectedly"
            echo "PostgreSQL logs:"
            cat /app/APP_DATA/db/postgres.log 2>/dev/null || echo "No log file found"
            fatal "PostgreSQL process died"
        fi
        
        # Try to connect to database
        if su postgres -c "psql -d postgres -c 'SELECT 1;'" >/dev/null 2>&1; then
            echo "✅ Database is ready!"
            break
        fi
        echo "⏳ Waiting for database... ($i/30)"
        sleep 2
    done

    # Check if database is ready
    if ! su postgres -c "psql -d postgres -c 'SELECT 1;'" >/dev/null 2>&1; then
        kill $DB_PID 2>/dev/null
        fatal "Database failed to start within 60 seconds"
    fi

    # Set postgres user password
    echo "🔐 Setting postgres user password..."
    su postgres -c "psql -c \"ALTER USER postgres PASSWORD '${POSTGRES_PASSWORD}';\""

    # Create application database
    echo "📝 Creating application database..."
    su postgres -c "createdb ${POSTGRES_DB_NAME}" 2>/dev/null || echo "ℹ️ Database '${POSTGRES_DB_NAME}' already exists"

    echo -e "\033[92m✅ PostgreSQL database started successfully\033[0m"
}

# Function to check if database tables have been initialized
check_tables_initialized() {
    local db_name="${POSTGRES_DB_NAME:-app_db}"
    
    # Query to count tables in the public schema (excluding system tables)
    local table_count=$(su postgres -c "psql -d ${db_name} -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';\" 2>/dev/null" | tr -d ' ' || echo "0")
    
    # Check if we got a valid number
    if ! [[ "$table_count" =~ ^[0-9]+$ ]]; then
        # If we couldn't determine the table count, return 1 to indicate database is not initialized
        return 1
    fi
    
    if [ "$table_count" -gt 0 ]; then
        # If tables exist, return 0 to indicate database is initialized
        return 0
    else
        # If no tables, return 1 to indicate database is not initialized
        return 1
    fi
}

# Function to run database migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    cd /app/backend

    # Check current migration version before running
    CURRENT_VERSION=$(alembic current 2>/dev/null | head -1 | awk '{print $1}' || echo "none")
    if [ "$CURRENT_VERSION" != "none" ] && [ -n "$CURRENT_VERSION" ]; then
        echo "   Current migration version: ${CURRENT_VERSION}"
    else
        echo "   No migrations applied yet"
        CURRENT_VERSION="none"
    fi

    # Run migrations (blocking operation - waits for completion)
    echo "   Running migrations..."
    if alembic upgrade head; then
        # Check new version after migration
        NEW_VERSION=$(alembic current 2>/dev/null | head -1 | awk '{print $1}' || echo "none")
        if [ "$CURRENT_VERSION" != "$NEW_VERSION" ] && [ "$NEW_VERSION" != "none" ]; then
            echo "✅ Migrations completed successfully (${CURRENT_VERSION} → ${NEW_VERSION})"
        else
            echo "✅ Database is already up to date (version: ${NEW_VERSION})"
        fi
    else
        echo "⚠️  Migration failed, but continuing startup..."
        return 1
    fi
    return 0
}

# Normalize NODE_ENV for Next.js compatibility
if [ "$NODE_ENV" = "dev" ]; then
    export NODE_ENV=development
    echo "📝 Normalized NODE_ENV: dev → development"
elif [ "$NODE_ENV" = "prod" ]; then
    export NODE_ENV=production
    echo "📝 Normalized NODE_ENV: prod → production"
fi

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    kill $DB_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Initialize and start PostgreSQL database
init_database

# Run database migrations before starting backend
# Only run migrations if tables are already initialized
if check_tables_initialized; then
    echo "Database tables are already initialized, running migrations..."
    run_migrations
else
    echo "Database tables are not initialized, skipping migrations..."
fi

# Start backend
echo "📡 Starting FastAPI backend on port 5000..."
cd /app/backend

# Check DEBUG mode
if [ "$DEBUG" = "1" ]; then
    echo "🐛 Starting backend in DEBUG mode with debugpy (waiting for client) on port 5678..."
    python -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py &
elif [ "$DEBUG" = "2" ]; then
    echo "🐛 Starting backend in DEBUG mode with debugpy (no wait) on port 5678..."
    python -m debugpy --listen 0.0.0.0:5678 main.py &
else
    echo "🚀 Starting backend in production mode..."
    python main.py &
fi
BACKEND_PID=$!

# Start frontend in background
echo "🌐 Starting Next.js frontend on port 3000..."
cd /app/frontend

# Create logs directory if it doesn't exist
mkdir -p /app/APP_DATA/logs

npm start > /app/APP_DATA/logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for backend process - if it dies, container exits
wait $BACKEND_PID