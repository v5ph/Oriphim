import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider, ProtectedRoute } from "@/contexts/AuthContext";
import Home from "./pages/Home";
import Product from "./pages/Product";
import Technology from "./pages/Technology";
import Pricing from "./pages/Pricing";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";
import Bots from "./pages/dashboard/Bots";
import Trading from "./pages/dashboard/Trading";
import Runs from "./pages/dashboard/Runs";
import DashboardAnalytics from "./pages/dashboard/DashboardAnalytics";
import Alerts from "./pages/dashboard/Alerts";
import DashboardSettings from "./pages/dashboard/DashboardSettings";
import Help from "./pages/dashboard/Help";
import Analytics from "./pages/Analytics";
import About from "./pages/About";
import Contact from "./pages/Contact";
import JoinWaitlist from "./pages/JoinWaitlist";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product" element={<Product />} />
          <Route path="/technology" element={<Technology />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/dashboard/bots" element={<ProtectedRoute><Bots /></ProtectedRoute>} />
          <Route path="/dashboard/trading" element={<ProtectedRoute><Trading /></ProtectedRoute>} />
          <Route path="/dashboard/runs" element={<ProtectedRoute><Runs /></ProtectedRoute>} />
          <Route path="/dashboard/analytics" element={<ProtectedRoute><DashboardAnalytics /></ProtectedRoute>} />
          <Route path="/dashboard/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
          <Route path="/dashboard/settings" element={<ProtectedRoute><DashboardSettings /></ProtectedRoute>} />
          <Route path="/dashboard/help" element={<ProtectedRoute><Help /></ProtectedRoute>} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/join-waitlist" element={<JoinWaitlist />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </AuthProvider>
</QueryClientProvider>
);

export default App;
