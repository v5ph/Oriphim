import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { ArrowLeft, TrendingUp, BarChart3 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { PnLChart } from "@/components/charts/PnLChart";

export default function Trading() {
  const navigate = useNavigate();
  const [selectedSymbol, setSelectedSymbol] = useState("SPY");
  const [timeframe, setTimeframe] = useState("15m");

  const symbols = ["SPY", "QQQ", "IWM", "SPX", "TSLA", "AAPL", "NVDA"];
  const timeframes = ["5m", "15m", "1h", "4h", "1d"];

  return (
    <div className="max-w-7xl mx-auto px-4 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/dashboard")}
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-smooth"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Dashboard
          </button>
          <h1 className="text-lg font-mono font-semibold tracking-tight">Trading Charts</h1>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="font-mono text-xs">
            Real-time Data
          </Badge>
        </div>
      </div>

      {/* Symbol Selector */}
      <div className="flex items-center gap-4 mb-6 overflow-x-auto">
        <span className="text-sm font-mono text-muted-foreground whitespace-nowrap">Symbols:</span>
        <div className="flex gap-2">
          {symbols.map((symbol) => (
            <Button
              key={symbol}
              variant={selectedSymbol === symbol ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedSymbol(symbol)}
              className="font-mono text-xs"
            >
              {symbol}
            </Button>
          ))}
        </div>
      </div>

      {/* Timeframe Selector */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm font-mono text-muted-foreground">Timeframe:</span>
        <div className="flex gap-2">
          {timeframes.map((tf) => (
            <Button
              key={tf}
              variant={timeframe === tf ? "default" : "outline"}
              size="sm"
              onClick={() => setTimeframe(tf)}
              className="font-mono text-xs"
            >
              {tf}
            </Button>
          ))}
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6">
        {/* Main Candlestick Chart */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-mono font-semibold">
              {selectedSymbol} - {timeframe} Candlestick Chart
            </h2>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Live Market Data</span>
            </div>
          </div>
          <CandlestickChart symbol={selectedSymbol} className="h-[400px]" />
        </Card>

        {/* Charts Row */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* P/L Performance */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-mono font-semibold">P/L Performance</h2>
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
            </div>
            <Tabs defaultValue="daily" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="intraday" className="text-xs">Intraday</TabsTrigger>
                <TabsTrigger value="daily" className="text-xs">Daily</TabsTrigger>
                <TabsTrigger value="weekly" className="text-xs">Weekly</TabsTrigger>
              </TabsList>
              <TabsContent value="intraday" className="mt-4">
                <PnLChart timeframe="intraday" className="h-[300px]" />
              </TabsContent>
              <TabsContent value="daily" className="mt-4">
                <PnLChart timeframe="daily" className="h-[300px]" />
              </TabsContent>
              <TabsContent value="weekly" className="mt-4">
                <PnLChart timeframe="weekly" className="h-[300px]" />
              </TabsContent>
            </Tabs>
          </Card>

          {/* Options Flow (Placeholder for now) */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-mono font-semibold">Options Flow</h2>
              <div className="flex gap-2">
                <Badge variant="outline" className="text-xs">Calls</Badge>
                <Badge variant="outline" className="text-xs">Puts</Badge>
              </div>
            </div>
            <div className="h-[300px] flex items-center justify-center border border-border rounded">
              <div className="text-center">
                <BarChart3 className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Options flow visualization</p>
                <p className="text-xs text-muted-foreground mt-1">Coming soon...</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Additional Charts Row */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Volume Analysis */}
          <Card className="p-6">
            <h3 className="text-sm font-mono font-semibold mb-4">Volume Analysis</h3>
            <div className="h-[200px] flex items-center justify-center border border-border rounded">
              <div className="text-center">
                <BarChart3 className="w-6 h-6 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Volume trends</p>
              </div>
            </div>
          </Card>

          {/* IV Rank */}
          <Card className="p-6">
            <h3 className="text-sm font-mono font-semibold mb-4">IV Rank</h3>
            <div className="h-[200px] flex items-center justify-center border border-border rounded">
              <div className="text-center">
                <TrendingUp className="w-6 h-6 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Implied volatility</p>
              </div>
            </div>
          </Card>

          {/* Greeks */}
          <Card className="p-6">
            <h3 className="text-sm font-mono font-semibold mb-4">Portfolio Greeks</h3>
            <div className="h-[200px] flex items-center justify-center border border-border rounded">
              <div className="text-center space-y-2">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <div className="text-muted-foreground">Delta</div>
                    <div className="font-mono">+0.25</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Gamma</div>
                    <div className="font-mono">+0.15</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Theta</div>
                    <div className="font-mono">-0.08</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Vega</div>
                    <div className="font-mono">+0.12</div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}