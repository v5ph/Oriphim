# Alert System Architecture

The Oriphim platform includes a comprehensive multi-channel alert system that provides real-time notifications for trading events and system status changes.

## Overview

The alert system follows the Runner-First architecture principle:
- **Local Processing**: Runner processes trades locally and pushes minimal events to cloud
- **Event-Driven Alerts**: Database triggers automatically fire notifications on key events
- **Multi-Channel Delivery**: Supports Email, Telegram, and Discord notifications
- **User Preferences**: Respects individual notification settings and quiet hours

## Components

### 1. Database Triggers (`schema.sql`)

Automatic triggers monitor these tables for alert-worthy events:
- `runs`: Trade execution start/stop/failure, P&L changes
- `runner_status`: Connectivity changes, broker disconnections

### 2. Supabase Edge Function (`send-alert/index.ts`)  

Serverless function that:
- Receives alert payloads from database triggers
- Filters based on user preferences
- Formats messages for each channel
- Delivers notifications via multiple providers

### 3. Settings UI (`Settings.tsx`)

User interface for configuring:
- API keys (Interactive Brokers, Telegram, Discord)
- Notification channel preferences
- Alert type filtering
- Quiet hours settings

## Alert Types

| Type | Description | Severity | Example |
|------|-------------|----------|---------|
| `entry` | New position opened | Info | "Bot started SPY Put spread" |
| `exit` | Position closed | Success/Info | "Position closed +$45.50 P&L" |
| `risk` | Large loss threshold | Warning | "P&L dropped to -$120" |
| `error` | System failures | Error | "Bot run failed: Connection timeout" |
| `connection` | Connectivity status | Success/Warning | "Runner disconnected" |

## Configuration

### Database Settings

```sql
-- Configure app settings for Edge Function calls
ALTER DATABASE postgres SET "app.supabase_url" = 'https://your-project.supabase.co';
ALTER DATABASE postgres SET "app.supabase_service_role_key" = 'your-service-role-key';
```

### Environment Variables

Set in Supabase project settings:
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `RESEND_API_KEY`: Email delivery service API key
- `SUPABASE_URL`: Project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key

### User Preferences

Stored in `auth.users.user_metadata.alert_preferences`:
```json
{
  "emailEnabled": true,
  "telegramEnabled": false,
  "discordEnabled": false,
  "alertTypes": {
    "entry": true,
    "exit": true,
    "risk": true,
    "error": true,
    "connection": true
  },
  "quietHours": {
    "enabled": false,
    "startTime": "22:00",
    "endTime": "07:00"
  }
}
```

## Data Flow

1. **Event Occurs**: Runner executes trade, status changes
2. **Database Update**: Minimal event data inserted into cloud tables  
3. **Trigger Fires**: PostgreSQL trigger detects relevant changes
4. **Alert Generated**: Trigger function builds alert payload
5. **Edge Function Called**: HTTP request to `send-alert` function
6. **User Filtering**: Function checks user preferences and quiet hours
7. **Multi-Channel Delivery**: Notifications sent via enabled channels
8. **Error Handling**: Failed deliveries logged for retry

## Cost Optimization

Following the Runner-First model:
- **Minimal Data**: Only essential events stored in cloud
- **Serverless Processing**: Edge Functions scale to zero when idle  
- **Selective Notifications**: User preferences prevent spam
- **Batch Processing**: Multiple alerts can be combined

## Testing

Use the Settings UI "Test Alert" button or call directly:

```javascript
const { data, error } = await supabase.functions.invoke('send-alert', {
  body: {
    type: 'test',
    title: 'Test Notification',
    message: 'Verifying alert system functionality',
    severity: 'info',
    data: { source: 'manual_test' }
  }
})
```

## Monitoring

Key metrics to track:
- Alert delivery success rates by channel
- User engagement with notifications  
- Edge Function execution times
- Database trigger performance

## Security

- API keys encrypted in database
- Service role key restricted to Edge Functions
- User preferences enforce access control
- No sensitive trading data in alert messages

## Future Enhancements

- SMS notifications via Twilio
- Push notifications for mobile app
- Alert escalation for critical failures
- Machine learning for alert priority scoring
- Integration with Slack, Microsoft Teams