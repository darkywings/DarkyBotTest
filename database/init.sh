#!/bin/bash
set -e

echo "--- DATABASE INITIALIZATION ---"

psql --username "$POSTGRES_USER" <<-EOSQL
    ALTER USER $POSTGRES_USER WITH PASSWORD $POSTGRES_PASSWORD;
EOSQL

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
        who_can_rp_me TEXT CHECK (who_can_rp_me IN ( 'all', 'only_users', 'only_bot', 'nobody' )) DEFAULT 'all',
        darky_verify_warns INT DEFAULT 0,
        is_banned BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users (id),
        title TEXT NOT NULL,
        content TEXT NOT NULL
    );
EOSQL


# --- chats ---

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_settings (
        id SERIAL PRIMARY KEY,
        update_notifications BOOLEAN DEFAULT TRUE,
        mention_in_greetings BOOLEAN DEFAULT TRUE,
        lvlups BOOLEAN DEFAULT TRUE,
        rp BOOLEAN DEFAULT TRUE,
        nicknames BOOLEAN DEFAULT TRUE,
        manage_rp TEXT CHECK (manage_rp IN ( 'all', 'admins', 'nobody' )) DEFAULT 'admins',
        manage_nicknames TEXT CHECK (manage_nicknames IN ( 'all', 'admins', 'nobody' )) DEFAULT 'admins',
        triggers BOOLEAN DEFAULT TRUE,
        layout_autodetect BOOLEAN DEFAULT TRUE,
        who_can_mute TEXT CHECK (who_can_mute IN ( 'all', 'admins', 'nobody' )) DEFAULT 'admins',
        who_can_kick TEXT CHECK (who_can_kick IN ( 'all', 'admins', 'nobody' )) DEFAULT 'admins',
        who_can_warn TEXT CHECK (who_can_warn IN ( 'all', 'admins', 'nobody' )) DEFAULT 'admins',
        who_can_ban TEXT CHECK (who_can_ban IN ( 'all', 'admins', 'nobody' )) DEFAULT 'admins',
        warn_limit INT DEFAULT 5,
        warn_punishment TEXT CHECK (warn_punishment IN ( 'ban', 'kick', 'mute', 'none' )) DEFAULT 'ban',
        autokick BOOLEAN DEFAULT FALSE
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS verify_settings (
        id SERIAL PRIMARY KEY,
        enabled BOOLEAN DEFAULT TRUE,
        punishment TEXT CHECK (punishment IN ( 'ban', 'kick' )) DEFAULT 'ban',
        days_from_signup INT DEFAULT 3,
        should_follow_groups BOOLEAN DEFAULT FALSE,
        spam_detection BOOLEAN DEFAULT TRUE
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_greetings (
        id SERIAL PRIMARY KEY,
        content TEXT DEFAULT NULL,
        attachment TEXT DEFAULT NULL
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_rules (
        id SERIAL PRIMARY KEY,
        content TEXT DEFAULT NULL,
        attachment TEXT DEFAULT NULL
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chats (
        id SERIAL PRIMARY KEY,
        chat_id INT UNIQUE NOT NULL,
        chat_title TEXT,
        settings_id INT REFERENCES chat_settings (id),
        verify_settings_id INT REFERENCES verify_settings (id),
        greeting_id INT REFERENCES chat_greetings (id),
        rules_id INT REFERENCES chat_rules (id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_assocs (
        id SERIAL PRIMARY KEY,
        chat_id INT REFERENCES chats (id),
        command TEXT NOT NULL,
        assocs TEXT[]
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS rp (
        id SERIAL PRIMARY KEY,
        chat_id INT REFERENCES chats (id),
        trigger TEXT NOT NULL,
        reply_male TEXT NOT NULL,
        reply_female TEXT NOT NULL
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS chat_members (
        id SERIAL PRIMARY KEY,
        chat_id INT REFERENCES chats (id),
        user_id INT NOT NULL,
        nickname TEXT DEFAULT NULL,
        warns INT DEFAULT 0,
        is_banned BOOLEAN DEFAULT FALSE,
        level INT DEFAULT 1,
        level_xp INT DEFAULT 0,
        messages INT DEFAULT 0,
        bad_words INT DEFAULT 0,
        photo INT DEFAULT 0,
        video INT DEFAULT 0,
        audio INT DEFAULT 0,
        docs INT DEFAULT 0,
        audio_messages INT DEFAULT 0
    );
EOSQL

psql --username "$POSTGRES_BOT_USER" --dbname "$POSTGRES_BOT_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS member_activity (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users (id),
        date DATE NOT NULL UNIQUE,
        activity INT NOT NULL
    );
EOSQL