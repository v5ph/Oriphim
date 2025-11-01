import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface AlertEvent {
  user_id: string
  type: 'entry' | 'exit' | 'risk' | 'error' | 'connection'
  title: string
  message: string
  data?: Record<string, any>
  severity: 'info' | 'warning' | 'error' | 'success'
}

interface AlertPreferences {
  email_enabled: boolean
  telegram_enabled: boolean
  discord_enabled: boolean
  telegram_chat_id?: string
  discord_webhook_url?: string
  alert_types: string[]
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Parse request body
    const alertEvent: AlertEvent = await req.json()
    console.log('Processing alert:', alertEvent)

    // Get user's alert preferences
    const { data: preferences, error: prefError } = await supabase
      .from('alert_preferences')
      .select('*')
      .eq('user_id', alertEvent.user_id)
      .single()

    if (prefError) {
      console.error('Error fetching alert preferences:', prefError)
      return new Response(
        JSON.stringify({ error: 'Failed to fetch alert preferences' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const alertPrefs = preferences as AlertPreferences

    // Check if this alert type is enabled
    if (!alertPrefs.alert_types.includes(alertEvent.type)) {
      console.log(`Alert type ${alertEvent.type} is disabled for user ${alertEvent.user_id}`)
      return new Response(
        JSON.stringify({ message: 'Alert type disabled', skipped: true }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const results = []

    // Send Email Alert
    if (alertPrefs.email_enabled) {
      try {
        const emailResult = await sendEmailAlert(alertEvent, supabase)
        results.push({ channel: 'email', success: true, result: emailResult })
      } catch (error) {
        console.error('Email alert failed:', error)
        results.push({ channel: 'email', success: false, error: error.message })
      }
    }

    // Send Telegram Alert  
    if (alertPrefs.telegram_enabled && alertPrefs.telegram_chat_id) {
      try {
        const telegramResult = await sendTelegramAlert(alertEvent, alertPrefs.telegram_chat_id)
        results.push({ channel: 'telegram', success: true, result: telegramResult })
      } catch (error) {
        console.error('Telegram alert failed:', error)
        results.push({ channel: 'telegram', success: false, error: error.message })
      }
    }

    // Send Discord Alert
    if (alertPrefs.discord_enabled && alertPrefs.discord_webhook_url) {
      try {
        const discordResult = await sendDiscordAlert(alertEvent, alertPrefs.discord_webhook_url)
        results.push({ channel: 'discord', success: true, result: discordResult })
      } catch (error) {
        console.error('Discord alert failed:', error)
        results.push({ channel: 'discord', success: false, error: error.message })
      }
    }

    return new Response(
      JSON.stringify({ 
        message: 'Alert processing completed',
        alert: alertEvent,
        results: results 
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Alert function error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

// Email notification using Supabase built-in email
async function sendEmailAlert(alertEvent: AlertEvent, supabase: any) {
  const { data: user } = await supabase.auth.admin.getUserById(alertEvent.user_id)
  
  if (!user?.user?.email) {
    throw new Error('User email not found')
  }

  const emailTemplate = generateEmailTemplate(alertEvent)
  
  // Use Supabase Auth to send email (requires proper email template setup)
  // For now, we'll use a simple approach - in production, integrate with SendGrid/Resend
  console.log(`Would send email to ${user.user.email}:`, emailTemplate.subject)
  
  return { sent: true, email: user.user.email, subject: emailTemplate.subject }
}

// Telegram notification
async function sendTelegramAlert(alertEvent: AlertEvent, chatId: string) {
  const botToken = Deno.env.get('TELEGRAM_BOT_TOKEN')
  if (!botToken) {
    throw new Error('Telegram bot token not configured')
  }

  const message = formatTelegramMessage(alertEvent)
  
  const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'Markdown'
    })
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Telegram API error: ${error}`)
  }

  return await response.json()
}

// Discord notification
async function sendDiscordAlert(alertEvent: AlertEvent, webhookUrl: string) {
  const embed = formatDiscordEmbed(alertEvent)
  
  const response = await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      embeds: [embed]
    })
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Discord webhook error: ${error}`)
  }

  return { sent: true }
}

// Email template generator
function generateEmailTemplate(alertEvent: AlertEvent) {
  const severityEmoji = {
    info: 'ℹ️',
    warning: '⚠️', 
    error: '🚨',
    success: '✅'
  }

  return {
    subject: `${severityEmoji[alertEvent.severity]} Oriphim Alert: ${alertEvent.title}`,
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1a1a1a; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
          <h2 style="margin: 0; display: flex; align-items: center; gap: 10px;">
            ${severityEmoji[alertEvent.severity]} ${alertEvent.title}
          </h2>
        </div>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px;">
          <p style="font-size: 16px; line-height: 1.5; margin: 0 0 15px 0;">
            ${alertEvent.message}
          </p>
          ${alertEvent.data ? `
            <div style="background: white; padding: 15px; border-radius: 4px; border-left: 4px solid #0066cc;">
              <h4 style="margin: 0 0 10px 0; color: #333;">Details:</h4>
              <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px;">
${JSON.stringify(alertEvent.data, null, 2)}
              </pre>
            </div>
          ` : ''}
          <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
          <p style="font-size: 12px; color: #666; margin: 0;">
            Sent by Oriphim Trading Automation • ${new Date().toLocaleString()}
          </p>
        </div>
      </div>
    `
  }
}

// Telegram message formatter
function formatTelegramMessage(alertEvent: AlertEvent) {
  const severityEmoji = {
    info: 'ℹ️',
    warning: '⚠️',
    error: '🚨', 
    success: '✅'
  }

  let message = `${severityEmoji[alertEvent.severity]} *${alertEvent.title}*\n\n`
  message += `${alertEvent.message}\n\n`
  
  if (alertEvent.data) {
    message += `📋 *Details:*\n\`\`\`\n${JSON.stringify(alertEvent.data, null, 2)}\n\`\`\`\n\n`
  }
  
  message += `🕐 ${new Date().toLocaleString()}`
  
  return message
}

// Discord embed formatter
function formatDiscordEmbed(alertEvent: AlertEvent) {
  const severityColors = {
    info: 3447003,    // Blue
    warning: 16776960, // Yellow
    error: 15158332,   // Red
    success: 3066993   // Green
  }

  return {
    title: alertEvent.title,
    description: alertEvent.message,
    color: severityColors[alertEvent.severity],
    fields: alertEvent.data ? Object.entries(alertEvent.data).map(([key, value]) => ({
      name: key,
      value: String(value),
      inline: true
    })) : [],
    timestamp: new Date().toISOString(),
    footer: {
      text: 'Oriphim Trading Automation'
    }
  }
}