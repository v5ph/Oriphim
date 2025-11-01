import { Circle } from "lucide-react";

interface StatusIndicatorProps {
  label: string;
  status: "connected" | "disconnected" | "reconnecting" | "ok" | "auth" | "closed";
  tooltip?: string;
}

export function StatusIndicator({ label, status, tooltip }: StatusIndicatorProps) {
  const getStatusColor = () => {
    switch (status) {
      case "connected":
      case "ok":
        return "fill-accent text-accent";
      case "disconnected":
      case "closed":
        return "fill-muted text-muted";
      case "reconnecting":
      case "auth":
        return "fill-yellow-500 text-yellow-500";
      default:
        return "fill-muted text-muted";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "connected":
        return "Connected";
      case "disconnected":
        return "Disconnected";
      case "reconnecting":
        return "Reconnecting";
      case "ok":
        return "OK";
      case "auth":
        return "Needs Auth";
      case "closed":
        return "Gateway Closed";
      default:
        return status;
    }
  };

  return (
    <div className="flex items-center gap-2" title={tooltip}>
      <Circle className={`w-2 h-2 ${getStatusColor()}`} />
      <span className="font-mono text-xs text-muted-foreground">
        {label}: <span className="text-foreground">{getStatusText()}</span>
      </span>
    </div>
  );
}
