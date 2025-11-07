import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { KPICard } from "@/components/dashboard/KPICard";
import { StatusIndicator } from "@/components/dashboard/StatusIndicator";
import { DollarSign, Bot, TrendingUp, AlertTriangle, Activity, Zap, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { supabase } from "@/lib/supabase";
import { useAuthContext } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { PnLChart } from "@/components/charts/PnLChart";
import type { Database } from "@/lib/supabase";

type Bot = Database['public']['Tables']['bots']['Row'];
type Run = Database['public']['Tables']['runs']['Row'];

interface DashboardStats {
  todayPnL: number;
  activeBots: number;
  openPositions: number;
  totalRuns: number;
  winRate: number;
}

export default function Overview() {
  const { user } = useAuthContext();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    todayPnL: 0,
    activeBots: 0,
    openPositions: 0,
    totalRuns: 0,
    winRate: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentRuns, setRecentRuns] = useState<Run[]>([]);
  const [runnerConnected, setRunnerConnected] = useState(false);
  const [brokerConnected, setBrokerConnected] = useState(false);

  // Fetch dashboard data
  useEffect(() => {
    if (!user) return;

    const fetchDashboardData = async () => {
      try {
        // Check runner connection status first
        const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
        const { data: runnerStatus, error: runnerError } = await supabase
          .from('runner_status')
          .select('*')
          .eq('user_id', user.id)
          .gte('last_seen', fiveMinutesAgo)
          .order('last_seen', { ascending: false })
          .limit(1);

        if (runnerError) throw runnerError;
        
        const isRunnerConnected = runnerStatus && runnerStatus.length > 0;
        
        setRunnerConnected(isRunnerConnected);

        // Check broker credentials
        const { data: brokerCreds, error: credsError } = await supabase
          .from('external_api_keys')
          .select('*')
          .eq('user_id', user.id)
          .eq('provider', 'ibkr');

        if (credsError) throw credsError;
        setBrokerConnected(brokerCreds && brokerCreds.length > 0);

        // Fetch user's bots
        const { data: bots, error: botsError } = await supabase
          .from('bots')
          .select('*')
          .eq('user_id', user.id);

        if (botsError) throw botsError;

        // Fetch recent runs
        const { data: runs, error: runsError } = await supabase
          .from('runs')
          .select('*')
          .eq('user_id', user.id)
          .order('started_at', { ascending: false })
          .limit(10);

        if (runsError) throw runsError;

        // Calculate today's P/L
        const today = new Date().toDateString();
        const todayRuns = runs?.filter(run => 
          new Date(run.started_at).toDateString() === today
        ) || [];
        
        const todayPnL = todayRuns.reduce((sum, run) => 
          sum + (run.pnl ? parseFloat(run.pnl.toString()) : 0), 0
        );

        // Calculate statistics
        const activeBots = bots?.filter(bot => bot.is_enabled).length || 0;
        const totalRuns = runs?.length || 0;
        const winningRuns = runs?.filter(run => 
          run.pnl && parseFloat(run.pnl.toString()) > 0
        ).length || 0;
        const winRate = totalRuns > 0 ? (winningRuns / totalRuns) * 100 : 0;

        setStats({
          todayPnL,
          activeBots,
          openPositions: 0,
          totalRuns,
          winRate,
        });

        setRecentRuns(runs || []);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        toast({
          title: "Error",
          description: "Failed to load dashboard data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();

    // Set up real-time subscription for runs
    const runsSubscription = supabase
      .channel('runs-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'runs',
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          // Refetch data when runs change
          fetchDashboardData();
        }
      )
      .subscribe();

    // Set up real-time subscription for bots
    const botsSubscription = supabase
      .channel('bots-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'bots',
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          // Refetch data when bots change
          fetchDashboardData();
        }
      )
      .subscribe();

    // Set up real-time subscription for runner status
    const runnerSubscription = supabase
      .channel('runner-status-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'runner_status',
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          // Refetch data when runner status changes
          fetchDashboardData();
        }
      )
      .subscribe();

    return () => {
      runsSubscription.unsubscribe();
      botsSubscription.unsubscribe();
      runnerSubscription.unsubscribe();
    };
  }, [user]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 pb-16">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 pb-16">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-mono font-semibold tracking-tight">Overview</h1>
        <div className="flex items-center gap-3">
          <StatusIndicator 
            label="Database" 
            status="connected" 
            tooltip="Supabase connection active" 
          />
          <StatusIndicator 
            label="Runner" 
            status={runnerConnected ? "connected" : "disconnected"} 
            tooltip={runnerConnected ? "Desktop Runner connected and active" : "Desktop Runner not connected"}
          />
          <StatusIndicator 
            label="Broker" 
            status={brokerConnected && runnerConnected ? "ok" : "disconnected"} 
            tooltip={brokerConnected ? 
              (runnerConnected ? "IBKR credentials configured and Runner active" : "IBKR credentials configured, start Runner") :
              "Configure IBKR credentials in Settings"
            }
          />
          <StatusIndicator 
            label="Realtime" 
            status="connected" 
            tooltip="Real-time data streaming active"
          />
          <Badge variant="secondary" className="font-mono text-xs">
            {stats.activeBots > 0 ? `${stats.activeBots} Active` : 'No Active Bots'}
          </Badge>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <KPICard
          title="Today's P/L"
          value={`${stats.todayPnL >= 0 ? '+' : ''}$${stats.todayPnL.toFixed(2)}`}
          icon={DollarSign}
          trend={stats.todayPnL !== 0 ? {
            value: `${stats.todayPnL >= 0 ? '+' : ''}${stats.todayPnL.toFixed(2)}`,
            positive: stats.todayPnL >= 0
          } : undefined}
        />
        <KPICard
          title="Active Bots"
          value={stats.activeBots}
          icon={Bot}
        />
        <KPICard
          title="Total Runs"
          value={stats.totalRuns}
          icon={TrendingUp}
        />
        <KPICard
          title="Win Rate"
          value={`${stats.winRate.toFixed(1)}%`}
          icon={Activity}
          trend={stats.totalRuns > 0 ? {
            value: `${stats.totalRuns} trades`,
            positive: stats.winRate >= 50
          } : undefined}
        />
        <KPICard
          title="Open Positions"
          value={stats.openPositions}
          icon={AlertTriangle}
        />
        <KPICard
          title="Uptime"
          value="100%"
          icon={Zap}
        />
      </div>

      {/* Connection Status Alert */}
      {(!runnerConnected || !brokerConnected) && (
        <div className="mb-6">
          <Card className="border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30">
            <div className="p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-medium text-amber-800 dark:text-amber-200 mb-1">
                    Connection Required for Trading
                  </h3>
                  <div className="text-sm text-amber-700 dark:text-amber-300 space-y-1">
                    {!runnerConnected && (
                      <p>• Download and start the <span className="font-medium">Oriphim Runner</span> desktop app to enable trading</p>
                    )}
                    {!brokerConnected && (
                      <p>• Configure your <span className="font-medium">IBKR credentials</span> in Settings to connect your broker</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* P/L Chart */}
        <div className="border border-border p-4 h-[360px] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-mono font-semibold">P/L Performance</h2>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" className="h-7 text-xs font-mono">
                Intraday
              </Button>
              <Button variant="ghost" size="sm" className="h-7 text-xs font-mono">
                Daily
              </Button>
            </div>
          </div>
          {runnerConnected && brokerConnected ? (
            <PnLChart className="flex-1" timeframe="daily" />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-3">
                <Bot className="h-12 w-12 text-muted-foreground mx-auto" />
                <div>
                  <p className="text-sm font-mono font-semibold text-muted-foreground">Connect Runner First</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {!brokerConnected ? "Configure broker credentials in Settings" : 
                     !runnerConnected ? "Start your Runner app to see live P/L data" :
                     "Waiting for connection..."}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Market Data Chart */}
        <div className="border border-border p-4 h-[360px] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-mono font-semibold">SPY Market Data</h2>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" className="h-7 text-xs font-mono">
                15m
              </Button>
              <Button variant="ghost" size="sm" className="h-7 text-xs font-mono">
                1h
              </Button>
            </div>
          </div>
          {runnerConnected && brokerConnected ? (
            <CandlestickChart symbol="SPY" className="flex-1" />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-3">
                <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto" />
                <div>
                  <p className="text-sm font-mono font-semibold text-muted-foreground">Broker Connection Required</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {!brokerConnected ? "Add IBKR credentials in Settings, then start Runner" : 
                     !runnerConnected ? "Start your Runner app to stream live market data" :
                     "Establishing connection..."}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Recent Runs */}
        <div className="border border-border p-4 h-[360px] flex flex-col">
          <h2 className="text-sm font-mono font-semibold mb-4">Recent Runs</h2>
          <div className="flex-1 overflow-auto">
            {recentRuns.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <span className="text-sm text-muted-foreground font-body">No runs yet</span>
              </div>
            ) : (
              <div className="space-y-2">
                {recentRuns.slice(0, 8).map((run) => (
                  <div key={run.id} className="flex items-center justify-between py-2 px-3 border border-border rounded">
                    <div className="flex items-center gap-3">
                      <Badge 
                        variant={run.status === 'completed' ? 'default' : run.status === 'running' ? 'secondary' : 'destructive'}
                        className="text-xs"
                      >
                        {run.status}
                      </Badge>
                      <span className="text-xs font-mono">{run.mode}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-mono ${
                        run.pnl ? (parseFloat(run.pnl.toString()) >= 0 ? 'text-green-500' : 'text-red-500') : 'text-muted-foreground'
                      }`}>
                        {run.pnl ? `${parseFloat(run.pnl.toString()) >= 0 ? '+' : ''}$${parseFloat(run.pnl.toString()).toFixed(2)}` : '$0.00'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(run.started_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="border border-border p-4">
          <h2 className="text-sm font-mono font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Button 
              variant="outline" 
              className="w-full justify-start font-body text-sm h-9"
              onClick={() => navigate('/dashboard/trading')}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              View Trading Charts
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start font-body text-sm h-9"
              onClick={() => navigate('/dashboard/bots')}
            >
              <Bot className="w-4 h-4 mr-2" />
              Manage Bots
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start font-body text-sm h-9"
              onClick={() => navigate('/dashboard/runs')}
            >
              <Activity className="w-4 h-4 mr-2" />
              View All Runs
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
