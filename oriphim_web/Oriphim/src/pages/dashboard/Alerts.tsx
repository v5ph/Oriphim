import { useNavigate } from "react-router-dom";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ArrowLeft } from "lucide-react";

export default function Alerts() {
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
        <h1 className="text-lg font-mono font-semibold tracking-tight">Alerts</h1>
      </div>

      <div className="border border-border p-4 space-y-6">
        <div>
          <h2 className="text-sm font-mono font-semibold mb-4">Channels</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="email" className="font-body text-sm">Email Notifications</Label>
              <Switch id="email" />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="telegram" className="font-body text-sm">Telegram</Label>
              <Switch id="telegram" />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="discord" className="font-body text-sm">Discord</Label>
              <Switch id="discord" />
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-sm font-mono font-semibold mb-4">Alert Types</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="enter" className="font-body text-sm">Entry Signals</Label>
              <Switch id="enter" />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="exit" className="font-body text-sm">Exit Signals (TP/SL)</Label>
              <Switch id="exit" />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="risk" className="font-body text-sm">Risk Halts</Label>
              <Switch id="risk" />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="error" className="font-body text-sm">Errors</Label>
              <Switch id="error" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
