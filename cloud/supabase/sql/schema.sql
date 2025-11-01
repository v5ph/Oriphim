-- Oriphim MVP Database Schema
-- SaaS trading automation platform with secure user isolation

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE bot_kind AS ENUM ('putlite', 'buywrite', 'condor', 'gammaburst');
CREATE TYPE run_status AS ENUM ('pending', 'running', 'completed', 'failed', 'stopped');
CREATE TYPE run_mode AS ENUM ('paper', 'live');
CREATE TYPE log_level AS ENUM ('debug', 'info', 'warning', 'error');
CREATE TYPE plan_tier AS ENUM ('free', 'pro', 'enterprise');

-- Bots table - stores bot configurations per user
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    kind bot_kind NOT NULL,
    name VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_user_bot_name UNIQUE (user_id, name)
);

-- Runs table - execution history for each bot run
CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    mode run_mode NOT NULL DEFAULT 'paper',
    status run_status NOT NULL DEFAULT 'pending',
    pnl DECIMAL(12,2) DEFAULT 0,
    max_drawdown DECIMAL(12,2) DEFAULT 0,
    trades_count INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Runner-sourced derived analytics (NOT raw market data)
    entry_conditions JSONB DEFAULT '{}', -- {"em": 3.4, "ivr": 62, "regime": "chop"}
    exit_conditions JSONB DEFAULT '{}',  -- {"reason": "time_stop", "pnl_target": false}
    market_regime JSONB DEFAULT '{}',    -- {"vix": 18.2, "skew": 1.15, "breadth": "neutral"}
    
    -- Sparse P/L snapshots for charting (5-10 points max per run)
    pnl_snapshots JSONB DEFAULT '[]',    -- [{"ts": "10:30", "pnl": 12.40}, {"ts": "11:00", "pnl": 18.60}]
    
    -- JSON metadata for analytics
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_pnl CHECK (pnl >= -999999.99 AND pnl <= 999999.99),
    CONSTRAINT valid_drawdown CHECK (max_drawdown >= 0)
);

-- Run logs table - realtime streaming logs from Runner
CREATE TABLE run_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level log_level NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}'
);

-- Positions table - normalized fill data (small, derived)
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    position_type VARCHAR(20) NOT NULL, -- 'option', 'stock', 'spread'
    side VARCHAR(10) NOT NULL, -- 'long', 'short'
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(10,4),
    current_price DECIMAL(10,4),
    unrealized_pnl DECIMAL(12,2) DEFAULT 0,
    realized_pnl DECIMAL(12,2) DEFAULT 0,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    
    -- Minimal contract details (not full chain data)
    contract_details JSONB DEFAULT '{}', -- {"strike": 450, "exp": "2025-11-01", "type": "C"}
    
    -- Entry/exit rationale from Runner
    entry_reason TEXT,
    exit_reason TEXT,
    
    CONSTRAINT valid_quantity CHECK (quantity != 0)
);

-- API keys table - device tokens for Runner authentication
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL DEFAULT 'Default Runner',
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    
    CONSTRAINT valid_token_length CHECK (length(token) >= 32)
);

-- Runner status table - live connection status and heartbeat
CREATE TABLE runner_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    is_connected BOOLEAN NOT NULL DEFAULT false,
    machine_name VARCHAR(255),
    runner_version VARCHAR(50),
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    broker_connected BOOLEAN DEFAULT false,
    broker_name VARCHAR(50), -- 'ibkr', 'tradier', etc.
    market_session VARCHAR(20), -- 'pre', 'regular', 'after', 'closed'
    active_bots INTEGER DEFAULT 0,
    system_info JSONB DEFAULT '{}', -- CPU, memory, disk space, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_user_runner UNIQUE (user_id, api_key_id)
);

-- External API Keys table - broker and data provider credentials
CREATE TYPE external_api_provider AS ENUM ('ibkr', 'tradier', 'alpaca', 'td_ameritrade', 'schwab');
CREATE TYPE external_api_environment AS ENUM ('paper', 'live');

CREATE TABLE external_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider external_api_provider NOT NULL,
    environment external_api_environment NOT NULL DEFAULT 'paper',
    name VARCHAR(100) NOT NULL,
    credentials JSONB NOT NULL, -- Encrypted credentials specific to each provider
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_user_provider_env UNIQUE (user_id, provider, environment)
);

-- Plans table - user subscription tiers and billing
CREATE TABLE plans (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tier plan_tier NOT NULL DEFAULT 'free',
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    canceled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row Level Security (RLS) Policies
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE run_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE runner_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;

-- Bots policies
CREATE POLICY "Users can view own bots" ON bots
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own bots" ON bots
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own bots" ON bots
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own bots" ON bots
    FOR DELETE USING (auth.uid() = user_id);

-- Runs policies
CREATE POLICY "Users can view own runs" ON runs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own runs" ON runs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own runs" ON runs
    FOR UPDATE USING (auth.uid() = user_id);

-- Run logs policies (read-only for users, Runner can insert)
CREATE POLICY "Users can view own run logs" ON run_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM runs 
            WHERE runs.id = run_logs.run_id 
            AND runs.user_id = auth.uid()
        )
    );

CREATE POLICY "Service can insert run logs" ON run_logs
    FOR INSERT WITH CHECK (true); -- Will be restricted via service key

-- API keys policies
CREATE POLICY "Users can manage own api keys" ON api_keys
    FOR ALL USING (auth.uid() = user_id);

-- External API keys policies
CREATE POLICY "Users can manage own external api keys" ON external_api_keys
    FOR ALL USING (auth.uid() = user_id);

-- Plans policies
CREATE POLICY "Users can view own plan" ON plans
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can manage plans" ON plans
    FOR ALL USING (true); -- Stripe webhooks need access

-- Runner status policies
CREATE POLICY "Users can view own runner status" ON runner_status
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can manage runner status" ON runner_status
    FOR ALL USING (true); -- Runner service needs full access

-- Positions policies
CREATE POLICY "Users can view own positions" ON positions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can manage positions" ON positions
    FOR ALL USING (true); -- Runner service needs full access

-- Indexes for performance
CREATE INDEX idx_bots_user_id ON bots(user_id);
CREATE INDEX idx_bots_kind ON bots(kind);
CREATE INDEX idx_runs_user_id ON runs(user_id);
CREATE INDEX idx_runs_bot_id ON runs(bot_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_started_at ON runs(started_at);
CREATE INDEX idx_run_logs_run_ts ON run_logs(run_id, ts);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_token ON api_keys(token) WHERE revoked_at IS NULL;
CREATE INDEX idx_external_api_keys_user_id ON external_api_keys(user_id);
CREATE INDEX idx_external_api_keys_provider ON external_api_keys(provider, environment);
CREATE INDEX idx_runner_status_user_id ON runner_status(user_id);
CREATE INDEX idx_runner_status_heartbeat ON runner_status(last_heartbeat);
CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_run_id ON positions(run_id);
CREATE INDEX idx_positions_status ON positions(opened_at, closed_at);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bots_updated_at BEFORE UPDATE ON bots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_external_api_keys_updated_at BEFORE UPDATE ON external_api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plans_updated_at BEFORE UPDATE ON plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_runner_status_updated_at BEFORE UPDATE ON runner_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Functions for common operations
CREATE OR REPLACE FUNCTION create_user_plan()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO plans (user_id, tier) VALUES (NEW.id, 'free');
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to create plan when user signs up
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_plan();

-- Waitlist table - email collection for signup waitlist
CREATE TABLE waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',
    source VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Contact messages table - customer support messages
CREATE TABLE contact_messages (
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
CREATE TABLE alert_preferences (
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
CREATE INDEX idx_waitlist_email ON waitlist(email);
CREATE INDEX idx_waitlist_created_at ON waitlist(created_at);
CREATE INDEX idx_contact_messages_status ON contact_messages(status);
CREATE INDEX idx_contact_messages_created_at ON contact_messages(created_at);
CREATE INDEX idx_alert_preferences_user_id ON alert_preferences(user_id);

-- Row Level Security (RLS) Policies for new tables
ALTER TABLE alert_preferences ENABLE ROW LEVEL SECURITY;

-- Alert preferences policies
CREATE POLICY "Users can view own alert preferences" ON alert_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own alert preferences" ON alert_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own alert preferences" ON alert_preferences
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own alert preferences" ON alert_preferences
    FOR DELETE USING (auth.uid() = user_id);

-- Waitlist and contact messages are public insert (no RLS needed for these)
-- They don't need user association for insert operations

-- Trigger for alert_preferences updated_at
CREATE TRIGGER update_alert_preferences_updated_at BEFORE UPDATE ON alert_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create default alert preferences when user signs up
CREATE OR REPLACE FUNCTION create_user_alert_preferences()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO alert_preferences (user_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to create alert preferences when user signs up
CREATE TRIGGER on_auth_user_created_alert_preferences
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_alert_preferences();

-- Realtime subscriptions setup (Runner-First Event-Driven Model)
BEGIN;
  -- Enable realtime for event-driven tables only (NOT market data)
  DROP PUBLICATION IF EXISTS supabase_realtime;
  CREATE PUBLICATION supabase_realtime FOR TABLE 
    runner_status,  -- Live connection status
    runs,          -- Trading session lifecycle
    run_logs,      -- Human-readable events
    positions;     -- Small, normalized fills
COMMIT;

-- Alert system triggers and functions
CREATE OR REPLACE FUNCTION trigger_alert_notification()
RETURNS TRIGGER AS $$
DECLARE
    alert_payload JSONB;
    alert_type TEXT;
    alert_title TEXT;
    alert_message TEXT;
    alert_severity TEXT;
    alert_data JSONB;
BEGIN
    -- Determine alert type and content based on the triggering event
    CASE TG_TABLE_NAME
        WHEN 'runs' THEN
            CASE
                WHEN TG_OP = 'INSERT' AND NEW.status = 'running' THEN
                    alert_type := 'entry';
                    alert_title := 'Trading Run Started';
                    alert_message := 'Bot "' || (SELECT name FROM bots WHERE id = NEW.bot_id) || '" started a new trading run';
                    alert_severity := 'info';
                    alert_data := jsonb_build_object(
                        'run_id', NEW.id,
                        'bot_name', (SELECT name FROM bots WHERE id = NEW.bot_id),
                        'mode', NEW.mode,
                        'started_at', NEW.started_at
                    );
                WHEN TG_OP = 'UPDATE' AND OLD.status != NEW.status AND NEW.status = 'completed' THEN
                    alert_type := 'exit';
                    alert_title := 'Trading Run Completed';
                    alert_message := 'Bot completed run with P&L: $' || COALESCE(NEW.pnl::TEXT, '0.00');
                    alert_severity := CASE WHEN NEW.pnl > 0 THEN 'success' ELSE 'info' END;
                    alert_data := jsonb_build_object(
                        'run_id', NEW.id,
                        'bot_name', (SELECT name FROM bots WHERE id = NEW.bot_id),
                        'pnl', NEW.pnl,
                        'trades_count', NEW.trades_count,
                        'duration_minutes', EXTRACT(EPOCH FROM (NEW.ended_at - NEW.started_at))/60
                    );
                WHEN TG_OP = 'UPDATE' AND OLD.status != NEW.status AND NEW.status = 'failed' THEN
                    alert_type := 'error';
                    alert_title := 'Trading Run Failed';
                    alert_message := 'Bot run failed: ' || COALESCE(NEW.error_message, 'Unknown error');
                    alert_severity := 'error';
                    alert_data := jsonb_build_object(
                        'run_id', NEW.id,
                        'bot_name', (SELECT name FROM bots WHERE id = NEW.bot_id),
                        'error_message', NEW.error_message,
                        'failed_at', NEW.ended_at
                    );
                WHEN TG_OP = 'UPDATE' AND OLD.pnl IS DISTINCT FROM NEW.pnl AND NEW.pnl < -100 THEN
                    alert_type := 'risk';
                    alert_title := 'Risk Alert: Large Loss';
                    alert_message := 'Run P&L dropped to $' || NEW.pnl::TEXT || ' - consider intervention';
                    alert_severity := 'warning';
                    alert_data := jsonb_build_object(
                        'run_id', NEW.id,
                        'bot_name', (SELECT name FROM bots WHERE id = NEW.bot_id),
                        'current_pnl', NEW.pnl,
                        'max_drawdown', NEW.max_drawdown
                    );
                ELSE
                    RETURN COALESCE(NEW, OLD); -- No alert needed
            END CASE;
        
        WHEN 'runner_status' THEN
            CASE
                WHEN TG_OP = 'UPDATE' AND OLD.is_connected != NEW.is_connected THEN
                    alert_type := 'connection';
                    alert_title := CASE WHEN NEW.is_connected THEN 'Runner Connected' ELSE 'Runner Disconnected' END;
                    alert_message := 'Runner on ' || COALESCE(NEW.machine_name, 'unknown machine') || 
                                   CASE WHEN NEW.is_connected THEN ' is now online' ELSE ' went offline' END;
                    alert_severity := CASE WHEN NEW.is_connected THEN 'success' ELSE 'warning' END;
                    alert_data := jsonb_build_object(
                        'machine_name', NEW.machine_name,
                        'runner_version', NEW.runner_version,
                        'broker_connected', NEW.broker_connected,
                        'active_bots', NEW.active_bots
                    );
                WHEN TG_OP = 'UPDATE' AND OLD.broker_connected != NEW.broker_connected AND NEW.broker_connected = false THEN
                    alert_type := 'error';
                    alert_title := 'Broker Connection Lost';
                    alert_message := 'Lost connection to ' || COALESCE(NEW.broker_name, 'broker') || ' - trading halted';
                    alert_severity := 'error';
                    alert_data := jsonb_build_object(
                        'broker_name', NEW.broker_name,
                        'machine_name', NEW.machine_name,
                        'active_bots', NEW.active_bots
                    );
                ELSE
                    RETURN COALESCE(NEW, OLD); -- No alert needed
            END CASE;
        
        ELSE
            RETURN COALESCE(NEW, OLD); -- Unknown table
    END CASE;

    -- Build alert payload
    alert_payload := jsonb_build_object(
        'user_id', COALESCE(NEW.user_id, OLD.user_id),
        'type', alert_type,
        'title', alert_title,
        'message', alert_message,
        'severity', alert_severity,
        'data', alert_data
    );

    -- Call the Edge Function to send alerts
    PERFORM net.http_post(
        url := current_setting('app.supabase_url') || '/functions/v1/send-alert',
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key')
        ),
        body := alert_payload
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for alert notifications
CREATE TRIGGER run_alerts_trigger
    AFTER INSERT OR UPDATE ON runs
    FOR EACH ROW
    EXECUTE FUNCTION trigger_alert_notification();

CREATE TRIGGER runner_status_alerts_trigger
    AFTER UPDATE ON runner_status
    FOR EACH ROW
    EXECUTE FUNCTION trigger_alert_notification();

-- Sample data for development (optional)
-- INSERT INTO auth.users (id, email, raw_user_meta_data, created_at, updated_at)
-- VALUES ('550e8400-e29b-41d4-a716-446655440000', 'test@oriphim.com', '{}', NOW(), NOW());