import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Bell, MessageSquare, Mail, Telegram, Bot, Save, TestTube, Key } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { supabase } from '@/lib/supabase'
import { toast } from 'sonner'

export default function Settings() {
  const [apiKeys, setApiKeys] = useState({
    interactiveBrokers: { port: '7497', clientId: '1' },
    telegram: { botToken: '', chatId: '' },
    discord: { webhookUrl: '' }
  })

  const [alertSettings, setAlertSettings] = useState({
    emailEnabled: true,
    telegramEnabled: false,
    discordEnabled: false,
    alertTypes: {
      entry: true,
      exit: true,
      risk: true,
      error: true,
      connection: true
    },
    quietHours: {
      enabled: false,
      startTime: '22:00',
      endTime: '07:00'
    }
  })

  const [loading, setLoading] = useState(false)
  const [testingAlert, setTestingAlert] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      // Load API keys
      const { data: keys } = await supabase
        .from('api_keys')
        .select('*')
        .eq('user_id', user.id)

      if (keys) {
        const keyMap = keys.reduce((acc: any, key) => {
          const service = key.service
          if (!acc[service]) acc[service] = {}
          acc[service][key.key_name] = key.encrypted_value
          return acc
        }, {})
        setApiKeys(prev => ({ ...prev, ...keyMap }))
      }

      // Load alert preferences from user metadata
      const alertPrefs = user.user_metadata?.alert_preferences
      if (alertPrefs) {
        setAlertSettings(prev => ({ ...prev, ...alertPrefs }))
      }

    } catch (error) {
      console.error('Error loading settings:', error)
      toast.error('Failed to load settings')
    }
  }

  const saveApiKey = async (service: string, keyName: string, value: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { error } = await supabase
        .from('api_keys')
        .upsert({
          user_id: user.id,
          service,
          key_name: keyName,
          encrypted_value: value
        })

      if (error) throw error
      toast.success('API key saved successfully')
    } catch (error) {
      console.error('Error saving API key:', error)
      toast.error('Failed to save API key')
    }
  }

  const saveAlertSettings = async () => {
    setLoading(true)
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { error } = await supabase.auth.updateUser({
        data: {
          alert_preferences: alertSettings
        }
      })

      if (error) throw error
      toast.success('Alert settings saved successfully')
    } catch (error) {
      console.error('Error saving alert settings:', error)
      toast.error('Failed to save alert settings')
    } finally {
      setLoading(false)
    }
  }

  const testAlert = async () => {
    setTestingAlert(true)
    try {
      const { data, error } = await supabase.functions.invoke('send-alert', {
        body: {
          type: 'test',
          title: 'Test Alert',
          message: 'This is a test alert to verify your notification settings.',
          severity: 'info',
          data: { timestamp: new Date().toISOString() }
        }
      })

      if (error) throw error
      toast.success('Test alert sent successfully')
    } catch (error) {
      console.error('Error sending test alert:', error)
      toast.error('Failed to send test alert')
    } finally {
      setTestingAlert(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Settings</h3>
        <p className="text-sm text-muted-foreground">
          Configure your trading automation and notification preferences.
        </p>
      </div>

      <Tabs defaultValue="api-keys" className="space-y-4">
        <TabsList>
          <TabsTrigger value="api-keys" className="flex items-center gap-2">
            <Key className="w-4 h-4" />
            API Keys
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Alerts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys" className="space-y-4">
          {/* Interactive Brokers Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                Interactive Brokers
              </CardTitle>
              <CardDescription>
                Configure connection to IBKR Trader Workstation (TWS)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ib-port">TWS Port</Label>
                  <Input
                    id="ib-port"
                    value={apiKeys.interactiveBrokers.port}
                    onChange={(e) => setApiKeys(prev => ({
                      ...prev,
                      interactiveBrokers: { ...prev.interactiveBrokers, port: e.target.value }
                    }))}
                    placeholder="7497 for Paper, 7496 for Live"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ib-client">Client ID</Label>
                  <Input
                    id="ib-client"
                    value={apiKeys.interactiveBrokers.clientId}
                    onChange={(e) => setApiKeys(prev => ({
                      ...prev,
                      interactiveBrokers: { ...prev.interactiveBrokers, clientId: e.target.value }
                    }))}
                    placeholder="Unique client ID (1-999)"
                  />
                </div>
              </div>
              <Button 
                onClick={() => {
                  saveApiKey('interactiveBrokers', 'port', apiKeys.interactiveBrokers.port)
                  saveApiKey('interactiveBrokers', 'clientId', apiKeys.interactiveBrokers.clientId)
                }}
                className="w-full"
              >
                <Save className="w-4 h-4 mr-2" />
                Save IB Settings
              </Button>
            </CardContent>
          </Card>

          {/* Telegram Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Telegram
              </CardTitle>
              <CardDescription>
                Configure Telegram bot for alert notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="telegram-token">Bot Token</Label>
                <Input
                  id="telegram-token"
                  type="password"
                  value={apiKeys.telegram.botToken}
                  onChange={(e) => setApiKeys(prev => ({
                    ...prev,
                    telegram: { ...prev.telegram, botToken: e.target.value }
                  }))}
                  placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telegram-chat">Chat ID</Label>
                <Input
                  id="telegram-chat"
                  value={apiKeys.telegram.chatId}
                  onChange={(e) => setApiKeys(prev => ({
                    ...prev,
                    telegram: { ...prev.telegram, chatId: e.target.value }
                  }))}
                  placeholder="-1001234567890"
                />
              </div>
              <Button 
                onClick={() => {
                  saveApiKey('telegram', 'botToken', apiKeys.telegram.botToken)
                  saveApiKey('telegram', 'chatId', apiKeys.telegram.chatId)
                }}
                className="w-full"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Telegram Settings
              </Button>
            </CardContent>
          </Card>

          {/* Discord Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                Discord
              </CardTitle>
              <CardDescription>
                Configure Discord webhook for alert notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="discord-webhook">Webhook URL</Label>
                <Input
                  id="discord-webhook"
                  type="password"
                  value={apiKeys.discord.webhookUrl}
                  onChange={(e) => setApiKeys(prev => ({
                    ...prev,
                    discord: { ...prev.discord, webhookUrl: e.target.value }
                  }))}
                  placeholder="https://discord.com/api/webhooks/..."
                />
              </div>
              <Button 
                onClick={() => saveApiKey('discord', 'webhookUrl', apiKeys.discord.webhookUrl)}
                className="w-full"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Discord Settings
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          {/* Alert Channels */}
          <Card>
            <CardHeader>
              <CardTitle>Notification Channels</CardTitle>
              <CardDescription>
                Enable or disable different notification methods
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5" />
                  <div>
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Sent to your account email</p>
                  </div>
                </div>
                <Switch
                  checked={alertSettings.emailEnabled}
                  onCheckedChange={(checked) => setAlertSettings(prev => ({
                    ...prev,
                    emailEnabled: checked
                  }))}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Telegram className="w-5 h-5" />
                  <div>
                    <Label>Telegram Notifications</Label>
                    <p className="text-sm text-muted-foreground">Real-time messages via Telegram bot</p>
                  </div>
                </div>
                <Switch
                  checked={alertSettings.telegramEnabled}
                  onCheckedChange={(checked) => setAlertSettings(prev => ({
                    ...prev,
                    telegramEnabled: checked
                  }))}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="w-5 h-5" />
                  <div>
                    <Label>Discord Notifications</Label>
                    <p className="text-sm text-muted-foreground">Messages to Discord channel</p>
                  </div>
                </div>
                <Switch
                  checked={alertSettings.discordEnabled}
                  onCheckedChange={(checked) => setAlertSettings(prev => ({
                    ...prev,
                    discordEnabled: checked
                  }))}
                />
              </div>
            </CardContent>
          </Card>

          {/* Alert Types */}
          <Card>
            <CardHeader>
              <CardTitle>Alert Types</CardTitle>
              <CardDescription>
                Choose which types of events trigger notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries({
                entry: { label: 'Trade Entry', desc: 'When a new position is opened', severity: 'info' },
                exit: { label: 'Trade Exit', desc: 'When a position is closed', severity: 'success' },
                risk: { label: 'Risk Alerts', desc: 'Large losses or margin calls', severity: 'warning' },
                error: { label: 'System Errors', desc: 'Bot failures or connection issues', severity: 'error' },
                connection: { label: 'Connection Status', desc: 'Runner or broker connectivity', severity: 'info' }
              }).map(([key, config]) => (
                <div key={key} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant={config.severity === 'error' ? 'destructive' : 
                                   config.severity === 'warning' ? 'outline' : 'default'}>
                      {config.label}
                    </Badge>
                    <div>
                      <p className="text-sm text-muted-foreground">{config.desc}</p>
                    </div>
                  </div>
                  <Switch
                    checked={alertSettings.alertTypes[key as keyof typeof alertSettings.alertTypes]}
                    onCheckedChange={(checked) => setAlertSettings(prev => ({
                      ...prev,
                      alertTypes: { ...prev.alertTypes, [key]: checked }
                    }))}
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Quiet Hours */}
          <Card>
            <CardHeader>
              <CardTitle>Quiet Hours</CardTitle>
              <CardDescription>
                Suppress non-critical notifications during specified hours
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Enable Quiet Hours</Label>
                <Switch
                  checked={alertSettings.quietHours.enabled}
                  onCheckedChange={(checked) => setAlertSettings(prev => ({
                    ...prev,
                    quietHours: { ...prev.quietHours, enabled: checked }
                  }))}
                />
              </div>

              {alertSettings.quietHours.enabled && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="quiet-start">Start Time</Label>
                    <Input
                      id="quiet-start"
                      type="time"
                      value={alertSettings.quietHours.startTime}
                      onChange={(e) => setAlertSettings(prev => ({
                        ...prev,
                        quietHours: { ...prev.quietHours, startTime: e.target.value }
                      }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="quiet-end">End Time</Label>
                    <Input
                      id="quiet-end"
                      type="time"
                      value={alertSettings.quietHours.endTime}
                      onChange={(e) => setAlertSettings(prev => ({
                        ...prev,
                        quietHours: { ...prev.quietHours, endTime: e.target.value }
                      }))}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Save and Test */}
          <div className="flex gap-3">
            <Button onClick={saveAlertSettings} disabled={loading} className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              {loading ? 'Saving...' : 'Save Alert Settings'}
            </Button>
            <Button 
              variant="outline" 
              onClick={testAlert} 
              disabled={testingAlert}
              className="flex items-center gap-2"
            >
              <TestTube className="w-4 h-4" />
              {testingAlert ? 'Sending...' : 'Test Alert'}
            </Button>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Test alerts will be sent to all enabled channels. Make sure you've configured 
              your API keys first in the API Keys tab.
            </AlertDescription>
          </Alert>
        </TabsContent>
      </Tabs>
    </div>
  )
}