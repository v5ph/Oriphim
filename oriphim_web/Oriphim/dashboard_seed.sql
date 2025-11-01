-- Seed script for testing dashboard with sample data
-- Run this in the Supabase SQL Editor to populate test data

-- First, let's create some sample bots for the current user
-- Replace 'your-user-id' with an actual user ID from auth.users

-- Sample bots
INSERT INTO bots (user_id, kind, name, config_json, is_enabled) VALUES
  ('your-user-id', 'putlite', 'SPY PUT-Lite Bot', '{"symbols": ["SPY"], "risk_per_trade": 500}', true),
  ('your-user-id', 'buywrite', 'QQQ Buy-Write Bot', '{"symbols": ["QQQ"], "risk_per_trade": 1000}', true),
  ('your-user-id', 'condor', 'SPX Iron Condor', '{"symbols": ["SPX"], "risk_per_trade": 750}', false);

-- Sample runs with various P/L outcomes
INSERT INTO runs (user_id, bot_id, mode, status, pnl, trades_count, win_rate, started_at, ended_at) VALUES
  -- Today's runs
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPY PUT-Lite Bot' LIMIT 1), 'paper', 'completed', 125.50, 3, 66.67, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'QQQ Buy-Write Bot' LIMIT 1), 'paper', 'completed', -45.25, 2, 50.00, NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPY PUT-Lite Bot' LIMIT 1), 'paper', 'completed', 78.75, 1, 100.00, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '30 minutes'),
  
  -- Yesterday's runs  
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPY PUT-Lite Bot' LIMIT 1), 'paper', 'completed', 200.00, 4, 75.00, NOW() - INTERVAL '1 day 3 hours', NOW() - INTERVAL '1 day 2 hours'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'QQQ Buy-Write Bot' LIMIT 1), 'paper', 'completed', -120.50, 3, 33.33, NOW() - INTERVAL '1 day 1 hour', NOW() - INTERVAL '1 day'),
  
  -- This week's runs
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPX Iron Condor' LIMIT 1), 'paper', 'completed', 350.00, 2, 100.00, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '1 hour'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPY PUT-Lite Bot' LIMIT 1), 'paper', 'completed', -85.00, 2, 50.00, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '30 minutes'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'QQQ Buy-Write Bot' LIMIT 1), 'paper', 'running', 0.00, 0, 0.00, NOW() - INTERVAL '10 minutes', NULL);

-- Sample logs for recent activity
INSERT INTO logs (user_id, bot_id, run_id, level, component, message) VALUES
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPY PUT-Lite Bot' LIMIT 1), (SELECT id FROM runs WHERE status = 'running' LIMIT 1), 'info', 'bot_engine', 'Bot started successfully'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'SPY PUT-Lite Bot' LIMIT 1), (SELECT id FROM runs WHERE status = 'running' LIMIT 1), 'info', 'risk_manager', 'Risk check passed: $500 < $2000 daily limit'),
  ('your-user-id', (SELECT id FROM bots WHERE name = 'QQQ Buy-Write Bot' LIMIT 1), NULL, 'info', 'market_data', 'Market data connection established');

-- To use this script:
-- 1. Go to your Supabase Dashboard > SQL Editor
-- 2. Replace 'your-user-id' with your actual user ID (check auth.users table)
-- 3. Run the script
-- 4. Your dashboard should now show real data!