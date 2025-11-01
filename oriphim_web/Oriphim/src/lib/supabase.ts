import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL!
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types based on existing schema
export type Database = {
  public: {
    Tables: {
      bots: {
        Row: {
          id: string
          user_id: string
          kind: 'putlite' | 'buywrite' | 'condor' | 'gammaburst'
          name: string
          config_json: any
          is_enabled: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          user_id: string
          kind: 'putlite' | 'buywrite' | 'condor' | 'gammaburst'
          name: string
          config_json?: any
          is_enabled?: boolean
        }
        Update: {
          name?: string
          config_json?: any
          is_enabled?: boolean
        }
      }
      runs: {
        Row: {
          id: string
          user_id: string
          bot_id: string
          mode: 'paper' | 'live'
          status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped'
          pnl: number
          max_drawdown: number
          trades_count: number
          win_rate: number
          started_at: string
          ended_at: string | null
          error_message: string | null
          metadata: any
        }
        Insert: {
          user_id: string
          bot_id: string
          mode?: 'paper' | 'live'
          status?: 'pending' | 'running' | 'completed' | 'failed' | 'stopped'
          pnl?: number
          max_drawdown?: number
          trades_count?: number
          win_rate?: number
          error_message?: string | null
          metadata?: any
        }
        Update: {
          status?: 'pending' | 'running' | 'completed' | 'failed' | 'stopped'
          pnl?: number
          max_drawdown?: number
          trades_count?: number
          win_rate?: number
          ended_at?: string | null
          error_message?: string | null
          metadata?: any
        }
      }
      run_logs: {
        Row: {
          id: string
          run_id: string
          ts: string
          level: 'debug' | 'info' | 'warning' | 'error'
          message: string
          context: any
        }
        Insert: {
          run_id: string
          level?: 'debug' | 'info' | 'warning' | 'error'
          message: string
          context?: any
        }
      }
      api_keys: {
        Row: {
          id: string
          user_id: string
          token: string
          name: string
          last_used_at: string | null
          created_at: string
          revoked_at: string | null
        }
        Insert: {
          user_id: string
          token: string
          name?: string
        }
        Update: {
          name?: string
          last_used_at?: string | null
          revoked_at?: string | null
        }
      }
      external_api_keys: {
        Row: {
          id: string
          user_id: string
          provider: 'ibkr' | 'tradier' | 'alpaca' | 'td_ameritrade' | 'schwab'
          environment: 'paper' | 'live'
          name: string
          credentials: any
          is_active: boolean
          last_used_at: string | null
          expires_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          user_id: string
          provider: 'ibkr' | 'tradier' | 'alpaca' | 'td_ameritrade' | 'schwab'
          environment?: 'paper' | 'live'
          name: string
          credentials: any
          is_active?: boolean
          expires_at?: string | null
        }
        Update: {
          name?: string
          credentials?: any
          is_active?: boolean
          last_used_at?: string | null
          expires_at?: string | null
        }
      }
      plans: {
        Row: {
          user_id: string
          tier: 'free' | 'pro' | 'enterprise'
          stripe_customer_id: string | null
          stripe_subscription_id: string | null
          current_period_start: string | null
          current_period_end: string | null
          trial_end: string | null
          canceled_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          user_id: string
          tier?: 'free' | 'pro' | 'enterprise'
          stripe_customer_id?: string | null
          stripe_subscription_id?: string | null
          current_period_start?: string | null
          current_period_end?: string | null
          trial_end?: string | null
        }
        Update: {
          tier?: 'free' | 'pro' | 'enterprise'
          stripe_customer_id?: string | null
          stripe_subscription_id?: string | null
          current_period_start?: string | null
          current_period_end?: string | null
          trial_end?: string | null
          canceled_at?: string | null
        }
      }
      waitlist: {
        Row: {
          id: string
          email: string
          created_at: string
          status: string
          source: string | null
          metadata: any
        }
        Insert: {
          email: string
          status?: string
          source?: string | null
          metadata?: any
        }
      }
      contact_messages: {
        Row: {
          id: string
          name: string
          email: string
          message: string
          status: string
          created_at: string
          responded_at: string | null
          response: string | null
        }
        Insert: {
          name: string
          email: string
          message: string
          status?: string
        }
        Update: {
          status?: string
          responded_at?: string | null
          response?: string | null
        }
      }
      alert_preferences: {
        Row: {
          user_id: string
          email_enabled: boolean
          telegram_enabled: boolean
          discord_enabled: boolean
          telegram_chat_id: string | null
          discord_webhook_url: string | null
          alert_types: any
          created_at: string
          updated_at: string
        }
        Insert: {
          user_id: string
          email_enabled?: boolean
          telegram_enabled?: boolean
          discord_enabled?: boolean
          telegram_chat_id?: string | null
          discord_webhook_url?: string | null
          alert_types?: any
        }
        Update: {
          email_enabled?: boolean
          telegram_enabled?: boolean
          discord_enabled?: boolean
          telegram_chat_id?: string | null
          discord_webhook_url?: string | null
          alert_types?: any
        }
      }
      runner_status: {
        Row: {
          id: string
          user_id: string
          api_key_id: string
          is_connected: boolean
          machine_name: string | null
          runner_version: string | null
          last_heartbeat: string
          broker_connected: boolean | null
          broker_name: string | null
          market_session: string | null
          active_bots: number | null
          system_info: any
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          api_key_id: string
          is_connected?: boolean
          machine_name?: string | null
          runner_version?: string | null
          last_heartbeat?: string
          broker_connected?: boolean | null
          broker_name?: string | null
          market_session?: string | null
          active_bots?: number | null
          system_info?: any
          created_at?: string
          updated_at?: string
        }
        Update: {
          is_connected?: boolean
          machine_name?: string | null
          runner_version?: string | null
          last_heartbeat?: string
          broker_connected?: boolean | null
          broker_name?: string | null
          market_session?: string | null
          active_bots?: number | null
          system_info?: any
          updated_at?: string
        }
      }
      positions: {
        Row: {
          id: string
          user_id: string
          run_id: string
          symbol: string
          position_type: string
          side: string
          quantity: number
          entry_price: number | null
          current_price: number | null
          unrealized_pnl: number | null
          realized_pnl: number | null
          opened_at: string
          closed_at: string | null
          contract_details: any
          entry_reason: string | null
          exit_reason: string | null
        }
        Insert: {
          id?: string
          user_id: string
          run_id: string
          symbol: string
          position_type: string
          side: string
          quantity: number
          entry_price?: number | null
          current_price?: number | null
          unrealized_pnl?: number | null
          realized_pnl?: number | null
          opened_at?: string
          closed_at?: string | null
          contract_details?: any
          entry_reason?: string | null
          exit_reason?: string | null
        }
        Update: {
          current_price?: number | null
          unrealized_pnl?: number | null
          realized_pnl?: number | null
          closed_at?: string | null
          exit_reason?: string | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      bot_kind: 'putlite' | 'buywrite' | 'condor' | 'gammaburst'
      run_status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped'
      run_mode: 'paper' | 'live'
      log_level: 'debug' | 'info' | 'warning' | 'error'
      plan_tier: 'free' | 'pro' | 'enterprise'
    }
  }
}

export type Bot = Database['public']['Tables']['bots']['Row']
export type BotInsert = Database['public']['Tables']['bots']['Insert']
export type BotUpdate = Database['public']['Tables']['bots']['Update']

export type Run = Database['public']['Tables']['runs']['Row']
export type RunInsert = Database['public']['Tables']['runs']['Insert']
export type RunUpdate = Database['public']['Tables']['runs']['Update']

export type RunLog = Database['public']['Tables']['run_logs']['Row']
export type RunLogInsert = Database['public']['Tables']['run_logs']['Insert']

export type ApiKey = Database['public']['Tables']['api_keys']['Row']
export type ApiKeyInsert = Database['public']['Tables']['api_keys']['Insert']
export type ApiKeyUpdate = Database['public']['Tables']['api_keys']['Update']

export type Plan = Database['public']['Tables']['plans']['Row']
export type PlanInsert = Database['public']['Tables']['plans']['Insert']
export type PlanUpdate = Database['public']['Tables']['plans']['Update']

export type WaitlistEntry = Database['public']['Tables']['waitlist']['Row']
export type WaitlistInsert = Database['public']['Tables']['waitlist']['Insert']

export type ContactMessage = Database['public']['Tables']['contact_messages']['Row']
export type ContactMessageInsert = Database['public']['Tables']['contact_messages']['Insert']
export type ContactMessageUpdate = Database['public']['Tables']['contact_messages']['Update']

export type AlertPreferences = Database['public']['Tables']['alert_preferences']['Row']
export type AlertPreferencesInsert = Database['public']['Tables']['alert_preferences']['Insert']
export type AlertPreferencesUpdate = Database['public']['Tables']['alert_preferences']['Update']

export type RunnerStatus = Database['public']['Tables']['runner_status']['Row']
export type RunnerStatusInsert = Database['public']['Tables']['runner_status']['Insert']
export type RunnerStatusUpdate = Database['public']['Tables']['runner_status']['Update']

export type Position = Database['public']['Tables']['positions']['Row']
export type PositionInsert = Database['public']['Tables']['positions']['Insert']
export type PositionUpdate = Database['public']['Tables']['positions']['Update']