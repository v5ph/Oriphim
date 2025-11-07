import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, Play, Square } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { useAuthContext } from "@/contexts/AuthContext";
import type { Database } from "@/lib/supabase";

type Run = Database['public']['Tables']['runs']['Row'] & {
  bots?: Database['public']['Tables']['bots']['Row']
};

type RunLog = Database['public']['Tables']['run_logs']['Row'];
type RunnerStatus = Database['public']['Tables']['runner_status']['Row'];

export default function Runs() {
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const [runs, setRuns] = useState<Run[]>([]);
  const [logs, setLogs] = useState<RunLog[]>([]);
  const [runnerStatus, setRunnerStatus] = useState<RunnerStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const fetchData = async () => {
      try {
        // Fetch runs with bot information
        const { data: runsData, error: runsError } = await supabase
          .from('runs')
          .select(`
            *,
            bots (
              id,
              name,
              kind
            )
          `)
          .eq('user_id', user.id)
          .order('started_at', { ascending: false })
          .limit(50);

        if (runsError) throw runsError;
        setRuns(runsData || []);

        // Fetch recent logs for active runs
        const activeRuns = runsData?.filter(run => 
          run.status === 'running' || run.status === 'pending'
        ) || [];

        if (activeRuns.length > 0) {
          const { data: logsData, error: logsError } = await supabase
            .from('run_logs')
            .select('*')
            .in('run_id', activeRuns.map(run => run.id))
            .order('ts', { ascending: false })
            .limit(100);

          if (logsError) throw logsError;
          setLogs(logsData || []);
        }

        // Fetch runner status
        const { data: statusData, error: statusError } = await supabase
          .from('runner_status')
          .select('*')
          .eq('user_id', user.id);

        if (statusError) throw statusError;
        setRunnerStatus(statusData || []);

      } catch (error) {
        console.error('Error fetching runs data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Set up real-time subscriptions
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
        () => fetchData()
      )
      .subscribe();

    const logsSubscription = supabase
      .channel('logs-realtime')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'run_logs',
        },
        (payload) => {
          const newLog = payload.new as RunLog;
          // Only add logs for runs we're tracking
          const relevantRun = runs.find(run => run.id === newLog.run_id);
          if (relevantRun) {
            setLogs(prev => [newLog, ...prev.slice(0, 99)]);
          }
        }
      )
      .subscribe();

    const statusSubscription = supabase
      .channel('runner-status-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'runner_status',
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          // Refetch runner status
          supabase
            .from('runner_status')
            .select('*')
            .eq('user_id', user.id)
            .then(({ data }) => setRunnerStatus(data || []));
        }
      )
      .subscribe();

    return () => {
      runsSubscription.unsubscribe();
      logsSubscription.unsubscribe();
      statusSubscription.unsubscribe();
    };
  }, [user]);

  const activeRuns = runs.filter(run => 
    run.status === 'running' || run.status === 'pending'
  );

  const getStatusBadge = (status: string) => {
    const statusMap = {
      pending: { variant: 'outline' as const, label: 'Pending' },
      running: { variant: 'default' as const, label: 'Running' },
      completed: { variant: 'secondary' as const, label: 'Completed' },
      failed: { variant: 'destructive' as const, label: 'Failed' },
      stopped: { variant: 'outline' as const, label: 'Stopped' },
    };
    return statusMap[status as keyof typeof statusMap] || { variant: 'outline' as const, label: status };
  };

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
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate("/dashboard")}
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-smooth"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </button>
        <h1 className="text-lg font-mono font-semibold tracking-tight">Runs</h1>
        <Badge variant="outline">{runs.length} total</Badge>
        {activeRuns.length > 0 && (
          <Badge variant="default">{activeRuns.length} active</Badge>
        )}
      </div>

      <Tabs defaultValue="live" className="w-full">
        <TabsList>
          <TabsTrigger value="live" className="font-mono">Live Monitor</TabsTrigger>
          <TabsTrigger value="history" className="font-mono">History</TabsTrigger>
        </TabsList>

        <TabsContent value="live" className="mt-6">
          <div className="grid lg:grid-cols-3 gap-4">
            {/* Log Stream */}
            <div className="lg:col-span-2 border border-border p-4 h-[360px] flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-mono font-semibold">Log Stream</h2>
                <div className="flex gap-2">
                  {runnerStatus.map((status) => (
                    <div key={status.id} className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        status.is_connected ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <span className="text-xs font-mono">
                        {status.machine_name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex-1 border border-border overflow-y-auto p-2 space-y-1 font-mono text-xs">
                {logs.length > 0 ? (
                  logs.map((log) => (
                    <div key={log.id} className="flex gap-2">
                      <span className="text-muted-foreground shrink-0">
                        {new Date(log.ts).toLocaleTimeString()}
                      </span>
                      <Badge 
                        variant={
                          log.level === 'error' ? 'destructive' :
                          log.level === 'warning' ? 'outline' : 'secondary'
                        }
                        className="text-xs shrink-0"
                      >
                        {log.level}
                      </Badge>
                      <span className="truncate">{log.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <span className="text-sm text-muted-foreground font-body">
                      {activeRuns.length > 0 ? 'Waiting for logs...' : 'No active runs'}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Active Runs & Runner Status */}
            <div className="space-y-4">
              <div className="border border-border p-4">
                <h2 className="text-sm font-mono font-semibold mb-4">Active Runs</h2>
                <div className="h-40 border border-border overflow-y-auto p-2 space-y-2">
                  {activeRuns.length > 0 ? (
                    activeRuns.map((run) => (
                      <div key={run.id} className="p-2 border rounded-sm space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs">
                            {run.bots?.name || 'Unknown Bot'}
                          </span>
                          <Badge {...getStatusBadge(run.status)} />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          P/L: ${run.pnl?.toFixed(2) || '0.00'}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Started: {new Date(run.started_at).toLocaleTimeString()}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <span className="text-sm text-muted-foreground font-body">No active runs</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="border border-border p-4">
                <h2 className="text-sm font-mono font-semibold mb-4">Runner Status</h2>
                <div className="space-y-3 text-sm font-mono">
                  {runnerStatus.length > 0 ? (
                    runnerStatus.map((status) => (
                      <div key={status.id} className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Connection</span>
                          <Badge variant={status.is_connected ? 'default' : 'destructive'}>
                            {status.is_connected ? 'Connected' : 'Disconnected'}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Last Heartbeat</span>
                          <span className="text-xs">
                            {new Date(status.last_heartbeat).toLocaleTimeString()}
                          </span>
                        </div>
                        {status.broker_connected && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Broker</span>
                            <Badge variant="default">{status.broker_name}</Badge>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-muted-foreground">
                      No runners connected
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <div className="space-y-4">
            {runs.length > 0 ? (
              <div className="grid gap-4">
                {runs.map((run) => (
                  <div key={run.id} className="border border-border p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <h3 className="font-mono font-semibold">
                          {run.bots?.name || 'Unknown Bot'}
                        </h3>
                        <Badge {...getStatusBadge(run.status)} />
                        <Badge variant="outline">{run.mode}</Badge>
                      </div>
                      <div className="text-sm font-mono">
                        P/L: ${run.pnl?.toFixed(2) || '0.00'}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-muted-foreground">
                      <div>
                        <span className="block text-xs">Started</span>
                        <span className="font-mono">
                          {new Date(run.started_at).toLocaleString()}
                        </span>
                      </div>
                      
                      {run.ended_at && (
                        <div>
                          <span className="block text-xs">Ended</span>
                          <span className="font-mono">
                            {new Date(run.ended_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                      
                      <div>
                        <span className="block text-xs">Trades</span>
                        <span className="font-mono">{run.trades_count || 0}</span>
                      </div>
                      
                      <div>
                        <span className="block text-xs">Win Rate</span>
                        <span className="font-mono">{run.win_rate?.toFixed(1) || '0.0'}%</span>
                      </div>
                    </div>

                    {run.error_message && (
                      <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        {run.error_message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="border border-border p-12 flex flex-col items-center justify-center text-center">
                <h3 className="text-lg font-mono font-semibold mb-2">No run history</h3>
                <p className="text-sm text-muted-foreground font-body">
                  Past runs will appear here once you start some bots
                </p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
