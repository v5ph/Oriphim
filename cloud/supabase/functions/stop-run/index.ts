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
    const { run_id } = await req.json()

    if (!run_id) {
      return new Response(
        JSON.stringify({ error: 'run_id is required' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Verify run belongs to user and is running
    const { data: run, error: runError } = await supabaseClient
      .from('runs')
      .select('*, bots(name, kind)')
      .eq('id', run_id)
      .eq('user_id', user.id)
      .single()

    if (runError || !run) {
      return new Response(
        JSON.stringify({ error: 'Run not found or access denied' }),
        { 
          status: 404, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Check if run can be stopped
    if (!['pending', 'running'].includes(run.status)) {
      return new Response(
        JSON.stringify({ error: `Cannot stop run in ${run.status} status` }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Update run status to indicate stop requested
    const { error: updateError } = await supabaseClient
      .from('runs')
      .update({ 
        status: 'stopping',
        metadata: {
          ...run.metadata,
          stop_requested_at: new Date().toISOString(),
          stop_requested_by: 'dashboard'
        }
      })
      .eq('id', run_id)

    if (updateError) {
      console.error('Error updating run status:', updateError)
      return new Response(
        JSON.stringify({ error: 'Failed to update run status' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Send stop notification to Runner via realtime channel
    const channel = `jobs:${user.id}`
    await supabaseClient.realtime.channel(channel).send({
      type: 'broadcast',
      event: 'stop_bot',
      payload: {
        run_id: run.id,
        reason: 'user_requested'
      }
    })

    // Log the stop event
    await supabaseClient
      .from('run_logs')
      .insert({
        run_id: run.id,
        level: 'info',
        message: `Stop requested for ${run.bots.name} (${run.bots.kind})`,
        context: { 
          action: 'stop_requested',
          source: 'dashboard'
        }
      })

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: `Stop request sent for ${run.bots.name}`
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