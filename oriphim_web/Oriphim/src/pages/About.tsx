import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import philImage from "@/assets/phil-v.jpg";
const team = [{
  name: "Phil V",
  role: "Founder & Lead Engineer",
  bio: "ML researcher and automations engineer - Currently in college",
  twitter: "https://x.com/_phil_v",
  image: philImage
}];
const About = () => {
  return <div className="min-h-screen">
      <Navigation />
      
      <section className="pt-16 pb-12 py-0">
        <div className="container mx-auto px-6">
          <div className="max-w-3xl mx-auto text-center mb-20">
            <h1 className="text-5xl font-mono font-bold mb-6">Our Approach.</h1>
          </div>

          {/* Mission */}
          <div className="max-w-3xl mx-auto mb-24">
            <p className="text-xl font-body text-muted-foreground leading-relaxed mb-8">
              Oriphim is focused on reliability and transparency in automated trading. 
              It is built around one principle - execute precisely, analyze clearly.
            </p>
            <p className="text-xl font-body text-muted-foreground leading-relaxed">
              Every component of the platform is designed to minimize risk, maximize control, and provide 
              complete visibility to trading operations. Trading proficiently and professionally made accessible.
            </p>
          </div>

          {/* Team */}
          <div className="border-t border-border pt-24">
          <h2 className="text-4xl font-mono font-bold text-center mb-16">Team</h2>
            
            <div className="flex justify-center max-w-5xl mx-auto">
              {team.map(member => <div key={member.name} className="border border-border p-8 text-center max-w-sm">
                  <img src={member.image} alt={member.name} className="w-24 h-24 mx-auto mb-6 object-cover" />
                  <h3 className="text-xl font-mono font-semibold mb-2">{member.name}</h3>
                  <p className="text-sm text-accent font-body mb-4">{member.role}</p>
                  <p className="text-sm text-muted-foreground font-body mb-4">{member.bio}</p>
                  <a href={member.twitter} target="_blank" rel="noopener noreferrer" className="text-sm text-foreground hover:text-accent transition-colors font-body">
                    @_phil_v
                  </a>
                </div>)}
            </div>
          </div>

          {/* Values */}
          <div className="border-t border-border pt-24 mt-24">
            <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
              <div>
                <h3 className="text-2xl font-mono font-semibold mb-4">Engineering First</h3>
                <p className="text-muted-foreground font-body">
                  We prioritize system stability, security, and performance over feature complexity. 
                  Every component is tested extensively before deployment.
                </p>
              </div>
              
              <div>
                <h3 className="text-2xl font-mono font-semibold mb-4">Transparent Operations</h3>
                <p className="text-muted-foreground font-body">
                  All trades, analytics, and system operations are visible to users. 
                  We believe transparency builds trust and enables better decision-making.
                </p>
              </div>
              
              <div>
                <h3 className="text-2xl font-mono font-semibold mb-4">User Control</h3>
                <p className="text-muted-foreground font-body">
                  Your capital, your rules. We provide the tools and infrastructure — 
                  you maintain complete control over execution and risk parameters.
                </p>
              </div>
              
              
            </div>
          </div>

          {/* Contact Info */}
          <div className="border-t border-border pt-12 mt-12 text-center">
            <p className="text-muted-foreground font-body mb-2">For any questions, concerns, bugs found, or feedback</p>
            <p className="text-muted-foreground font-body font-extrabold text-xl">contact@oriphim.com</p>
          </div>
        </div>
      </section>

      <Footer />
    </div>;
};
export default About;