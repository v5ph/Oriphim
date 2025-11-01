# Send Alert Edge Function

This Supabase Edge Function handles multi-channel alert notifications for the Oriphim trading platform.

## Features

- **Multi-channel support**: Email, Telegram, Discord
- **User preference filtering**: Respects individual notification settings
- **Quiet hours**: Suppresses non-critical alerts during configured hours
- **Alert type categorization**: Entry, exit, risk, error, connection alerts
- **Proper error handling**: Graceful fallbacks and logging

## Deployment

```bash
supabase functions deploy send-alert
```

## Environment Variables

Set these in your Supabase project settings:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `RESEND_API_KEY`: Your Resend API key for email notifications
- `SUPABASE_URL`: Your Supabase project URL  
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for database access

## Usage

The function is automatically triggered by database triggers when:
- Trading runs start/stop/fail
- P&L crosses risk thresholds
- Runner connectivity changes
- Broker connections are lost

Manual testing:
```javascript
const { data, error } = await supabase.functions.invoke('send-alert', {
  body: {
    type: 'test',
    title: 'Test Alert',
    message: 'This is a test notification',
    severity: 'info',
    data: { timestamp: new Date().toISOString() }
  }
})
```

## Alert Types

- `entry`: New positions opened
- `exit`: Positions closed  
- `risk`: Large losses or margin issues
- `error`: System failures
- `connection`: Connectivity status changes
- `test`: Manual test alerts