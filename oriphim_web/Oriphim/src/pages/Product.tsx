import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Link } from "react-router-dom";

const bots = [
  {
    name: "Put-Lite",
    description: "Conservative intraday credit spreads.",
    params: ["Risk per trade", "Time window", "Symbols", "Mode: Paper/Live"],
  },
  {
    name: "Gamma Burst",
    description: "Momentum-driven directional plays.",
    params: ["Risk per trade", "Time window", "Symbols", "Mode: Paper/Live"],
  },
  {
    name: "Condor",
    description: "Iron condor builder for balanced setups.",
    params: ["Risk per trade", "Time window", "Symbols", "Mode: Paper/Live"],
  },
  {
    name: "Buy-Write",
    description: "Covered call rotation system.",
    params: ["Risk per trade", "Time window", "Symbols", "Mode: Paper/Live"],
  },
];

const Product = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      
      <section className="pt-32 pb-24">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto text-center mb-20">
            <h1 className="text-5xl font-mono font-bold mb-6">Trading Bots & Strategies.</h1>
            <p className="text-xl text-muted-foreground font-body">
              Each Oriphim bot runs locally through your connected brokerage.
            </p>
          </div>

          {/* Bot Grid */}
          <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto mb-24">
            {bots.map((bot) => (
              <div key={bot.name} className="border border-border p-8 hover:border-muted-foreground transition-smooth">
                <h3 className="text-2xl font-mono font-semibold mb-3">{bot.name}</h3>
                <p className="text-muted-foreground font-body mb-6">{bot.description}</p>
                
                <div className="space-y-3">
                  {bot.params.map((param, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="font-body text-muted-foreground">{param}</span>
                      <div className="w-32 h-1 bg-border" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Explainer Section */}
          <div className="border-t border-border pt-24">
            <div className="max-w-4xl mx-auto">
              <div className="grid md:grid-cols-2 gap-12 items-center">
                <div>
                  <h2 className="text-3xl font-mono font-bold mb-6">Configure and Execute</h2>
                  <p className="text-muted-foreground font-body leading-relaxed mb-6">
                    Adjust parameters, click Start Paper Mode, and Oriphim sends jobs to your local Runner for execution.
                  </p>
                  <p className="text-muted-foreground font-body leading-relaxed">
                    Once verified, promote strategies to live trading with a single toggle.
                  </p>
                </div>
                
                <div className="border border-border p-8">
                  <div className="space-y-4 font-mono text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Bot Status</span>
                      <span className="text-accent">PAPER ACTIVE</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Trades Today</span>
                      <span>12</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Win Rate</span>
                      <span>67%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">P/L (Session)</span>
                      <span className="text-accent">+$240</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center mt-24">
            <Link
              to="/signup"
              className="inline-block px-8 py-4 border border-foreground font-body hover:bg-foreground hover:text-background transition-smooth"
            >
              Create Your Account
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Product;
