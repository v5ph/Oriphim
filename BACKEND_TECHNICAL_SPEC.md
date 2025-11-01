# ORIPHIM Backend Technical Specification

## Architecture Decision Record (ADR)

### Tech Stack Selection

**Backend Framework: FastAPI (Python)**
- **Rationale**: 
  - Automatic OpenAPI/Swagger documentation
  - Excellent WebSocket support
  - Type hints for better code quality
  - Async/await for high performance
  - Easy integration with ML/analytics libraries
  - Strong ecosystem for financial data processing

**Database: PostgreSQL + Redis**
- **PostgreSQL**: Primary data store for structured data
- **Redis**: Session storage, caching, real-time data

**Authentication: JWT + OAuth2**
- Stateless authentication
- Refresh token rotation
- 2FA support with TOTP

**Real-time: WebSocket + Server-Sent Events**
- WebSocket for bidirectional communication with Runner
- SSE for one-way dashboard updates

## Database Schema Design

### Core Tables

```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    plan_type VARCHAR(50) DEFAULT 'free',
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

-- Bot Management
CREATE TABLE bot_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL, -- 'put-lite', 'buy-write', 'condor', 'gamma-burst'
    mode VARCHAR(10) NOT NULL DEFAULT 'PAPER', -- 'PAPER' or 'LIVE'
    symbols TEXT[] NOT NULL,
    schedule_start_time TIME,
    schedule_end_time TIME,
    risk_per_trade DECIMAL(10,2),
    daily_risk_cap DECIMAL(10,2),
    parameters JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'stopped', -- 'running', 'paused', 'stopped', 'error'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_run_at TIMESTAMP
);

-- Trading Data
CREATE TABLE trading_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID NOT NULL REFERENCES bot_configs(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'running', 'completed', 'error', 'stopped'
    total_pnl DECIMAL(15,4) DEFAULT 0,
    num_trades INTEGER DEFAULT 0,
    max_drawdown DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES trading_runs(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(15,4),
    exit_price DECIMAL(15,4),
    pnl DECIMAL(15,4),
    fees DECIMAL(15,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'closed', 'expired'
    option_details JSONB, -- strike, expiry, type, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE trade_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES trading_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(10) NOT NULL, -- 'INFO', 'WARN', 'ERROR', 'DEBUG'
    message TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alerts and Notifications
CREATE TABLE alert_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    discord_enabled BOOLEAN DEFAULT FALSE,
    telegram_chat_id VARCHAR(255),
    discord_webhook_url VARCHAR(255),
    alert_types JSONB DEFAULT '["entry", "exit", "risk", "error"]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    channels TEXT[] NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    metadata JSONB DEFAULT '{}'
);

-- API Keys and Runner Integration
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL, -- First few chars for display
    permissions TEXT[] DEFAULT '["runner:connect", "runner:execute"]',
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE runner_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    machine_id VARCHAR(255) NOT NULL,
    machine_info JSONB,
    connected_at TIMESTAMP DEFAULT NOW(),
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'connected', -- 'connected', 'disconnected', 'error'
    version VARCHAR(50)
);

-- Waitlist and Contact
CREATE TABLE waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'invited', 'converted'
    source VARCHAR(50), -- 'website', 'referral', etc.
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE contact_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'new', -- 'new', 'read', 'responded', 'closed'
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP,
    response TEXT
);

-- Performance Analytics (Materialized Views)
CREATE MATERIALIZED VIEW daily_performance AS
SELECT 
    user_id,
    bot_id,
    DATE(entry_time) as trade_date,
    COUNT(*) as num_trades,
    SUM(pnl) as daily_pnl,
    AVG(pnl) as avg_trade_pnl,
    STDDEV(pnl) as pnl_stddev,
    COUNT(CASE WHEN pnl > 0 THEN 1 END)::FLOAT / COUNT(*) as win_rate
FROM positions p
JOIN trading_runs tr ON p.run_id = tr.id
JOIN bot_configs bc ON tr.bot_id = bc.id  
WHERE p.status = 'closed'
GROUP BY user_id, bot_id, DATE(entry_time);

-- Indexes for Performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_bot_configs_user_id ON bot_configs(user_id);
CREATE INDEX idx_trading_runs_bot_id ON trading_runs(bot_id);
CREATE INDEX idx_positions_run_id ON positions(run_id);
CREATE INDEX idx_positions_entry_time ON positions(entry_time);
CREATE INDEX idx_trade_logs_run_id_timestamp ON trade_logs(run_id, timestamp);
CREATE INDEX idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_runner_sessions_user_id ON runner_sessions(user_id);
```

## API Endpoint Specification

### Authentication Endpoints

```python
# /api/auth/
POST /signup
    Request: {email, password, first_name?, last_name?}
    Response: {user, access_token, refresh_token}

POST /signin  
    Request: {email, password}
    Response: {user, access_token, refresh_token}

POST /refresh
    Request: {refresh_token}
    Response: {access_token, refresh_token}

POST /logout
    Request: {refresh_token}
    Response: {message}

POST /forgot-password
    Request: {email}
    Response: {message}

POST /reset-password
    Request: {token, new_password}
    Response: {message}

POST /verify-email
    Request: {token}
    Response: {message}
```

### User Management

```python
# /api/users/
GET /profile
    Response: {user, profile}

PUT /profile
    Request: {first_name?, last_name?, timezone?, preferences?}
    Response: {profile}

PUT /change-password
    Request: {current_password, new_password}
    Response: {message}

POST /enable-2fa
    Response: {qr_code, backup_codes}

POST /verify-2fa
    Request: {totp_code}
    Response: {message}
```

### Bot Management

```python
# /api/bots/
GET /
    Response: {bots: [bot_config]}

POST /
    Request: {name, strategy_type, mode, symbols, schedule, risk_settings, parameters}
    Response: {bot_config}

GET /{bot_id}
    Response: {bot_config, recent_runs, performance_summary}

PUT /{bot_id}
    Request: {name?, symbols?, schedule?, risk_settings?, parameters?}
    Response: {bot_config}

DELETE /{bot_id}
    Response: {message}

POST /{bot_id}/start
    Response: {message, run_id}

POST /{bot_id}/stop
    Response: {message}

POST /{bot_id}/pause
    Response: {message}

GET /{bot_id}/runs
    Query: {limit?, offset?, status?}
    Response: {runs, total_count}

GET /{bot_id}/performance
    Query: {start_date?, end_date?}
    Response: {metrics, daily_data, trade_outcomes}
```

### Trading Data

```python
# /api/trading/
GET /runs
    Query: {status?, bot_id?, limit?, offset?}
    Response: {runs, total_count}

GET /runs/{run_id}
    Response: {run, positions, logs}

GET /runs/{run_id}/logs
    Query: {level?, limit?, offset?}
    Response: {logs, total_count}

GET /positions
    Query: {status?, symbol?, limit?, offset?}
    Response: {positions, total_count}

GET /positions/{position_id}
    Response: {position, related_positions}

# WebSocket endpoints
WS /trading/live
    Events: position_update, pnl_update, log_message, status_change
```

### Analytics

```python
# /api/analytics/
GET /performance
    Query: {bot_id?, start_date?, end_date?, granularity?}
    Response: {
        summary: {total_pnl, num_trades, win_rate, sharpe_ratio, max_drawdown},
        daily_data: [{date, pnl, cumulative_pnl, num_trades}],
        monthly_data: [{month, pnl, num_trades, win_rate}]
    }

GET /trade-outcomes
    Query: {bot_id?, strategy_type?, symbol?}
    Response: {
        win_loss_distribution: [{bucket, count}],
        pnl_histogram: [{range, count}],  
        holding_time_distribution: [{duration, count}]
    }

GET /regimes
    Query: {start_date?, end_date?}
    Response: {
        iv_rank_data: [{date, iv_rank, realized_vol}],
        regime_periods: [{start, end, regime_type, performance}],
        correlation_matrix: {symbols: [], correlations: [[]]}
    }

GET /ai-comparison
    Query: {bot_id}
    Response: {
        ai_vs_rules: {ai_pnl, rules_pnl, improvement_pct},
        feature_importance: [{feature, importance}],
        model_metrics: {accuracy, precision, recall}
    }
```

### Alerts

```python
# /api/alerts/
GET /preferences
    Response: {alert_preferences}

PUT /preferences
    Request: {email_enabled?, telegram_enabled?, discord_enabled?, telegram_chat_id?, discord_webhook_url?, alert_types?}
    Response: {alert_preferences}

GET /history
    Query: {limit?, offset?, alert_type?, status?}
    Response: {alerts, total_count}

POST /test
    Request: {channel, message?}
    Response: {message, status}
```

### Runner Integration

```python
# /api/runner/
POST /authenticate
    Request: {api_key}
    Response: {session_token, user_info, permissions}

GET /config
    Response: {bot_configs, global_settings, risk_limits}

POST /heartbeat
    Request: {machine_info?, status?, active_bots?}
    Response: {message, commands?}

# WebSocket for runner communication
WS /runner/connect
    Events: bot_command, config_update, emergency_stop
```

### Admin & Utilities

```python
# /api/admin/ (admin only)
GET /users
    Query: {limit?, offset?, status?}
    Response: {users, total_count}

GET /waitlist
    Query: {limit?, offset?, status?}
    Response: {waitlist_entries, total_count}

GET /system-health
    Response: {database, redis, websocket, runner_connections}

# /api/contact/
POST /message
    Request: {name, email, message}
    Response: {message}

# /api/waitlist/
POST /join
    Request: {email, source?}
    Response: {message}
```

## WebSocket Event Schema

### Trading Data Events

```typescript
// Client -> Server
type ClientMessage = 
  | { type: 'subscribe', channels: string[] }
  | { type: 'unsubscribe', channels: string[] }
  | { type: 'ping' }

// Server -> Client  
type ServerMessage =
  | { type: 'position_update', data: Position }
  | { type: 'pnl_update', data: { run_id: string, total_pnl: number, daily_pnl: number } }
  | { type: 'log_message', data: { run_id: string, level: string, message: string, timestamp: string } }
  | { type: 'bot_status', data: { bot_id: string, status: string, error?: string } }
  | { type: 'runner_status', data: { connected: boolean, last_heartbeat: string, machine_info: object } }
  | { type: 'pong' }
```

### Runner Communication Events

```typescript
// Server -> Runner
type RunnerCommand =
  | { type: 'start_bot', bot_id: string, config: BotConfig }
  | { type: 'stop_bot', bot_id: string }
  | { type: 'update_config', bot_id: string, config: Partial<BotConfig> }
  | { type: 'emergency_stop', reason: string }
  | { type: 'ping' }

// Runner -> Server
type RunnerMessage =
  | { type: 'position_opened', data: Position }
  | { type: 'position_closed', data: Position }
  | { type: 'log', data: { level: string, message: string, bot_id?: string } }
  | { type: 'error', data: { error: string, bot_id?: string } }
  | { type: 'heartbeat', data: { machine_info: object, active_bots: string[] } }
  | { type: 'pong' }
```

## Security Considerations

### Authentication Security
- Password hashing with bcrypt (cost factor 12+)
- JWT tokens with short expiry (15 minutes access, 7 days refresh)
- Refresh token rotation on each use
- Rate limiting on auth endpoints
- Account lockout after failed attempts

### API Security
- CORS configuration for frontend domains only
- Request rate limiting per user/IP
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- XSS protection with content security policy

### Runner Security
- API keys with limited scope and expiration
- Secure WebSocket with token authentication
- Machine fingerprinting for session validation
- Command validation and authorization
- Encrypted communication over WSS

## Performance Optimization

### Database Optimization
- Connection pooling with pgbouncer
- Read replicas for analytics queries
- Materialized views for complex aggregations
- Partitioning for time-series data (positions, logs)
- Regular VACUUM and ANALYZE operations

### Caching Strategy
- Redis for session storage
- Cache frequently accessed bot configs
- Cache analytics results (5-minute TTL)
- Cache user preferences and settings
- WebSocket connection state in Redis

### Real-time Performance
- WebSocket connection pooling
- Event batching for high-frequency updates
- Client-side buffering and throttling
- Server-sent events for one-way updates
- Background job processing for heavy analytics

## Deployment Architecture

### Production Environment
```
Frontend (Vercel)
    ↓
Load Balancer (Cloudflare)
    ↓
Backend Instances (Railway/Render) × 2
    ↓
Database (PostgreSQL + Redis)
    ↓
Background Workers (Celery)
```

### Environment Configuration
```yaml
# docker-compose.prod.yml
services:
  backend:
    image: oriphim/backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - EMAIL_API_KEY=${EMAIL_API_KEY}
    
  worker:
    image: oriphim/backend:latest
    command: celery worker
    
  redis:
    image: redis:7-alpine
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=oriphim
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
```

This technical specification provides the foundation for implementing all the stub functionality while ensuring scalability, security, and maintainability.