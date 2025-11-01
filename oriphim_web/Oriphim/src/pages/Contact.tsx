import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { useState } from "react";
import { toast } from "@/hooks/use-toast";
import { supabase } from "@/lib/supabase";

const Contact = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: ""
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Insert into contact_messages table
      const { error } = await supabase
        .from('contact_messages')
        .insert([{ 
          name: formData.name,
          email: formData.email,
          message: formData.message,
          status: 'unread'
        }]);

      if (error) {
        throw new Error(error.message);
      }

      toast({
        title: "Message sent.",
        description: "We'll respond within 24 hours."
      });
      
      setFormData({
        name: "",
        email: "",
        message: ""
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  return <div className="min-h-screen">
      <Navigation />
      
      <section className="pt-32 pb-24">
        <div className="container mx-auto px-6">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <h1 className="text-5xl font-mono font-bold mb-6">Contact</h1>
              <p className="text-xl text-muted-foreground font-body">
                Questions about our platform or integration support.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block font-mono text-sm mb-2" htmlFor="name">
                  Name
                </label>
                <input type="text" id="name" required value={formData.name} onChange={e => setFormData({
                ...formData,
                name: e.target.value
              })} className="w-full px-4 py-3 border border-border bg-background font-body focus:outline-none focus:border-foreground transition-smooth" />
              </div>

              <div>
                <label className="block font-mono text-sm mb-2" htmlFor="email">
                  Email
                </label>
                <input type="email" id="email" required value={formData.email} onChange={e => setFormData({
                ...formData,
                email: e.target.value
              })} className="w-full px-4 py-3 border border-border bg-background font-body focus:outline-none focus:border-foreground transition-smooth" />
              </div>

              <div>
                <label className="block font-mono text-sm mb-2" htmlFor="message">
                  Message
                </label>
                <textarea id="message" required rows={6} value={formData.message} onChange={e => setFormData({
                ...formData,
                message: e.target.value
              })} className="w-full px-4 py-3 border border-border bg-background font-body focus:outline-none focus:border-foreground transition-smooth resize-none" />
              </div>

              <button type="submit" disabled={loading} className="w-full py-4 border border-foreground font-body hover:bg-foreground hover:text-background transition-smooth disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? "Sending..." : "Send Message"}
              </button>
            </form>

            <div className="mt-12 pt-12 border-t border-border text-center">
              <p className="text-muted-foreground font-body mb-2">Direct Email</p>
              <a href="mailto:contact@oriphim.app" className="font-mono text-lg hover:text-accent transition-smooth">contact@oriphim.com</a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>;
};
export default Contact;