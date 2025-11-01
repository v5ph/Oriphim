import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { 
        global: { 
          headers: { Authorization: req.headers.get('Authorization')! } 
        } 
      }
    )

    // Get user from JWT token
    const { data: { user } } = await supabaseClient.auth.getUser()
    
    if (!user) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Parse request body
    const { bot_id, mode = 'paper', config_override = {} } = await req.json()

    if (!bot_id) {
      return new Response(
        JSON.stringify({ error: 'bot_id is required' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Verify bot belongs to user
    const { data: bot, error: botError } = await supabaseClient
      .from('bots')
      .select('*')
      .eq('id', bot_id)
      .eq('user_id', user.id)
      .single()

    if (botError || !bot) {
      return new Response(
        JSON.stringify({ error: 'Bot not found or access denied' }),
        { 
          status: 404, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Check if bot is enabled
    if (!bot.is_enabled) {
      return new Response(
        JSON.stringify({ error: 'Bot is disabled' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Check plan restrictions for live mode
    if (mode === 'live') {
      const { data: plan } = await supabaseClient
        .from('plans')
        .select('tier')
        .eq('user_id', user.id)
        .single()

      if (!plan || plan.tier === 'free') {
        return new Response(
          JSON.stringify({ error: 'Live trading requires Pro plan' }),
          { 
            status: 403, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }
    }

    // Check for existing running bot of same type
    const { data: existingRuns } = await supabaseClient
      .from('runs')
      .select('id')
      .eq('user_id', user.id)
      .eq('bot_id', bot_id)
      .eq('status', 'running')

    if (existingRuns && existingRuns.length > 0) {
      return new Response(
        JSON.stringify({ error: 'Bot is already running' }),
        { 
          status: 409, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Merge bot config with any overrides
    const final_config = { ...bot.config_json, ...config_override }

    // Create new run record
    const { data: run, error: runError } = await supabaseClient
      .from('runs')
      .insert({
        user_id: user.id,
        bot_id: bot_id,
        mode: mode,
        status: 'pending',
        metadata: {
          bot_kind: bot.kind,
          config: final_config,
          started_from: 'dashboard'
        }
      })
      .select()
      .single()

    if (runError) {
      console.error('Error creating run:', runError)
      return new Response(
        JSON.stringify({ error: 'Failed to create run' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Send notification to Runner via realtime channel
    const channel = `jobs:${user.id}`
    await supabaseClient.realtime.channel(channel).send({
      type: 'broadcast',
      event: 'start_bot',
      payload: {
        run_id: run.id,
        bot_kind: bot.kind,
        mode: mode,
        config: final_config
      }
    })

    // Log the start event
    await supabaseClient
      .from('run_logs')
      .insert({
        run_id: run.id,
        level: 'info',
        message: `Bot ${bot.name} (${bot.kind}) starting in ${mode} mode`,
        context: { 
          action: 'start_requested',
          source: 'dashboard'
        }
      })

    return new Response(
      JSON.stringify({ 
        success: true, 
        run_id: run.id,
        message: `Bot ${bot.name} start request sent to Runner`
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Unexpected error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})