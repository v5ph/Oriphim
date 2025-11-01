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

const getBotKindDisplay = (kind: Bot['kind']) => {
  const kindMap = {
    putlite: 'PUT-Lite',
    buywrite: 'Buy-Write', 
    condor: 'Iron Condor',
    gammaburst: 'Gamma Burst'
  };
  return kindMap[kind] || kind;
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

      // Update local bot enabled state
      setBots(prev => prev.map(bot => 
        bot.id === botId 
          ? { ...bot, is_enabled: action === 'start' }
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
          <TabsTrigger value="enabled">Enabled</TabsTrigger>
          <TabsTrigger value="disabled">Disabled</TabsTrigger>
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
                            {getBotKindDisplay(bot.kind)}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`h-2 w-2 rounded-full ${bot.is_enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
                          <span className="text-xs font-body">
                            {bot.is_enabled ? 'Enabled' : 'Disabled'}
                          </span>
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

                    <div className="text-sm font-body">
                      <span className="text-muted-foreground">Created:</span>
                      <p className="mt-1">{new Date(bot.created_at).toLocaleDateString()}</p>
                    </div>

                    <div className="border-t pt-3 flex items-center justify-between">
                      <div className="text-sm font-body">
                        <span className="text-muted-foreground">Status: </span>
                        <span className={bot.is_enabled ? "text-green-500" : "text-gray-500"}>
                          {bot.is_enabled ? 'Ready' : 'Disabled'}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        {bot.is_enabled ? (
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => handleBotAction(bot.id, 'stop')}
                            disabled={actionLoading === bot.id}
                            className="font-body"
                          >
                            {actionLoading === bot.id ? (
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Square className="h-3 w-3 mr-1" />
                            )}
                            Stop
                          </Button>
                        ) : (
                          <Button 
                            size="sm" 
                            onClick={() => handleBotAction(bot.id, 'start')}
                            disabled={actionLoading === bot.id}
                            className="font-body"
                          >
                            {actionLoading === bot.id ? (
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Play className="h-3 w-3 mr-1" />
                            )}
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

        <TabsContent value="enabled" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {bots
              .filter((bot) => bot.is_enabled)
              .map((bot) => (
                <Card key={bot.id} className="p-6">
                  <p className="text-sm">
                    <strong>{bot.name}</strong> - {getBotKindDisplay(bot.kind)}
                  </p>
                </Card>
              ))}
          </div>
        </TabsContent>

        <TabsContent value="disabled" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {bots
              .filter((bot) => !bot.is_enabled)
              .map((bot) => (
                <Card key={bot.id} className="p-6">
                  <p className="text-sm">
                    <strong>{bot.name}</strong> - {getBotKindDisplay(bot.kind)}
                  </p>
                </Card>
              ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}