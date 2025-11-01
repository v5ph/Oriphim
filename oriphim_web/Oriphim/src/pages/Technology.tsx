import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { ArrowRight } from "lucide-react";

const Technology = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      
      <section className="pt-32 pb-24">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto text-center mb-20">
            <h1 className="text-5xl font-mono font-bold mb-6">The Runner: Your Local Execution Layer.</h1>
          </div>

          {/* Architecture Diagram */}
          <div className="max-w-5xl mx-auto mb-24">
            <div className="grid md:grid-cols-2 gap-16">
              <div className="flex flex-col items-center justify-center space-y-8">
                <div className="border border-border p-6 w-full text-center">
                  <p className="font-mono">Web Dashboard</p>
                </div>
                <ArrowRight className="rotate-90 md:rotate-0 text-muted-foreground" size={32} />
                <div className="border border-border p-6 w-full text-center">
                  <p className="font-mono">Secure WebSocket</p>
                </div>
                <ArrowRight className="rotate-90 md:rotate-0 text-muted-foreground" size={32} />
                <div className="border border-border p-6 w-full text-center">
                  <p className="font-mono">Local Runner</p>
                </div>
                <ArrowRight className="rotate-90 md:rotate-0 text-muted-foreground" size={32} />
                <div className="border border-border p-6 w-full text-center">
                  <p className="font-mono">Broker API</p>
                </div>
              </div>

              <div className="space-y-6">
                <div className="border-l-2 border-accent pl-6">
                  <h3 className="font-mono font-semibold mb-2">Lightweight</h3>
                  <p className="text-muted-foreground font-body">Runner is ~20 MB.</p>
                </div>
                
                <div className="border-l-2 border-accent pl-6">
                  <h3 className="font-mono font-semibold mb-2">Local Execution</h3>
                  <p className="text-muted-foreground font-body">All order routing happens on your machine.</p>
                </div>
                
                <div className="border-l-2 border-accent pl-6">
                  <h3 className="font-mono font-semibold mb-2">Zero Credential Exposure</h3>
                  <p className="text-muted-foreground font-body">Oriphim servers never handle brokerage credentials.</p>
                </div>
                
                <div className="border-l-2 border-accent pl-6">
                  <h3 className="font-mono font-semibold mb-2">Real-time Sync</h3>
                  <p className="text-muted-foreground font-body">P/L and order updates sync automatically.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Reliability Section */}
          <div className="border-t border-border pt-24">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-4xl font-mono font-bold mb-8">Reliable by Design.</h2>
              <p className="text-lg font-body text-muted-foreground leading-relaxed">
                Once installed, the Runner reconnects automatically on startup and executes jobs on schedule. 
                You can monitor or pause bots from your browser anytime.
              </p>
            </div>
          </div>

          {/* Technical Specs */}
          <div className="mt-24 max-w-4xl mx-auto">
            <div className="grid md:grid-cols-3 gap-8">
              <div className="border border-border p-6">
                <h4 className="font-mono text-sm text-muted-foreground mb-2">Platform</h4>
                <p className="font-mono">Windows, macOS, Linux</p>
              </div>
              
              <div className="border border-border p-6">
                <h4 className="font-mono text-sm text-muted-foreground mb-2">Connection</h4>
                <p className="font-mono">Secure WebSocket (WSS)</p>
              </div>
              
              <div className="border border-border p-6">
                <h4 className="font-mono text-sm text-muted-foreground mb-2">Brokers Supported</h4>
                <p className="font-mono">IBKR, Tradier, TD</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Technology;
