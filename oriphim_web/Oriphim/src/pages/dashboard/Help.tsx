import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Circle, ArrowLeft } from "lucide-react";

export default function Help() {
  const navigate = useNavigate();
  
  const checklistItems = [
    { title: "Create account", completed: true },
    { title: "Download Runner", completed: false },
    { title: "Generate Runner Key", completed: false },
    { title: "Connect Broker", completed: false },
    { title: "Create First Bot", completed: false },
    { title: "Start Paper Session", completed: false },
  ];

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
        <h1 className="text-lg font-mono font-semibold tracking-tight">Help & Onboarding</h1>
      </div>

      <div className="border border-border p-4">
        <h2 className="text-sm font-mono font-semibold mb-4">Getting Started Checklist</h2>
        <div className="space-y-3">
          {checklistItems.map((item, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 border border-border">
              {item.completed ? (
                <CheckCircle2 className="w-4 h-4 text-accent flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              )}
              <span className={`font-body text-sm flex-1 ${item.completed ? "line-through text-muted-foreground" : ""}`}>
                {item.title}
              </span>
              {!item.completed && (
                <Button variant="outline" size="sm" className="font-body h-8 text-xs">
                  Start
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="border border-border p-4">
        <h2 className="text-sm font-mono font-semibold mb-4">Resources</h2>
        <div className="space-y-3">
          <Button variant="outline" className="w-full justify-start font-body h-9 text-sm">
            Documentation
          </Button>
          <Button variant="outline" className="w-full justify-start font-body h-9 text-sm">
            Troubleshooting Guide
          </Button>
          <Button variant="outline" className="w-full justify-start font-body h-9 text-sm">
            Contact Support
          </Button>
        </div>
      </div>
    </div>
  );
}
