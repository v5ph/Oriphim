"""
Oriphim Runner - UI Manager

Manages the desktop UI interface including system tray, main window,
and real-time status updates. Provides minimal, clean interface for
monitoring and controlling the Runner.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Try to import system tray support
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logging.warning("System tray not available - install pillow and pystray")

logger = logging.getLogger('oriphim_runner.ui')


class UIManager:
    """
    Desktop UI manager for Oriphim Runner
    
    Features:
    - System tray integration with status indicators
    - Main status window with real-time updates
    - Minimal, clean interface following design spec
    - Async-safe UI updates from background threads
    """
    
    def __init__(self):
        self.root = None
        self.tray_icon = None
        self.is_running = False
        self.show_window = False
        
        # UI state
        self.connection_status = "disconnected"
        self.broker_status = "disconnected"
        self.current_job = None
        self.is_paused = False
        self.recent_logs = []
        
        # UI components
        self.status_labels = {}
        self.log_text = None
        self.control_buttons = {}
        
        # Thread safety
        self.ui_thread = None
        self.update_queue = asyncio.Queue() if hasattr(asyncio, 'Queue') else None
        
        logger.info("UI Manager initialized")
    
    def start(self):
        """Start the UI in the current thread"""
        try:
            self.is_running = True
            
            # Create main window
            self.root = tk.Tk()
            self.setup_main_window()
            
            # Setup system tray if available
            if TRAY_AVAILABLE:
                self.setup_system_tray()
            
            # Start with window hidden (minimized to tray)
            self.root.withdraw()
            
            # Start UI update loop
            self.root.after(1000, self.ui_update_loop)
            
            logger.info("UI started")
            
            # Run tkinter main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"UI startup error: {e}")
    
    def setup_main_window(self):
        """Setup the main status window"""
        try:
            self.root.title("Oriphim Runner")
            self.root.geometry("500x400")
            self.root.resizable(True, True)
            
            # Set window icon (if available)
            try:
                icon_path = Path(__file__).parent / "assets" / "oriphim_legend.png"
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
            except:
                pass  # Icon not critical
            
            # Create main frame
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Configure grid weights
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(1, weight=1)
            
            # Header
            header_label = ttk.Label(main_frame, text="⚛ ORIPHIM RUNNER", 
                                   font=("Arial", 14, "bold"))
            header_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
            
            # Status section
            ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, 
                                                               sticky=(tk.W, tk.E), pady=5)
            
            # Connection status
            ttk.Label(main_frame, text="● Cloud Connection:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.status_labels['cloud'] = ttk.Label(main_frame, text="DISCONNECTED", 
                                                   foreground="red")
            self.status_labels['cloud'].grid(row=2, column=1, sticky=tk.W, pady=2)
            
            # Broker status
            ttk.Label(main_frame, text="● Broker:").grid(row=3, column=0, sticky=tk.W, pady=2)
            self.status_labels['broker'] = ttk.Label(main_frame, text="DISCONNECTED", 
                                                    foreground="red")
            self.status_labels['broker'].grid(row=3, column=1, sticky=tk.W, pady=2)
            
            # Mode
            ttk.Label(main_frame, text="● Mode:").grid(row=4, column=0, sticky=tk.W, pady=2)
            self.status_labels['mode'] = ttk.Label(main_frame, text="PAPER")
            self.status_labels['mode'].grid(row=4, column=1, sticky=tk.W, pady=2)
            
            # Version
            ttk.Label(main_frame, text="● Runner Version:").grid(row=5, column=0, sticky=tk.W, pady=2)
            self.status_labels['version'] = ttk.Label(main_frame, text="v1.0.0")
            self.status_labels['version'].grid(row=5, column=1, sticky=tk.W, pady=2)
            
            # Current job
            ttk.Label(main_frame, text="● Current Job:").grid(row=6, column=0, sticky=tk.W, pady=2)
            self.status_labels['job'] = ttk.Label(main_frame, text="None")
            self.status_labels['job'].grid(row=6, column=1, sticky=tk.W, pady=2)
            
            # Logs section
            ttk.Separator(main_frame, orient='horizontal').grid(row=7, column=0, columnspan=2, 
                                                               sticky=(tk.W, tk.E), pady=(10, 5))
            
            ttk.Label(main_frame, text="▸ Latest Logs", font=("Arial", 10, "bold")).grid(
                row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
            
            # Log text area
            self.log_text = scrolledtext.ScrolledText(main_frame, height=8, width=60, 
                                                     font=("Consolas", 9))
            self.log_text.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            main_frame.rowconfigure(9, weight=1)
            
            # Control buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=10, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
            
            self.control_buttons['pause'] = ttk.Button(button_frame, text="Pause Runner", 
                                                      command=self.on_pause_click)
            self.control_buttons['pause'].grid(row=0, column=0, padx=(0, 5))
            
            self.control_buttons['restart'] = ttk.Button(button_frame, text="Restart", 
                                                        command=self.on_restart_click)
            self.control_buttons['restart'].grid(row=0, column=1, padx=5)
            
            self.control_buttons['logs'] = ttk.Button(button_frame, text="Open Logs Folder", 
                                                     command=self.on_open_logs_click)
            self.control_buttons['logs'].grid(row=0, column=2, padx=5)
            
            # Status bar
            ttk.Separator(main_frame, orient='horizontal').grid(row=11, column=0, columnspan=2, 
                                                               sticky=(tk.W, tk.E), pady=(10, 5))
            
            status_frame = ttk.Frame(main_frame)
            status_frame.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E))
            
            self.status_labels['tunnel'] = ttk.Label(status_frame, text="Secure Tunnel: Active")
            self.status_labels['tunnel'].grid(row=0, column=0, sticky=tk.W)
            
            self.status_labels['ml'] = ttk.Label(status_frame, text="Local ML: Idle")
            self.status_labels['ml'].grid(row=0, column=1, sticky=tk.E)
            status_frame.columnconfigure(1, weight=1)
            
            # Window close handling
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
            
            # Add initial log message
            self.add_log_message("UI initialized - waiting for connections...")
            
        except Exception as e:
            logger.error(f"Error setting up main window: {e}")
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        try:
            if not TRAY_AVAILABLE:
                return
            
            # Create tray icon image
            icon_image = self.create_tray_icon()
            
            # Create tray menu
            menu = pystray.Menu(
                pystray.MenuItem("Oriphim Runner", self.on_tray_title_click, enabled=False),
                pystray.MenuItem("", None),  # Separator
                pystray.MenuItem("Open Runner", self.on_tray_open_click),
                pystray.MenuItem("Pause/Resume", self.on_tray_pause_click),
                pystray.MenuItem("Restart", self.on_tray_restart_click),
                pystray.MenuItem("View Logs", self.on_tray_logs_click),
                pystray.MenuItem("", None),  # Separator
                pystray.MenuItem("Exit", self.on_tray_exit_click)
            )
            
            # Create tray icon
            self.tray_icon = pystray.Icon("oriphim_runner", icon_image, 
                                         "Oriphim Runner", menu)
            
            # Start tray icon in background thread
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            logger.info("System tray initialized")
            
        except Exception as e:
            logger.error(f"Error setting up system tray: {e}")
    
    def create_tray_icon(self, status: str = "disconnected") -> Image.Image:
        """Create system tray icon with status indicator"""
        try:
            # Try to load actual icon file
            icon_path = Path(__file__).parent / "assets" / "oriphim_legend.png"
            if icon_path.exists():
                icon = Image.open(icon_path)
                icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
            else:
                # Create simple icon
                icon = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(icon)
                
                # Draw circle background
                draw.ellipse([8, 8, 56, 56], fill=(50, 50, 50), outline=(100, 100, 100))
                
                # Draw "O" for Oriphim
                draw.text((20, 20), "O", fill=(255, 255, 255))
            
            # Add status indicator
            draw = ImageDraw.Draw(icon)
            if status == "connected":
                color = (0, 255, 0)  # Green
            elif status == "running":
                color = (255, 255, 0)  # Yellow
            else:
                color = (255, 0, 0)  # Red
            
            # Small status dot
            draw.ellipse([48, 8, 60, 20], fill=color, outline=(255, 255, 255))
            
            return icon
            
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
            # Return minimal icon
            icon = Image.new('RGBA', (64, 64), (50, 50, 50))
            return icon
    
    def ui_update_loop(self):
        """Periodic UI update loop"""
        try:
            if not self.is_running:
                return
            
            # Update tray icon if status changed
            if self.tray_icon:
                status = "connected" if self.connection_status == "connected" else "disconnected"
                if self.current_job:
                    status = "running"
                
                new_icon = self.create_tray_icon(status)
                self.tray_icon.icon = new_icon
            
            # Schedule next update
            if self.root:
                self.root.after(5000, self.ui_update_loop)  # Update every 5 seconds
                
        except Exception as e:
            logger.error(f"UI update loop error: {e}")
    
    def add_log_message(self, message: str, timestamp: datetime = None):
        """Add log message to UI"""
        try:
            if not self.log_text:
                return
            
            if timestamp is None:
                timestamp = datetime.now()
            
            formatted_message = f"[{timestamp.strftime('%H:%M:%S')}] {message}\n"
            
            # Insert at end
            self.log_text.insert(tk.END, formatted_message)
            
            # Auto-scroll to bottom
            self.log_text.see(tk.END)
            
            # Limit log size (keep last 100 lines)
            lines = self.log_text.get(1.0, tk.END).split('\n')
            if len(lines) > 100:
                # Remove oldest lines
                self.log_text.delete(1.0, f"{len(lines) - 100}.0")
            
        except Exception as e:
            logger.error(f"Error adding log message: {e}")
    
    # Async-safe update methods
    async def update_connection_status(self, status: str):
        """Update cloud connection status"""
        self.connection_status = status
        
        if self.root and self.status_labels.get('cloud'):
            if status == "connected":
                text = "CONNECTED"
                color = "green"
            else:
                text = "DISCONNECTED"
                color = "red"
            
            self.root.after(0, lambda: self.status_labels['cloud'].configure(text=text, foreground=color))
            self.root.after(0, lambda: self.add_log_message(f"Cloud connection: {status}"))
    
    async def update_broker_status(self, status: str, broker_info: Dict[str, Any] = None):
        """Update broker connection status"""
        self.broker_status = status
        
        if self.root and self.status_labels.get('broker'):
            if status == "connected":
                if broker_info:
                    text = f"IBKR {broker_info.get('mode', 'Unknown')} ({broker_info.get('account_id', 'Unknown')})"
                else:
                    text = "CONNECTED"
                color = "green"
            else:
                text = "DISCONNECTED"
                color = "red"
            
            self.root.after(0, lambda: self.status_labels['broker'].configure(text=text, foreground=color))
            self.root.after(0, lambda: self.add_log_message(f"Broker: {text}"))
    
    async def update_current_job(self, job: Optional[Dict[str, Any]]):
        """Update current job display"""
        self.current_job = job
        
        if self.root and self.status_labels.get('job'):
            if job:
                text = f"{job.get('strategy', 'Unknown')} - {job.get('symbol', 'Unknown')}"
                self.root.after(0, lambda: self.add_log_message(f"Job started: {text}"))
            else:
                text = "None"
                self.root.after(0, lambda: self.add_log_message("Job completed"))
            
            self.root.after(0, lambda: self.status_labels['job'].configure(text=text))
    
    async def update_logs(self, log_entries: List[Dict[str, Any]]):
        """Update log display"""
        self.recent_logs = log_entries
        
        # Add new log entries to UI
        for entry in log_entries[-5:]:  # Show last 5 entries
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            self.root.after(0, lambda msg=entry['message'], ts=timestamp: self.add_log_message(msg, ts))
    
    async def update_pause_status(self, is_paused: bool):
        """Update pause status"""
        self.is_paused = is_paused
        
        if self.root and self.control_buttons.get('pause'):
            text = "Resume Runner" if is_paused else "Pause Runner"
            self.root.after(0, lambda: self.control_buttons['pause'].configure(text=text))
            
            status_msg = "PAUSED" if is_paused else "RUNNING"
            self.root.after(0, lambda: self.add_log_message(f"Runner status: {status_msg}"))
    
    # Event handlers
    def on_window_close(self):
        """Handle window close - minimize to tray instead of exit"""
        self.root.withdraw()
        self.show_window = False
    
    def on_pause_click(self):
        """Handle pause/resume button click"""
        # This would trigger pause/resume in main application
        self.add_log_message("Pause/Resume requested")
    
    def on_restart_click(self):
        """Handle restart button click"""
        result = messagebox.askyesno("Restart", "Are you sure you want to restart the Runner?")
        if result:
            self.add_log_message("Restart requested")
    
    def on_open_logs_click(self):
        """Open logs folder in explorer"""
        try:
            import os
            logs_dir = Path.home() / ".oriphim" / "logs"
            
            if sys.platform == "win32":
                os.startfile(logs_dir)
            elif sys.platform == "darwin":
                os.system(f"open {logs_dir}")
            else:
                os.system(f"xdg-open {logs_dir}")
                
        except Exception as e:
            logger.error(f"Error opening logs folder: {e}")
            messagebox.showerror("Error", f"Could not open logs folder: {e}")
    
    # Tray event handlers
    def on_tray_title_click(self, icon, item):
        """Tray title click (disabled)"""
        pass
    
    def on_tray_open_click(self, icon, item):
        """Show main window from tray"""
        if self.root:
            self.root.after(0, self.root.deiconify)
            self.root.after(0, self.root.lift)
            self.show_window = True
    
    def on_tray_pause_click(self, icon, item):
        """Pause/resume from tray"""
        self.on_pause_click()
    
    def on_tray_restart_click(self, icon, item):
        """Restart from tray"""
        self.on_restart_click()
    
    def on_tray_logs_click(self, icon, item):
        """Open logs from tray"""
        self.on_open_logs_click()
    
    def on_tray_exit_click(self, icon, item):
        """Exit application from tray"""
        result = messagebox.askyesno("Exit", "Are you sure you want to exit Oriphim Runner?")
        if result:
            self.shutdown()
    
    async def show_setup_dialog(self):
        """Show initial setup dialog for API key"""
        try:
            if not self.root:
                return
            
            setup_window = tk.Toplevel(self.root)
            setup_window.title("Oriphim Runner Setup")
            setup_window.geometry("400x300")
            setup_window.grab_set()  # Modal
            
            frame = ttk.Frame(setup_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Instructions
            ttk.Label(frame, text="Welcome to Oriphim Runner!", 
                     font=("Arial", 12, "bold")).pack(pady=(0, 10))
            
            ttk.Label(frame, text="To get started, please enter your API key from the Oriphim dashboard:",
                     wraplength=350).pack(pady=(0, 10))
            
            # API key entry
            ttk.Label(frame, text="API Key:").pack(anchor=tk.W)
            api_key_var = tk.StringVar()
            api_entry = ttk.Entry(frame, textvariable=api_key_var, width=50, show="*")
            api_entry.pack(fill=tk.X, pady=(5, 10))
            
            # Instructions
            ttk.Label(frame, text="You can find your API key in the Oriphim dashboard under Settings > API Keys.",
                     wraplength=350, font=("Arial", 8)).pack(pady=(0, 20))
            
            # Buttons
            button_frame = ttk.Frame(frame)
            button_frame.pack(fill=tk.X)
            
            def on_save():
                api_key = api_key_var.get().strip()
                if api_key:
                    # Save API key (this would be handled by the main app)
                    messagebox.showinfo("Success", "API key saved! Restarting connection...")
                    setup_window.destroy()
                else:
                    messagebox.showerror("Error", "Please enter a valid API key")
            
            def on_cancel():
                setup_window.destroy()
            
            ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
            
            # Focus on entry
            api_entry.focus()
            
        except Exception as e:
            logger.error(f"Error showing setup dialog: {e}")
    
    async def shutdown(self):
        """Shutdown UI gracefully"""
        try:
            logger.info("Shutting down UI...")
            
            self.is_running = False
            
            # Stop tray icon
            if self.tray_icon:
                self.tray_icon.stop()
            
            # Close main window
            if self.root:
                self.root.quit()
            
            logger.info("UI shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during UI shutdown: {e}")


# Mock UI Manager for headless testing
class MockUIManager(UIManager):
    """Mock UI Manager that logs updates without actual UI"""
    
    def start(self):
        """Mock UI start"""
        logger.info("Mock UI started (headless mode)")
    
    async def update_connection_status(self, status: str):
        logger.info(f"UI Update: Cloud connection = {status}")
    
    async def update_broker_status(self, status: str, broker_info: Dict[str, Any] = None):
        logger.info(f"UI Update: Broker = {status}")
    
    async def update_current_job(self, job: Optional[Dict[str, Any]]):
        if job:
            logger.info(f"UI Update: Job started = {job.get('strategy')} {job.get('symbol')}")
        else:
            logger.info("UI Update: Job completed")
    
    async def show_setup_dialog(self):
        logger.info("Mock setup dialog shown")