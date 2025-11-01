import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";

const Analytics = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      
      <section className="pt-32 pb-24">
        <div className="container mx-auto px-6">
          <div className="mb-12">
            <h1 className="text-4xl font-mono font-bold mb-4">Analytics</h1>
            <p className="text-muted-foreground font-body">
              Performance data from your live and paper sessions.
            </p>
          </div>

          {/* Charts Grid */}
          <div className="grid lg:grid-cols-2 gap-8 mb-8">
            {/* Daily Returns */}
            <div className="border border-border p-6">
              <h2 className="text-xl font-mono font-semibold mb-6">Daily Returns</h2>
              <div className="h-64 border border-border relative">
                <svg className="w-full h-full" viewBox="0 0 400 200">
                  <polyline
                    points="0,180 50,140 100,160 150,100 200,120 250,60 300,80 350,40 400,50"
                    fill="none"
                    stroke="hsl(var(--foreground))"
                    strokeWidth="2"
                  />
                </svg>
              </div>
            </div>

            {/* Trade Distribution */}
            <div className="border border-border p-6">
              <h2 className="text-xl font-mono font-semibold mb-6">Trade Distribution</h2>
              <div className="h-64 border border-border flex items-end justify-between p-4 gap-2">
                {[85, 95, 70, 60, 80, 90, 75, 65, 55, 85].map((height, idx) => (
                  <div key={idx} className="flex-1 bg-muted" style={{ height: `${height}%` }} />
                ))}
              </div>
            </div>
          </div>

          {/* Summary Stats Table */}
          <div className="border border-border p-6">
            <h2 className="text-xl font-mono font-semibold mb-6">Trade History</h2>
            <div className="overflow-x-auto">
              <table className="w-full font-mono text-sm">
                <thead className="border-b border-border">
                  <tr className="text-muted-foreground text-left">
                    <th className="pb-3">Date</th>
                    <th className="pb-3">Bot</th>
                    <th className="pb-3">Symbol</th>
                    <th className="pb-3">Result</th>
                    <th className="pb-3">IV Rank</th>
                    <th className="pb-3">P/L</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border">
                    <td className="py-3">2025-01-15</td>
                    <td className="py-3">Put-Lite</td>
                    <td className="py-3">SPY</td>
                    <td className="py-3 text-accent">WIN</td>
                    <td className="py-3">42</td>
                    <td className="py-3 text-accent">+$125</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3">2025-01-15</td>
                    <td className="py-3">Gamma Burst</td>
                    <td className="py-3">QQQ</td>
                    <td className="py-3 text-destructive">LOSS</td>
                    <td className="py-3">38</td>
                    <td className="py-3 text-destructive">-$80</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3">2025-01-14</td>
                    <td className="py-3">Condor</td>
                    <td className="py-3">IWM</td>
                    <td className="py-3 text-accent">WIN</td>
                    <td className="py-3">55</td>
                    <td className="py-3 text-accent">+$200</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3">2025-01-14</td>
                    <td className="py-3">Buy-Write</td>
                    <td className="py-3">AAPL</td>
                    <td className="py-3 text-accent">WIN</td>
                    <td className="py-3">31</td>
                    <td className="py-3 text-accent">+$95</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Info Text */}
          <div className="mt-12 max-w-3xl mx-auto text-center">
            <p className="text-muted-foreground font-body">
              Analytics are built from your live and paper sessions, available directly in the browser.
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Analytics;
