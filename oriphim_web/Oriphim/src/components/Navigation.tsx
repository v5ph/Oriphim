import { Link, useLocation } from "react-router-dom";

const Navigation = () => {
  const location = useLocation();
  
  const links = [
    { path: "/", label: "Home" },
    { path: "/product", label: "Product" },
    { path: "/technology", label: "Technology" },
    { path: "/pricing", label: "Pricing" },
    { path: "/about", label: "About" },
    { path: "/contact", label: "Contact" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-xl font-mono font-semibold tracking-tight">
            ORIPHIM
          </Link>
          
          <div className="flex gap-8">
            {links.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`font-body text-sm transition-smooth ${
                  location.pathname === link.path
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {link.label}
              </Link>
            ))}
            <Link
              to="/dashboard"
              className="font-body text-sm px-4 py-1 border border-foreground hover:bg-foreground hover:text-background transition-smooth"
            >
              Dev
            </Link>
            <Link
              to="/join-waitlist"
              className="font-body text-sm px-4 py-1 bg-foreground text-background hover:bg-foreground/90 transition-smooth"
            >
              Join Waitlist
            </Link>
            <Link
              to="/signin"
              className="font-body text-sm px-4 py-1 border border-foreground hover:bg-foreground hover:text-background transition-smooth"
            >
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
