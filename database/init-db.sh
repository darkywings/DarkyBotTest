#!/bin/bash
set -e

echo "=== DATABASE INITIALIZATION ==="

# Ожидание запуска PostgreSQL
echo "Waiting for PostgreSQL..."
until pg_isready -U $POSTGRES_USER; do
  sleep 1
done

echo "PostgreSQL is started!"

# Проверка существования пользователя
echo "Check for bot's user..."
USER_EXISTS=$(psql -U $POSTGRES_USER -tAc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_BOT_USER'")

if [ -z "$USER_EXISTS" ]; then
    psql -U $POSTGRES_USER -c "CREATE USER $POSTGRES_BOT_USER WITH PASSWORD '$POSTGRES_BOT_PASSWORD';"
    echo "User was created"
else
    echo "$POSTGRES_BOT_USER already exists"
fi

# Проверка существования базы данных
echo "Check for database..."
DB_EXISTS=$(psql -U $POSTGRES_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_BOT_DB'")

if [ -z "$DB_EXISTS" ]; then
    echo "Creating database: $POSTGRES_BOT_DB..."
    psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_BOT_DB OWNER $POSTGRES_BOT_USER;"
    psql -U $POSTGRES_USER -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_BOT_DB TO $POSTGRES_BOT_USER;"
    echo "Database was created"
else
    echo "Database $POSTGRES_BOT_DB already exists"
fi

# Создание необхоимых таблиц
echo "Checking for tables..."

psql -U $POSTGRES_BOT_USER -d "$POSTGRES_BOT_DB" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'chat_member' AND typtype = 'c'
    ) THEN CREATE TYPE chat_member AS (
        id BIGINT,
        is_banned BOOLEAN,
        warns INTEGER,
        nickname VARCHAR(255),
        level INTEGER,
        level_xp BIGINT
    );
    END IF;
END \$\$;
EOSQL

psql -U $POSTGRES_BOT_USER -d "$POSTGRES_BOT_DB" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'chat_settings' AND typtype = 'c'
    ) THEN CREATE TYPE chat_settings AS (
        simple_triggers BOOLEAN,
        lvlups BOOLEAN,
        warn_limit INTEGER,
        warn_punishment TEXT,
        autokick BOOLEAN,
        rp BOOLEAN,
        admin_panel TEXT,
        manage_rp TEXT
    );
    END IF;
END \$\$;
EOSQL

psql -U $POSTGRES_BOT_USER -d "$POSTGRES_BOT_DB" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'chat_greeting' AND typtype = 'c'
    ) THEN CREATE TYPE chat_greeting AS (
        content TEXT,
        attachment TEXT
    );
    END IF;
END \$\$;
EOSQL

psql -U $POSTGRES_BOT_USER -d "$POSTGRES_BOT_DB" <<-EOSQL
CREATE TABLE IF NOT EXISTS chats (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    chat_title VARCHAR(255),
    settings chat_settings DEFAULT ROW(TRUE, TRUE, 5, 'ban', FALSE, TRUE, 'admins', 'admins'
    ),
    greeting chat_greeting DEFAULT ROW(NULL, NULL),
    rules TEXT DEFAULT NULL,
    members chat_member[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOSQL

psql -U $POSTGRES_BOT_USER -d "$POSTGRES_BOT_DB" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'user_note' AND typtype = 'c'
    ) THEN CREATE TYPE user_note AS (
        id INTEGER,
        title TEXT,
        content TEXT
    );
    END IF;
END \$\$;
EOSQL

psql -U $POSTGRES_BOT_USER -d "$POSTGRES_BOT_DB" <<-EOSQL
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    mentions BOOLEAN DEFAULT TRUE,
    who_can_rp TEXT DEFAULT 'all',
    notes user_note[]
);
EOSQL

echo "=== INITIALIZATION COMPLETE ==="