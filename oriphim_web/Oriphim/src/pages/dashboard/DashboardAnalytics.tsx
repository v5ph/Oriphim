import { useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft } from "lucide-react";

export default function DashboardAnalytics() {
  const navigate = useNavigate();

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
        <h1 className="text-lg font-mono font-semibold tracking-tight">Analytics</h1>
      </div>

      <Tabs defaultValue="performance" className="w-full">
        <TabsList>
          <TabsTrigger value="performance" className="font-mono">Performance</TabsTrigger>
          <TabsTrigger value="regimes" className="font-mono">Regimes & IV</TabsTrigger>
          <TabsTrigger value="ai" className="font-mono">AI vs Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="mt-6 space-y-4">
          <div className="grid md:grid-cols-4 gap-4">
            <div className="border border-border p-4">
              <div className="text-xs text-muted-foreground font-body mb-2 uppercase tracking-wide">Total Return</div>
              <div className="text-2xl font-mono font-semibold">$0.00</div>
            </div>
            <div className="border border-border p-4">
              <div className="text-xs text-muted-foreground font-body mb-2 uppercase tracking-wide">Hit Rate</div>
              <div className="text-2xl font-mono font-semibold">0%</div>
            </div>
            <div className="border border-border p-4">
              <div className="text-xs text-muted-foreground font-body mb-2 uppercase tracking-wide">Expectancy</div>
              <div className="text-2xl font-mono font-semibold">$0.00</div>
            </div>
            <div className="border border-border p-4">
              <div className="text-xs text-muted-foreground font-body mb-2 uppercase tracking-wide">Sharpe</div>
              <div className="text-2xl font-mono font-semibold">0.00</div>
            </div>
          </div>

          <div className="border border-border p-4 h-[360px] flex flex-col">
            <h2 className="text-sm font-mono font-semibold mb-4">Equity Curve</h2>
            <div className="flex-1 border border-border flex items-center justify-center">
              <span className="text-sm text-muted-foreground font-body">No data</span>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="regimes" className="mt-6">
          <div className="border border-border p-12 flex flex-col items-center justify-center text-center">
            <h3 className="text-lg font-mono font-semibold mb-2">No regime data</h3>
            <p className="text-sm text-muted-foreground font-body">
              Regime detection and IV analysis will appear after running bots
            </p>
          </div>
        </TabsContent>

        <TabsContent value="ai" className="mt-6">
          <div className="border border-border p-12 flex flex-col items-center justify-center text-center">
            <h3 className="text-lg font-mono font-semibold mb-2">No AI comparison data</h3>
            <p className="text-sm text-muted-foreground font-body">
              AI Assist metrics will appear after enabling AI features
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
