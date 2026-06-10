#!/bin/bash
set -e

echo "--- DATABASE INITIALIZATION ---"

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$POSTGRES_BOT_USER') THEN
            CREATE USER $POSTGRES_BOT_USER WITH PASSWORD '$POSTGRES_BOT_PASSWORD';
        END IF;
    END \$\$;
EOSQL

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE $POSTGRES_BOT_DB OWNER $POSTGRES_BOT_USER'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_BOT_DB')\gexec
EOSQL

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_BOT_DB TO $POSTGRES_BOT_USER;
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS settings (
        id SERIAL PRIMARY KEY,
        version TEXT NOT NULL,
        last_update TEXT NOT NULL,
        requests_handled INT DEFAULT 0,
        debug BOOLEAN DEFAULT FALSE
    );
    INSERT INTO settings (version, last_update, debug) VALUES ('6.0.0.0', '9 июня 2026г.', FALSE);
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL UNIQUE,
        error_messages BOOLEAN DEFAULT TRUE
    );
    INSERT INTO admins (user_id) VALUES ('$BOT_ADMIN_ID');
EOSQL



# --- users ----

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL UNIQUE,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        screen_name TEXT NOT NULL UNIQUE,
        update_notifications BOOLEAN DEFAULT TRUE,
        mentions BOOLEAN DEFAULT TRUE,
        who_can_rp TEXT DEFAULT 'all',
        darky_verify_warns INT DEFAULT 0,
        is_banned BOOLEAN DEFAULT FALSE
    );
EOSQL



# --- chats ---

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chats (
        id SERIAL PRIMARY KEY,
        chat_id INT UNIQUE NOT NULL,
        chat_title TEXT,
        settings_id INT NOT NULL UNIQUE,
        verify_settings_id INT NOT NULL UNIQUE,
        greeting_id INT NOT NULL UNIQUE,
        rules_id INT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_settings (
        id SERIAL PRIMARY KEY,
        update_notifications BOOLEAN DEFAULT TRUE,
        mention_in_greetings BOOLEAN DEFAULT TRUE,
        lvlups BOOLEAN DEFAULT TRUE,
        rp BOOLEAN DEFAULT TRUE,
        nicknames BOOLEAN DEFAULT TRUE,
        manage_rp TEXT DEFAULT 'admins',
        manage_nicknames TEXT DEFAULT 'admins',
        triggers BOOLEAN DEFAULT TRUE,
        kick_access TEXT DEFAULT 'admins',
        warn_access TEXT DEFAULT 'admins',
        ban_access TEXT DEFAULT 'admins',
        warn_limit INT DEFAULT 5,
        warn_punishment TEXT DEFAULT 'ban',
        autokick BOOLEAN DEFAULT FALSE
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS verify_settings (
        id SERIAL PRIMARY KEY,
        enabled BOOLEAN DEFAULT TRUE,
        punishment TEXT DEFAULT 'ban',
        days_from_signup INT DEFAULT 3,
        should_follow_groups BOOLEAN DEFAULT FALSE,
        spam_detection BOOLEAN DEFAULT TRUE
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_greetings (
        id SERIAL PRIMARY KEY,
        content TEXT,
        attachment TEXT
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_rules (
        id SERIAL PRIMARY KEY,
        content TEXT,
        attachment TEXT
    );
EOSQL