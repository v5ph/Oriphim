import { useEffect, useState } from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { supabase } from '@/lib/supabase';

interface MarketDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface CandlestickChartProps {
  symbol: string;
  className?: string;
}

// Custom Candlestick Bar Component
const CandlestickBar = (props: any) => {
  const { payload, x, y, width, height } = props;
  if (!payload) return null;

  const { open, close, high, low } = payload;
  const isGreen = close > open;
  const color = isGreen ? '#22c55e' : '#ef4444';
  const bodyHeight = Math.abs(close - open) * height / (payload.high - payload.low);
  const bodyY = y + (high - Math.max(open, close)) * height / (payload.high - payload.low);
  
  return (
    <g>
      {/* Wick (high-low line) */}
      <line
        x1={x + width / 2}
        y1={y}
        x2={x + width / 2}
        y2={y + height}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body (open-close rectangle) */}
      <rect
        x={x + width * 0.2}
        y={bodyY}
        width={width * 0.6}
        height={bodyHeight}
        fill={isGreen ? color : 'transparent'}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

export function CandlestickChart({ symbol, className }: CandlestickChartProps) {
  const [data, setData] = useState<MarketDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // RUNNER-FIRST MODEL: Simulated market data for dashboard visualization
    // Real market data flows: Broker → Runner (local) → Trading Events → Cloud
    // This chart shows simulated bars. Real data stays on Runner to avoid feed costs.
    const generateSampleData = () => {
      const now = new Date();
      const sampleData: MarketDataPoint[] = [];
      let basePrice = 450; // Starting price for SPY
      
      for (let i = 29; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 15 * 60 * 1000); // 15-minute bars
        
        // Generate realistic OHLC data
        const open = basePrice + (Math.random() - 0.5) * 2;
        const volatility = Math.random() * 1.5 + 0.5;
        const high = open + Math.random() * volatility;
        const low = open - Math.random() * volatility;
        const close = low + Math.random() * (high - low);
        const volume = Math.floor(Math.random() * 1000000 + 500000);
        
        sampleData.push({
          timestamp: timestamp.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          open: Number(open.toFixed(2)),
          high: Number(high.toFixed(2)),
          low: Number(low.toFixed(2)),
          close: Number(close.toFixed(2)),
          volume
        });
        
        basePrice = close;
      }
      
      return sampleData;
    };

    // Simulate data loading
    setTimeout(() => {
      setData(generateSampleData());
      setLoading(false);
    }, 1000);

    // RUNNER-FIRST: Market data stays local to Runner to avoid data feed costs
    // Dashboard subscribes to trading EVENTS, not raw market ticks:
    // const subscription = supabase
    //   .channel('runner-events')
    //   .on('postgres_changes', { event: '*', schema: 'public', table: 'runs' }, handleTradingEvent)
    //   .subscribe();

  }, [symbol]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border border-border p-3 rounded shadow-lg">
          <p className="font-mono text-sm font-semibold">{`Time: ${label}`}</p>
          <p className="text-sm"><span className="text-muted-foreground">Open:</span> ${data.open}</p>
          <p className="text-sm"><span className="text-muted-foreground">High:</span> ${data.high}</p>
          <p className="text-sm"><span className="text-muted-foreground">Low:</span> ${data.low}</p>
          <p className="text-sm"><span className="text-muted-foreground">Close:</span> ${data.close}</p>
          <p className="text-sm"><span className="text-muted-foreground">Volume:</span> {data.volume.toLocaleString()}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-[300px] ${className}`}>
        <div className="text-sm text-muted-foreground">Loading chart data...</div>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis 
            dataKey="timestamp" 
            stroke="#9ca3af"
            fontSize={12}
            tick={{ fill: '#9ca3af' }}
          />
          <YAxis 
            yAxisId="price"
            domain={['dataMin - 0.5', 'dataMax + 0.5']}
            stroke="#9ca3af"
            fontSize={12}
            tick={{ fill: '#9ca3af' }}
            orientation="left"
          />
          <YAxis 
            yAxisId="volume"
            domain={[0, 'dataMax']}
            stroke="#6b7280"
            fontSize={10}
            tick={{ fill: '#6b7280' }}
            orientation="right"
            opacity={0.6}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Volume bars at bottom */}
          <Bar 
            dataKey="volume" 
            fill="#6b7280" 
            opacity={0.3}
            yAxisId="volume"
          />
          
          {/* Custom candlesticks */}
          <Bar 
            dataKey="high" 
            shape={CandlestickBar}
            yAxisId="price"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}