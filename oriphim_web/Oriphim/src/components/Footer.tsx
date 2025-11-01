import { Link } from "react-router-dom";

const Footer = () => {
  return (
    <footer className="border-t border-border mt-24 py-12">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div>
            <h3 className="font-mono text-lg mb-4">ORIPHIM</h3>
            <p className="text-muted-foreground text-sm font-body">
              Automated options trading platform for professionals.
            </p>
          </div>
          
          <div>
            <h4 className="font-mono text-sm mb-4 text-muted-foreground">Product</h4>
            <div className="space-y-2">
              <Link to="/product" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                Trading Bots
              </Link>
              <Link to="/technology" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                Technology
              </Link>
              <Link to="/pricing" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                Pricing
              </Link>
            </div>
          </div>
          
          <div>
            <h4 className="font-mono text-sm mb-4 text-muted-foreground">Company</h4>
            <div className="space-y-2">
              <Link to="/about" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                About
              </Link>
              <Link to="/contact" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                Contact
              </Link>
            </div>
          </div>
          
          <div>
            <h4 className="font-mono text-sm mb-4 text-muted-foreground">Legal</h4>
            <div className="space-y-2">
              <a href="#" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                Terms
              </a>
              <a href="#" className="block text-sm font-body text-muted-foreground hover:text-foreground transition-smooth">
                Privacy
              </a>
            </div>
          </div>
        </div>
        
        <div className="mt-12 pt-8 border-t border-border">
          <p className="text-sm font-body text-muted-foreground text-center">
            © 2025 Oriphim. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
