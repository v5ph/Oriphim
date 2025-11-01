import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Check } from "lucide-react";
import { Link } from "react-router-dom";

const plans = [
  {
    name: "Starter",
    price: "Free",
    features: [
      "Paper trading mode",
      "Basic analytics",
      "Single bot instance",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$49/month",
    features: [
      "Live trading support",
      "Multi-bot management",
      "IBKR, Tradier, TD integrations",
      "Advanced analytics",
      "Email support",
    ],
  },
  {
    name: "Elite",
    price: "$99/month",
    features: [
      "Everything in Pro",
      "Regime tracking",
      "Custom bot parameters",
      "Priority support",
      "Dedicated account manager",
    ],
  },
];

const Pricing = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      
      <section className="pt-32 pb-24">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto text-center mb-20">
            <h1 className="text-5xl font-mono font-bold mb-6">Transparent Pricing.</h1>
            <p className="text-xl text-muted-foreground font-body">
              Start with paper trading, scale to live execution.
            </p>
          </div>

          {/* Pricing Grid */}
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {plans.map((plan, idx) => (
              <div
                key={plan.name}
                className={`border p-8 transition-smooth ${
                  idx === 1
                    ? "border-muted-foreground"
                    : "border-border hover:border-muted-foreground"
                }`}
              >
                <h3 className="text-2xl font-mono font-semibold mb-2">{plan.name}</h3>
                <p className="text-4xl font-mono font-bold mb-8">{plan.price}</p>
                
                <div className="space-y-4 mb-8">
                  {plan.features.map((feature) => (
                    <div key={feature} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
                      <span className="font-body text-muted-foreground">{feature}</span>
                    </div>
                  ))}
                </div>
                
                <Link
                  to="/signup"
                  className={`block w-full py-3 text-center border font-body transition-smooth ${
                    idx === 1
                      ? "border-foreground bg-foreground text-background hover:bg-transparent hover:text-foreground"
                      : "border-foreground hover:bg-foreground hover:text-background"
                  }`}
                >
                  Get Started
                </Link>
              </div>
            ))}
          </div>

          {/* Additional Info */}
          <div className="mt-24 max-w-3xl mx-auto text-center">
            <p className="text-muted-foreground font-body mb-8">
              All plans include access to the Oriphim Runner and cloud dashboard. 
              Upgrade or downgrade anytime.
            </p>
            <Link
              to="/signup"
              className="inline-block px-8 py-4 border border-foreground font-body hover:bg-foreground hover:text-background transition-smooth"
            >
              Sign Up and Connect Your Brokerage
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Pricing;
