import { useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft } from "lucide-react";

export default function Runs() {
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
        <h1 className="text-lg font-mono font-semibold tracking-tight">Runs</h1>
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
              <h2 className="text-sm font-mono font-semibold mb-4">Log Stream</h2>
              <div className="flex-1 border border-border overflow-y-auto flex items-center justify-center">
                <span className="text-sm text-muted-foreground font-body">No active runs</span>
              </div>
            </div>

            {/* Position & Risk */}
            <div className="space-y-4">
              <div className="border border-border p-4">
                <h2 className="text-sm font-mono font-semibold mb-4">Positions</h2>
                <div className="h-40 border border-border overflow-y-auto flex items-center justify-center">
                  <span className="text-sm text-muted-foreground font-body">No positions</span>
                </div>
              </div>

              <div className="border border-border p-4">
                <h2 className="text-sm font-mono font-semibold mb-4">Risk</h2>
                <div className="space-y-3 text-sm font-mono">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Daily Loss Cap</span>
                    <span>$0 / $0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Kill Switches</span>
                    <span>Active</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <div className="border border-border p-12 flex flex-col items-center justify-center text-center">
            <h3 className="text-lg font-mono font-semibold mb-2">No run history</h3>
            <p className="text-sm text-muted-foreground font-body">
              Past runs will appear here
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
