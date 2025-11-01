-- Migration: Add missing tables for waitlist, contact messages, and alert preferences
-- Date: 2025-10-31
-- Description: Adds support for email collection, contact forms, and user alert preferences

-- Waitlist table - email collection for signup waitlist
CREATE TABLE IF NOT EXISTS waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',
    source VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Contact messages table - customer support messages
CREATE TABLE IF NOT EXISTS contact_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    response TEXT,
    
    CONSTRAINT valid_contact_email CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_message_length CHECK (length(message) >= 10 AND length(message) <= 5000),
    CONSTRAINT valid_name_length CHECK (length(name) >= 1 AND length(name) <= 255)
);

-- Alert preferences table - user notification settings
CREATE TABLE IF NOT EXISTS alert_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    discord_enabled BOOLEAN DEFAULT FALSE,
    telegram_chat_id VARCHAR(255),
    discord_webhook_url VARCHAR(255),
    alert_types JSONB DEFAULT '["entry", "exit", "risk", "error"]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_telegram_chat_id CHECK (telegram_chat_id IS NULL OR length(telegram_chat_id) > 0),
    CONSTRAINT valid_discord_webhook CHECK (discord_webhook_url IS NULL OR discord_webhook_url ~ '^https://discord(app)?\.com/api/webhooks/'),
    CONSTRAINT valid_alert_types CHECK (jsonb_typeof(alert_types) = 'array')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist(email);
CREATE INDEX IF NOT EXISTS idx_waitlist_created_at ON waitlist(created_at);
CREATE INDEX IF NOT EXISTS idx_contact_messages_status ON contact_messages(status);
CREATE INDEX IF NOT EXISTS idx_contact_messages_created_at ON contact_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_preferences_user_id ON alert_preferences(user_id);

-- Row Level Security (RLS) Policies for new tables
ALTER TABLE alert_preferences ENABLE ROW LEVEL SECURITY;

-- Alert preferences policies
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'alert_preferences' 
        AND policyname = 'Users can view own alert preferences'
    ) THEN
        CREATE POLICY "Users can view own alert preferences" ON alert_preferences
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'alert_preferences' 
        AND policyname = 'Users can insert own alert preferences'
    ) THEN
        CREATE POLICY "Users can insert own alert preferences" ON alert_preferences
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'alert_preferences' 
        AND policyname = 'Users can update own alert preferences'
    ) THEN
        CREATE POLICY "Users can update own alert preferences" ON alert_preferences
            FOR UPDATE USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'alert_preferences' 
        AND policyname = 'Users can delete own alert preferences'
    ) THEN
        CREATE POLICY "Users can delete own alert preferences" ON alert_preferences
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;

-- Trigger for alert_preferences updated_at
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_alert_preferences_updated_at'
    ) THEN
        CREATE TRIGGER update_alert_preferences_updated_at BEFORE UPDATE ON alert_preferences
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Function to create default alert preferences when user signs up
CREATE OR REPLACE FUNCTION create_user_alert_preferences()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO alert_preferences (user_id) VALUES (NEW.id);
    RETURN NEW;
EXCEPTION
    WHEN unique_violation THEN
        -- Alert preferences already exist, ignore
        RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to create alert preferences when user signs up
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'on_auth_user_created_alert_preferences'
    ) THEN
        CREATE TRIGGER on_auth_user_created_alert_preferences
            AFTER INSERT ON auth.users
            FOR EACH ROW EXECUTE FUNCTION create_user_alert_preferences();
    END IF;
END $$;

-- Update realtime publication to include alert_preferences for live updates
BEGIN;
  DROP PUBLICATION IF EXISTS supabase_realtime;
  CREATE PUBLICATION supabase_realtime FOR TABLE run_logs, runs, alert_preferences;
COMMIT;