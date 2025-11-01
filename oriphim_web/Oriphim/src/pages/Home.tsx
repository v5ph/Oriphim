import { Link } from "react-router-dom";
import { Shield, Cloud, Target } from "lucide-react";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";

const Home = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 grid-pattern animate-grid opacity-20" />
        
        <div className="container mx-auto px-6 relative z-10 fade-in">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-6xl md:text-7xl font-mono font-bold mb-6 tracking-tight">
              Automated Options Trading,<br />Done Right.
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground font-body mb-12 max-w-2xl mx-auto">
              Oriphim connects your brokerage, executes strategies locally, and syncs performance in real time.
            </p>
            <Link
              to="/signup"
              className="inline-block px-8 py-4 border-2 border-foreground font-body font-medium hover:bg-foreground hover:text-background transition-smooth"
            >
              Get Started
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 border-t border-border">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-12">
            <div className="border border-border p-8 hover:border-muted-foreground transition-smooth">
              <Shield className="w-12 h-12 mb-6" />
              <h3 className="text-2xl font-mono font-semibold mb-4">Secure Local Execution</h3>
              <p className="text-muted-foreground font-body">
                Your trades execute from your computer through the Oriphim Runner.
              </p>
            </div>
            
            <div className="border border-border p-8 hover:border-muted-foreground transition-smooth">
              <Cloud className="w-12 h-12 mb-6" />
              <h3 className="text-2xl font-mono font-semibold mb-4">Cloud Control</h3>
              <p className="text-muted-foreground font-body">
                Manage and monitor bots from any browser.
              </p>
            </div>
            
            <div className="border border-border p-8 hover:border-muted-foreground transition-smooth">
              <Target className="w-12 h-12 mb-6" />
              <h3 className="text-2xl font-mono font-semibold mb-4">Built for Precision</h3>
              <p className="text-muted-foreground font-body">
                No copy-paste scripts. No remote execution risk.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 border-t border-border">
        <div className="container mx-auto px-6">
          <h2 className="text-4xl font-mono font-bold text-center mb-16">How Oriphim Works</h2>
          
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="text-center">
                <div className="w-16 h-16 border-2 border-foreground flex items-center justify-center mx-auto mb-4 font-mono text-xl">
                  01
                </div>
                <p className="font-body text-muted-foreground">Dashboard</p>
              </div>
              
              <div className="h-px w-full md:w-20 bg-border" />
              
              <div className="text-center">
                <div className="w-16 h-16 border-2 border-foreground flex items-center justify-center mx-auto mb-4 font-mono text-xl">
                  02
                </div>
                <p className="font-body text-muted-foreground">Runner</p>
              </div>
              
              <div className="h-px w-full md:w-20 bg-border" />
              
              <div className="text-center">
                <div className="w-16 h-16 border-2 border-foreground flex items-center justify-center mx-auto mb-4 font-mono text-xl">
                  03
                </div>
                <p className="font-body text-muted-foreground">Brokerage</p>
              </div>
              
              <div className="h-px w-full md:w-20 bg-border" />
              
              <div className="text-center">
                <div className="w-16 h-16 border-2 border-foreground flex items-center justify-center mx-auto mb-4 font-mono text-xl">
                  04
                </div>
                <p className="font-body text-muted-foreground">Analytics</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-24 border-t border-border">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl font-mono font-bold mb-8">Tested in Live Markets.</h2>
            <p className="text-lg font-body text-muted-foreground leading-relaxed mb-8">
              Our team and early users have run Oriphim bots across multiple brokerages under live and paper conditions. 
              We continually test and refine strategies to improve consistency.
            </p>
            <Link
              to="/product"
              className="inline-block px-8 py-4 border border-foreground font-body hover:bg-foreground hover:text-background transition-smooth"
            >
              Explore Bots
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Home;
