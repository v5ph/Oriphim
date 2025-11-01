import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: {
    value: string;
    positive: boolean;
  };
  onClick?: () => void;
}

export function KPICard({ title, value, icon: Icon, trend, onClick }: KPICardProps) {
  return (
    <div
      className={`border border-border p-4 flex flex-col gap-2 ${onClick ? "cursor-pointer hover:bg-muted/50 transition-smooth" : ""}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs uppercase tracking-wide text-muted-foreground font-body">{title}</p>
        {Icon && <Icon className="w-4 h-4 text-muted-foreground" />}
      </div>
      <p className="text-2xl font-mono font-semibold leading-none">{value}</p>
      {trend && (
        <p className={`text-xs font-mono ${trend.positive ? "text-accent" : "text-destructive"}`}>
          {trend.value}
        </p>
      )}
    </div>
  );
}
