import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Play, Square, MoreVertical, Copy, Edit, Trash2, ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { supabase } from "@/lib/supabase";
import { useAuthContext } from "@/contexts/AuthContext";
import type { Database } from "@/lib/supabase";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type Bot = Database['public']['Tables']['bots']['Row'];
type Run = Database['public']['Tables']['runs']['Row'];

interface BotWithRun extends Bot {
  activeRun?: Run | null;
}

const getBotKindDisplay = (kind: Bot['kind']) => {
  const kindMap = {
    putlite: 'PUT-Lite',
    buywrite: 'Buy-Write', 
    condor: 'Iron Condor',
    gammaburst: 'Gamma Burst'
  };
  return kindMap[kind] || kind;
};

export default function Bots() {
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const [bots, setBots] = useState<BotWithRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [runnerConnected, setRunnerConnected] = useState(false);
  const [brokerConnected, setBrokerConnected] = useState(false);

  // Fetch user's bots with their active runs
  useEffect(() => {
    if (!user) return;
    
    const fetchBots = async () => {
      try {
        // Check runner connection status
        const { data: runnerStatus, error: runnerError } = await supabase
          .from('runner_status')
          .select('*')
          .eq('user_id', user.id)
          .order('last_heartbeat', { ascending: false })
          .limit(1);

        if (runnerError) throw runnerError;
        
        const isRunnerConnected = runnerStatus && runnerStatus.length > 0 && 
          new Date(runnerStatus[0].last_heartbeat) > new Date(Date.now() - 5 * 60 * 1000);
        
        setRunnerConnected(isRunnerConnected);

        // Check broker credentials
        const { data: brokerCreds, error: credsError } = await supabase
          .from('external_api_keys')
          .select('*')
          .eq('user_id', user.id)
          .eq('provider', 'ibkr');

        if (credsError) throw credsError;
        setBrokerConnected(brokerCreds && brokerCreds.length > 0);

        // Get bots with their active runs
        const { data: botsData, error: botsError } = await supabase
          .from('bots')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });

        if (botsError) throw botsError;

        // Get active runs for these bots
        const { data: runsData, error: runsError } = await supabase
          .from('runs')
          .select('*')
          .eq('user_id', user.id)
          .in('status', ['pending', 'running'])
          .order('created_at', { ascending: false });

        if (runsError) throw runsError;

        // Combine bots with their active runs
        const botsWithRuns: BotWithRun[] = (botsData || []).map(bot => {
          const activeRun = runsData?.find(run => run.bot_id === bot.id) || null;
          return { ...bot, activeRun };
        });

        setBots(botsWithRuns);
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to load bots",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchBots();

    // Set up real-time subscriptions for live updates
    const botsSubscription = supabase
      .channel('bots-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'bots',
          filter: `user_id=eq.${user.id}`,
        },
        () => fetchBots()
      )
      .subscribe();

    const runsSubscription = supabase
      .channel('runs-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'runs',
          filter: `user_id=eq.${user.id}`,
        },
        () => fetchBots()
      )
      .subscribe();

    return () => {
      botsSubscription.unsubscribe();
      runsSubscription.unsubscribe();
    };
  }, [user]);

  // Handle bot start/stop actions
  const handleBotStart = async (botId: string, mode: 'paper' | 'live' = 'paper') => {
    // Check runner and broker connection before starting
    if (!brokerConnected) {
      toast({
        title: "Broker Not Connected",
        description: "Please configure IBKR credentials in Settings first",
        variant: "destructive"
      });
      return;
    }

    if (!runnerConnected) {
      toast({
        title: "Runner Not Connected",
        description: "Please start your Oriphim Runner desktop app first",
        variant: "destructive"
      });
      return;
    }

    setActionLoading(botId);
    
    try {
      const { data, error } = await supabase.functions.invoke('start-run', {
        body: { 
          bot_id: botId,
          mode: mode
        }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: `Bot started in ${mode} mode successfully`,
      });
      
      // Refresh bots to get updated state
      window.location.reload(); // Simple refresh for now

    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to start bot: ${error.message || 'Unknown error'}`,
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleBotStop = async (bot: BotWithRun) => {
    if (!bot.activeRun) {
      toast({
        title: "Error",
        description: "No active run to stop",
        variant: "destructive",
      });
      return;
    }

    setActionLoading(bot.id);
    
    try {
      const { data, error } = await supabase.functions.invoke('stop-run', {
        body: { run_id: bot.activeRun.id }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Bot stopped successfully",
      });
      
      // Refresh bots to get updated state
      window.location.reload(); // Simple refresh for now

    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to stop bot: ${error.message || 'Unknown error'}`,
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 pb-16">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/dashboard")}
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-smooth"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Dashboard
          </button>
          <h1 className="text-lg font-mono font-semibold tracking-tight">Bots</h1>
        </div>
        <Button className="font-body h-9 text-sm">Create Bot</Button>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="enabled">Enabled</TabsTrigger>
          <TabsTrigger value="disabled">Disabled</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : bots.length === 0 ? (
            <div className="text-center py-12 border border-border rounded-lg">
              <p className="text-muted-foreground mb-4">No bots created yet</p>
              <Button className="font-body">Create Your First Bot</Button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {bots.map((bot) => (
                <Card key={bot.id} className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-mono font-semibold text-lg">{bot.name}</h3>
                          <Badge variant="outline" className="font-body text-xs">
                            {getBotKindDisplay(bot.kind)}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`h-2 w-2 rounded-full ${
                            bot.activeRun ? 'bg-blue-500' : 
                            bot.is_enabled ? 'bg-green-500' : 'bg-gray-400'
                          }`} />
                          <span className="text-xs font-body">
                            {bot.activeRun ? `Running (${bot.activeRun.mode})` : 
                             bot.is_enabled ? 'Ready' : 'Disabled'}
                          </span>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Copy className="h-4 w-4 mr-2" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive">
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <div className="text-sm font-body">
                      <span className="text-muted-foreground">Created:</span>
                      <p className="mt-1">{new Date(bot.created_at).toLocaleDateString()}</p>
                    </div>

                    <div className="border-t pt-3 flex items-center justify-between">
                      <div className="text-sm font-body">
                        <span className="text-muted-foreground">Status: </span>
                        <span className={
                          bot.activeRun ? "text-blue-500" : 
                          bot.is_enabled ? "text-green-500" : "text-gray-500"
                        }>
                          {bot.activeRun ? `Running (${bot.activeRun.mode})` : 
                           bot.is_enabled ? 'Ready' : 'Disabled'}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        {bot.activeRun ? (
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleBotStop(bot)}
                            disabled={actionLoading === bot.id}
                            className="font-body h-7"
                          >
                            {actionLoading === bot.id ? (
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Square className="h-3 w-3 mr-1" />
                            )}
                            Stop
                          </Button>
                        ) : bot.is_enabled ? (
                          <div className="flex gap-1">
                            <Button 
                              size="sm" 
                              onClick={() => handleBotStart(bot.id, 'paper')}
                              disabled={actionLoading === bot.id || !runnerConnected || !brokerConnected}
                              className={`font-body ${(!runnerConnected || !brokerConnected) ? 'opacity-50 cursor-not-allowed' : ''}`}
                              title={!runnerConnected ? 'Runner not connected' : !brokerConnected ? 'Broker not connected' : ''}
                            >
                              {actionLoading === bot.id ? (
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              ) : !runnerConnected || !brokerConnected ? (
                                <AlertCircle className="h-3 w-3 mr-1" />
                              ) : (
                                <Play className="h-3 w-3 mr-1" />
                              )}
                              Start Paper
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleBotStart(bot.id, 'live')}
                              disabled={actionLoading === bot.id || !runnerConnected || !brokerConnected}
                              className={`font-body text-xs px-2 ${(!runnerConnected || !brokerConnected) ? 'opacity-50 cursor-not-allowed' : ''}`}
                              title={!runnerConnected ? 'Runner not connected' : !brokerConnected ? 'Broker not connected' : ''}
                            >
                              Live
                            </Button>
                          </div>
                        ) : (
                          <div className="text-xs text-muted-foreground">
                            Bot is disabled
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="enabled" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {bots
              .filter((bot) => bot.is_enabled)
              .map((bot) => (
                <Card key={bot.id} className="p-6">
                  <p className="text-sm">
                    <strong>{bot.name}</strong> - {getBotKindDisplay(bot.kind)}
                  </p>
                </Card>
              ))}
          </div>
        </TabsContent>

        <TabsContent value="disabled" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {bots
              .filter((bot) => !bot.is_enabled)
              .map((bot) => (
                <Card key={bot.id} className="p-6">
                  <p className="text-sm">
                    <strong>{bot.name}</strong> - {getBotKindDisplay(bot.kind)}
                  </p>
                </Card>
              ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}