import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { supabase } from '@/lib/supabase';
import { useAuthContext } from '@/contexts/AuthContext';

interface PnLDataPoint {
  timestamp: string;
  cumulativePnL: number;
  dailyPnL: number;
}

interface PnLChartProps {
  className?: string;
  timeframe?: 'intraday' | 'daily' | 'weekly';
}

export function PnLChart({ className, timeframe = 'intraday' }: PnLChartProps) {
  const { user } = useAuthContext();
  const [data, setData] = useState<PnLDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;

    const fetchPnLData = async () => {
      try {
        // Get runs from the last 7 days
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

        const { data: runs, error } = await supabase
          .from('runs')
          .select('*')
          .eq('user_id', user.id)
          .gte('started_at', sevenDaysAgo.toISOString())
          .order('started_at', { ascending: true });

        if (error) throw error;

        // RUNNER-FIRST MODEL: Process sparse P/L snapshots from runs
        // Runner sends only 5-10 snapshots per run, not tick-by-tick data
        const pnlData: PnLDataPoint[] = [];
        let cumulativePnL = 0;

        if (timeframe === 'intraday') {
          // Use pnl_snapshots for intraday granular view
          runs?.forEach(run => {
            if (run.metadata && (run.metadata as any).pnl_snapshots) {
              const snapshots = (run.metadata as any).pnl_snapshots as Array<{ts: string, pnl: number}>;
              snapshots.forEach(snapshot => {
                pnlData.push({
                  timestamp: snapshot.ts,
                  cumulativePnL: cumulativePnL + snapshot.pnl,
                  dailyPnL: snapshot.pnl
                });
              });
            } else if (run.pnl) {
              // Fallback to run start/end if no snapshots
              const runDate = new Date(run.started_at);
              pnlData.push({
                timestamp: runDate.toLocaleTimeString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                }),
                cumulativePnL: cumulativePnL + parseFloat(run.pnl.toString()),
                dailyPnL: parseFloat(run.pnl.toString())
              });
            }
            if (run.pnl) cumulativePnL += parseFloat(run.pnl.toString());
          });
        } else {
          // Group runs by day for daily/weekly timeframes
          const groupedRuns = new Map<string, { pnl: number, count: number }>();

          runs?.forEach(run => {
            if (!run.pnl) return;
            
            const runDate = new Date(run.started_at);
            const key = runDate.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric' 
            });

            const existing = groupedRuns.get(key) || { pnl: 0, count: 0 };
            existing.pnl += parseFloat(run.pnl.toString());
            existing.count += 1;
            groupedRuns.set(key, existing);
          });

          // Convert to chart data
          groupedRuns.forEach((value, key) => {
            cumulativePnL += value.pnl;
            pnlData.push({
              timestamp: key,
              cumulativePnL: Number(cumulativePnL.toFixed(2)),
              dailyPnL: Number(value.pnl.toFixed(2))
            });
          });
        }

        // If no data, create a flat line at zero
        if (pnlData.length === 0) {
          const now = new Date();
          for (let i = 6; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            pnlData.push({
              timestamp: date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
              }),
              cumulativePnL: 0,
              dailyPnL: 0
            });
          }
        }

        setData(pnlData);
      } catch (error) {
        console.error('Error fetching P/L data:', error);
        // Fallback to zero data
        setData([
          { timestamp: 'Mon', cumulativePnL: 0, dailyPnL: 0 },
          { timestamp: 'Tue', cumulativePnL: 0, dailyPnL: 0 },
          { timestamp: 'Wed', cumulativePnL: 0, dailyPnL: 0 },
          { timestamp: 'Thu', cumulativePnL: 0, dailyPnL: 0 },
          { timestamp: 'Fri', cumulativePnL: 0, dailyPnL: 0 },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchPnLData();

    // Set up real-time subscription for new runs
    const subscription = supabase
      .channel('pnl-updates')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'runs',
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          fetchPnLData(); // Refetch when new runs are added
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [user, timeframe]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const cumPnL = payload.find((p: any) => p.dataKey === 'cumulativePnL')?.value || 0;
      const dailyPnL = payload.find((p: any) => p.dataKey === 'dailyPnL')?.value || 0;
      
      return (
        <div className="bg-background border border-border p-3 rounded shadow-lg">
          <p className="font-mono text-sm font-semibold">{label}</p>
          <p className="text-sm">
            <span className="text-muted-foreground">Daily P/L:</span>{' '}
            <span className={dailyPnL >= 0 ? 'text-green-500' : 'text-red-500'}>
              ${dailyPnL >= 0 ? '+' : ''}${dailyPnL}
            </span>
          </p>
          <p className="text-sm">
            <span className="text-muted-foreground">Cumulative:</span>{' '}
            <span className={cumPnL >= 0 ? 'text-green-500' : 'text-red-500'}>
              ${cumPnL >= 0 ? '+' : ''}${cumPnL}
            </span>
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-[300px] ${className}`}>
        <div className="text-sm text-muted-foreground">Loading P/L data...</div>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis 
            dataKey="timestamp" 
            stroke="#9ca3af"
            fontSize={12}
            tick={{ fill: '#9ca3af' }}
          />
          <YAxis 
            stroke="#9ca3af"
            fontSize={12}
            tick={{ fill: '#9ca3af' }}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Zero line reference */}
          <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
          
          {/* Cumulative P/L line */}
          <Line
            type="monotone"
            dataKey="cumulativePnL"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 0, r: 4 }}
            activeDot={{ r: 6, fill: '#3b82f6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}