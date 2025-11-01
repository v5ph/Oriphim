import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Play, Square, MoreVertical, Copy, Edit, Trash2, ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { supabase } from "@/lib/supabase";
import { useAuthContext } from "@/contexts/AuthContext";
import type { Database } from "@/lib/supabase";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type Bot = Database['public']['Tables']['bots']['Row'];



const getStatusColor = (status: string) => {
  switch (status) {
    case "running":
      return "text-green-500";
    case "paused":
      return "text-muted-foreground";
    case "error":
      return "text-destructive";
    default:
      return "text-muted-foreground";
  }
};

const getStatusDot = (status: string) => {
  switch (status) {
    case "running":
      return "bg-green-500 animate-pulse";
    case "paused":
      return "bg-muted-foreground";
    case "error":
      return "bg-destructive";
    default:
      return "bg-muted-foreground";
  }
};

const getModeVariant = (mode: string) => {
  return mode === "LIVE" ? "destructive" : "secondary";
};

export default function Bots() {
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Fetch user's bots
  useEffect(() => {
    if (!user) return;
    
    const fetchBots = async () => {
      try {
        const { data, error } = await supabase
          .from('bots')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });

        if (error) throw error;
        setBots(data || []);
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to load bots",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchBots();
  }, [user]);

  // Handle bot start/stop actions
  const handleBotAction = async (botId: string, action: 'start' | 'stop') => {
    setActionLoading(botId);
    
    try {
      const { data, error } = await supabase.functions.invoke(`${action}-run`, {
        body: { bot_id: botId }
      });

      if (error) throw error;

      // Update local state
      setBots(prev => prev.map(bot => 
        bot.id === botId 
          ? { ...bot, status: action === 'start' ? 'running' : 'stopped' }
          : bot
      ));

      toast({
        title: "Success",
        description: `Bot ${action === 'start' ? 'started' : 'stopped'} successfully`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${action} bot`,
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 pb-16">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/dashboard")}
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-smooth"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Dashboard
          </button>
          <h1 className="text-lg font-mono font-semibold tracking-tight">Bots</h1>
        </div>
        <Button className="font-body h-9 text-sm">Create Bot</Button>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="running">Running</TabsTrigger>
          <TabsTrigger value="paused">Paused</TabsTrigger>
          <TabsTrigger value="stopped">Stopped</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : bots.length === 0 ? (
            <div className="text-center py-12 border border-border rounded-lg">
              <p className="text-muted-foreground mb-4">No bots created yet</p>
              <Button className="font-body">Create Your First Bot</Button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {bots.map((bot) => (
              <Card key={bot.id} className="p-6">
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-mono font-semibold text-lg">{bot.name}</h3>
                        <Badge variant="outline" className="font-body text-xs">
                          {bot.kind}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`h-2 w-2 rounded-full ${getStatusDot(bot.status)}`} />
                        <span className={`text-xs font-body capitalize ${getStatusColor(bot.status)}`}>
                          {bot.status === "running" ? "Running" : bot.status}
                        </span>
                        <Badge variant={getModeVariant(bot.mode)} className="font-body text-xs">
                          {bot.mode}
                        </Badge>
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Copy className="h-4 w-4 mr-2" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm font-body">
                    <div>
                      <span className="text-muted-foreground">Symbols:</span>
                      <div className="flex gap-1 mt-1">
                        {bot.symbols.map((symbol) => (
                          <Badge key={symbol} variant="outline" className="text-xs">
                            {symbol}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Schedule:</span>
                      <p className="mt-1">{bot.schedule}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Risk/Trade:</span>
                      <p className="mt-1">{bot.riskPerTrade}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Daily Cap:</span>
                      <p className="mt-1">{bot.dailyCap}</p>
                    </div>
                  </div>

                  <div className="border-t pt-3 flex items-center justify-between">
                    <div className="text-sm font-body">
                      <span className="text-muted-foreground">Last run: </span>
                      <span className={bot.lastRun.pl.startsWith("+") ? "text-green-500" : bot.lastRun.pl.startsWith("-") ? "text-destructive" : ""}>
                        {bot.lastRun.pl}
                      </span>
                      <span className="text-muted-foreground ml-2">{bot.lastRun.time}</span>
                    </div>
                    <div className="flex gap-2">
                      {bot.status === "running" ? (
                        <Button size="sm" variant="outline" className="font-body">
                          <Square className="h-3 w-3 mr-1" />
                          Stop
                        </Button>
                      ) : (
                        <Button size="sm" className="font-body">
                          <Play className="h-3 w-3 mr-1" />
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="running" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {bots
              .filter((bot) => bot.status === "running")
              .map((bot) => (
                <Card key={bot.id} className="p-6">
                  <p className="text-sm text-muted-foreground">Running bot: {bot.name}</p>
                </Card>
              ))}
          </div>
        </TabsContent>

        <TabsContent value="paused" className="mt-6">
          <div className="text-center p-12 border border-border">
            <p className="text-sm text-muted-foreground">No paused bots</p>
          </div>
        </TabsContent>

        <TabsContent value="stopped" className="mt-6">
          <div className="text-center p-12 border border-border">
            <p className="text-sm text-muted-foreground">No stopped bots</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
