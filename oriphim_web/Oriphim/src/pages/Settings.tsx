import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Bell, MessageSquare, Mail, Send, Bot, Save, Key, Plus, Copy, Trash } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { supabase } from '@/lib/supabase'
import { toast } from 'sonner'

export default function Settings() {
  // External API Keys (broker credentials)
  const [brokerKeys, setBrokerKeys] = useState({
    ibkr: { port: '7497', clientId: '1', name: 'Paper Trading' }
  })
  
  // Runner API Keys (device tokens)
  const [runnerKeys, setRunnerKeys] = useState<Array<{
    id: string
    name: string
    token: string
    created_at: string
    last_used_at?: string
  }>>([])
  
  // Alert settings (notification channels)
  const [alertSettings, setAlertSettings] = useState({
    emailEnabled: true,
    telegramEnabled: false,
    discordEnabled: false,
    telegram: { botToken: '', chatId: '' },
    discord: { webhookUrl: '' },
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
  const [generatingKey, setGeneratingKey] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      // Load external API keys (broker credentials)
      const { data: externalKeys } = await supabase
        .from('external_api_keys')
        .select('*')
        .eq('user_id', user.id)

      if (externalKeys && externalKeys.length > 0) {
        const ibkrKey = externalKeys.find(key => key.provider === 'ibkr')
        if (ibkrKey) {
          setBrokerKeys(prev => ({
            ...prev,
            ibkr: {
              ...prev.ibkr,
              ...ibkrKey.credentials,
              name: ibkrKey.name
            }
          }))
        }
      }

      // Load runner API keys (device tokens)
      const { data: runnerTokens } = await supabase
        .from('api_keys')
        .select('id, name, token, created_at, last_used_at')
        .eq('user_id', user.id)
        .is('revoked_at', null)
        .order('created_at', { ascending: false })

      if (runnerTokens) {
        setRunnerKeys(runnerTokens)
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

  const saveBrokerCredentials = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { error } = await supabase
        .from('external_api_keys')
        .upsert({
          user_id: user.id,
          provider: 'ibkr',
          environment: brokerKeys.ibkr.port === '7497' ? 'paper' : 'live',
          name: brokerKeys.ibkr.name,
          credentials: {
            port: brokerKeys.ibkr.port,
            clientId: brokerKeys.ibkr.clientId
          },
          is_active: true
        })

      if (error) throw error
      toast.success('Broker credentials saved successfully')
    } catch (error) {
      console.error('Error saving broker credentials:', error)
      toast.error('Failed to save broker credentials')
    }
  }

  const generateRunnerKey = async () => {
    setGeneratingKey(true)
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      // Generate a secure random token
      const token = Array.from(crypto.getRandomValues(new Uint8Array(32)))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')

      const deviceName = `Runner ${new Date().toLocaleDateString()}`

      const { data, error } = await supabase
        .from('api_keys')
        .insert({
          user_id: user.id,
          token: token,
          name: deviceName
        })
        .select('id, name, token, created_at')
        .single()

      if (error) throw error

      // Add to local state
      setRunnerKeys(prev => [data, ...prev])
      toast.success('Runner key generated successfully')

    } catch (error) {
      console.error('Error generating runner key:', error)
      toast.error('Failed to generate runner key')
    } finally {
      setGeneratingKey(false)
    }
  }

  const revokeRunnerKey = async (keyId: string) => {
    try {
      const { error } = await supabase
        .from('api_keys')
        .update({ revoked_at: new Date().toISOString() })
        .eq('id', keyId)

      if (error) throw error

      // Remove from local state
      setRunnerKeys(prev => prev.filter(key => key.id !== keyId))
      toast.success('Runner key revoked successfully')

    } catch (error) {
      console.error('Error revoking runner key:', error)
      toast.error('Failed to revoke runner key')
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Copied to clipboard')
    } catch (error) {
      toast.error('Failed to copy to clipboard')
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

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Settings</h3>
        <p className="text-sm text-muted-foreground">
          Configure your trading automation and notification preferences.
        </p>
      </div>

      <Tabs defaultValue="broker" className="space-y-4">
        <TabsList>
          <TabsTrigger value="broker" className="flex items-center gap-2">
            <Bot className="w-4 h-4" />
            Broker
          </TabsTrigger>
          <TabsTrigger value="runner" className="flex items-center gap-2">
            <Key className="w-4 h-4" />
            Runner Keys
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Alerts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="broker" className="space-y-4">
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
              <div className="space-y-2">
                <Label htmlFor="ib-name">Configuration Name</Label>
                <Input
                  id="ib-name"
                  value={brokerKeys.ibkr.name}
                  onChange={(e) => setBrokerKeys(prev => ({
                    ...prev,
                    ibkr: { ...prev.ibkr, name: e.target.value }
                  }))}
                  placeholder="e.g., Paper Trading"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ib-port">TWS Port</Label>
                  <Input
                    id="ib-port"
                    value={brokerKeys.ibkr.port}
                    onChange={(e) => setBrokerKeys(prev => ({
                      ...prev,
                      ibkr: { ...prev.ibkr, port: e.target.value }
                    }))}
                    placeholder="7497 for Paper, 7496 for Live"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ib-client">Client ID</Label>
                  <Input
                    id="ib-client"
                    value={brokerKeys.ibkr.clientId}
                    onChange={(e) => setBrokerKeys(prev => ({
                      ...prev,
                      ibkr: { ...prev.ibkr, clientId: e.target.value }
                    }))}
                    placeholder="Unique client ID (1-999)"
                  />
                </div>
              </div>
              <Button 
                onClick={saveBrokerCredentials}
                className="w-full"
                disabled={loading}
              >
                <Save className="w-4 h-4 mr-2" />
                Save Broker Settings
              </Button>
              
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Make sure TWS is running with API connections enabled before starting the Runner.
                  Port 7497 = Paper Trading, Port 7496 = Live Trading
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="runner" className="space-y-4">
          {/* Generate Runner Key */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                Runner Authentication Keys
              </CardTitle>
              <CardDescription>
                Generate API keys for your local Runner instances to connect to the cloud
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button 
                onClick={generateRunnerKey}
                disabled={generatingKey}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                {generatingKey ? 'Generating...' : 'Generate New Runner Key'}
              </Button>
            </CardContent>
          </Card>

          {/* Active Runner Keys */}
          {runnerKeys.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Active Runner Keys</CardTitle>
                <CardDescription>
                  Manage your active Runner authentication keys
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {runnerKeys.map((key) => (
                  <div key={key.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{key.name}</Badge>
                        {key.last_used_at && (
                          <span className="text-xs text-muted-foreground">
                            Last used: {new Date(key.last_used_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <div className="font-mono text-xs bg-muted p-2 rounded break-all">
                        {key.token.substring(0, 16)}...{key.token.substring(-8)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Created: {new Date(key.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(key.token)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => revokeRunnerKey(key.id)}
                      >
                        <Trash className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Copy your Runner key and paste it into your local Runner configuration. 
              Keep these keys secure - they provide access to your trading account.
            </AlertDescription>
          </Alert>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          {/* Alert Channels */}
          <Card>
            <CardHeader>
              <CardTitle>Notification Channels</CardTitle>
              <CardDescription>
                Configure where you receive trading alerts
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

              {/* Telegram Settings */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Send className="w-5 h-5" />
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
                
                {alertSettings.telegramEnabled && (
                  <div className="ml-8 grid grid-cols-1 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="telegram-token">Bot Token</Label>
                      <Input
                        id="telegram-token"
                        type="password"
                        value={alertSettings.telegram.botToken}
                        onChange={(e) => setAlertSettings(prev => ({
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
                        value={alertSettings.telegram.chatId}
                        onChange={(e) => setAlertSettings(prev => ({
                          ...prev,
                          telegram: { ...prev.telegram, chatId: e.target.value }
                        }))}
                        placeholder="-1001234567890"
                      />
                    </div>
                  </div>
                )}
              </div>

              <Separator />

              {/* Discord Settings */}
              <div className="space-y-3">
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
                
                {alertSettings.discordEnabled && (
                  <div className="ml-8">
                    <div className="space-y-2">
                      <Label htmlFor="discord-webhook">Webhook URL</Label>
                      <Input
                        id="discord-webhook"
                        type="password"
                        value={alertSettings.discord.webhookUrl}
                        onChange={(e) => setAlertSettings(prev => ({
                          ...prev,
                          discord: { ...prev.discord, webhookUrl: e.target.value }
                        }))}
                        placeholder="https://discord.com/api/webhooks/..."
                      />
                    </div>
                  </div>
                )}
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

          {/* Save Settings */}
          <div className="flex gap-3">
            <Button onClick={saveAlertSettings} disabled={loading} className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              {loading ? 'Saving...' : 'Save Alert Settings'}
            </Button>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Alerts will be sent to all enabled channels when bots encounter errors or 
              complete trades. Make sure you've configured your API keys first.
            </AlertDescription>
          </Alert>
        </TabsContent>
      </Tabs>
    </div>
  )
}