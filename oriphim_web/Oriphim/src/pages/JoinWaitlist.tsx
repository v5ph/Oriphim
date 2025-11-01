import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { supabase } from "@/lib/supabase";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";

const JoinWaitlist = () => {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Insert into waitlist table
      const { error } = await supabase
        .from('waitlist')
        .insert([{ 
          email,
          source: 'website'
        }]);

      if (error) {
        // Handle duplicate email error specifically
        if (error.code === '23505') {
          throw new Error('This email is already on our waitlist!');
        }
        throw new Error(error.message);
      }

      setSubmitted(true);
      toast({
        title: "You're on the list!",
        description: "We'll notify you as soon as we launch.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to join waitlist",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navigation />
      
      <main className="flex-1 flex items-center justify-center px-6 pt-20">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-mono font-bold tracking-tight mb-4">
              Join the Waitlist
            </h1>
            <p className="text-muted-foreground">
              Be the first to know when ORIPHIM launches. Get early access to our autonomous trading platform.
            </p>
          </div>

          {!submitted ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full"
                />
              </div>

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50"
            >
              {loading ? "Joining..." : "Join Waitlist"}
            </Button>              <p className="text-xs text-muted-foreground text-center">
                We'll never share your email. Unsubscribe anytime.
              </p>
            </form>
          ) : (
            <div className="text-center p-8 border border-border rounded-lg bg-card">
              <h2 className="text-2xl font-semibold mb-2">You're on the list!</h2>
              <p className="text-muted-foreground">
                We'll send you updates as we get closer to launch.
              </p>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default JoinWaitlist;
