import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"
import { create, verify } from "https://deno.land/x/djwt@v2.8/mod.ts"

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
    // Initialize Supabase client with service key for API key validation
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Parse request body
    const { api_key } = await req.json()

    if (!api_key) {
      return new Response(
        JSON.stringify({ error: 'api_key is required' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Validate API key and get user info
    const { data: apiKeyData, error: apiKeyError } = await supabaseClient
      .from('api_keys')
      .select('user_id, name, last_used_at, revoked_at')
      .eq('token', api_key)
      .single()

    if (apiKeyError || !apiKeyData) {
      return new Response(
        JSON.stringify({ error: 'Invalid API key' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Check if API key is revoked
    if (apiKeyData.revoked_at) {
      return new Response(
        JSON.stringify({ error: 'API key has been revoked' }),
        { 
          status: 401, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Update last_used_at timestamp
    await supabaseClient
      .from('api_keys')
      .update({ last_used_at: new Date().toISOString() })
      .eq('token', api_key)

    // Get user details
    const { data: userData, error: userError } = await supabaseClient.auth.admin
      .getUserById(apiKeyData.user_id)

    if (userError || !userData.user) {
      return new Response(
        JSON.stringify({ error: 'User not found' }),
        { 
          status: 404, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Get user plan for access control
    const { data: planData } = await supabaseClient
      .from('plans')
      .select('tier')
      .eq('user_id', apiKeyData.user_id)
      .single()

    // Create JWT token for Runner authentication
    const jwtSecret = Deno.env.get('SUPABASE_JWT_SECRET')
    if (!jwtSecret) {
      throw new Error('JWT secret not configured')
    }

    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(jwtSecret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign', 'verify']
    )

    const now = Math.floor(Date.now() / 1000)
    const payload = {
      sub: apiKeyData.user_id,
      email: userData.user.email,
      aud: 'oriphim-runner',
      exp: now + (24 * 60 * 60), // 24 hours
      iat: now,
      iss: 'oriphim-cloud',
      plan_tier: planData?.tier || 'free',
      device_name: apiKeyData.name
    }

    const jwt = await create({ alg: 'HS256', typ: 'JWT' }, payload, key)

    return new Response(
      JSON.stringify({
        success: true,
        token: jwt,
        user_id: apiKeyData.user_id,
        email: userData.user.email,
        plan_tier: planData?.tier || 'free',
        device_name: apiKeyData.name,
        expires_at: new Date((now + 24 * 60 * 60) * 1000).toISOString()
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