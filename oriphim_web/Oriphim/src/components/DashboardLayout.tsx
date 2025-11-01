import { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { Circle } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        
        <div className="flex-1 flex flex-col">
          <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
            <div className="flex h-14 items-center gap-4 px-6">
              <SidebarTrigger />
              
              <Link to="/" className="text-lg font-mono font-semibold tracking-tight">
                ORIPHIM
              </Link>

              <div className="flex-1" />

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Circle className="w-2 h-2 fill-accent text-accent" />
                  <span className="font-mono text-xs text-muted-foreground">Runner Connected</span>
                </div>

                <Badge variant="secondary" className="font-mono text-xs">
                  PAPER
                </Badge>

                <DropdownMenu>
                  <DropdownMenuTrigger className="font-mono text-sm hover:text-foreground transition-smooth">
                    Account
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>My Account</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>Profile</DropdownMenuItem>
                    <DropdownMenuItem>Plan & Billing</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>Logout</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </header>

          <main className="flex-1 p-6">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
