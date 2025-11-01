#!/usr/bin/env python3
"""
Oriphim Runner - Main Application Entry Point

A lightweight desktop companion that securely executes trading bots locally
while syncing with the Oriphim Cloud dashboard. Handles execution via IBKR,
provides real-time status updates, and maintains secure cloud connectivity.

Architecture:
- Cloud: Supabase backend with WebSocket channels
- Runner: Local Python core with minimal UI
- Broker: IBKR TWS/Gateway connection
- UI: HTML/CSS/JS frontend via Tauri or tkinter
"""

import asyncio
import sys
import os
import logging
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import time

# Add ibkr_bots to path for importing trading logic
sys.path.insert(0, str(Path(__file__).parent.parent / "ibkr_bots"))

from websocket_client import CloudWebSocketClient
from broker_ibkr import IBKRManager
from engine import TradingEngine
from storage import LocalDataManager
from ui_manager import UIManager

# Configure logging
def setup_logging():
    """Set up comprehensive logging for the Runner"""
    log_dir = Path.home() / ".oriphim" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"runner_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger('oriphim_runner')


class OriphimRunner:
    """
    Main Oriphim Runner Application
    
    Coordinates all components:
    - Cloud WebSocket connection
    - IBKR broker management  
    - Trading engine execution
    - Local data persistence
    - UI status updates
    """
    
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("=" * 60)
        self.logger.info("ORIPHIM RUNNER STARTING")
        self.logger.info(f"Version: 1.0.0")
        self.logger.info(f"Platform: {sys.platform}")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.data_manager = LocalDataManager()
        self.ui_manager = UIManager()
        self.ibkr_manager = IBKRManager()
        self.trading_engine = TradingEngine()
        
        # WebSocket client for cloud communication
        self.ws_client = None
        
        # Application state
        self.is_running = False
        self.is_paused = False
        self.current_job = None
        self.connection_status = "disconnected"
        self.broker_status = "disconnected"
        
        # Event loop and threads
        self.loop = None
        self.ui_thread = None
        
        self.logger.info("Oriphim Runner initialized")
    
    async def start(self):
        """Start the Oriphim Runner application"""
        try:
            self.is_running = True
            
            # 1. Initialize local data storage
            await self.data_manager.initialize()
            
            # 2. Load configuration
            config = await self.data_manager.load_config()
            if not config or not config.get('api_key'):
                self.logger.warning("No API key found - user setup required")
                await self.ui_manager.show_setup_dialog()
                return
            
            # 3. Start UI in separate thread
            self.ui_thread = threading.Thread(target=self.ui_manager.start, daemon=True)
            self.ui_thread.start()
            
            # 4. Connect to IBKR broker
            await self.connect_broker()
            
            # 5. Establish cloud WebSocket connection
            await self.connect_cloud(config['api_key'])
            
            # 6. Start main event loop
            await self.main_loop()
            
        except Exception as e:
            self.logger.error(f"Failed to start Oriphim Runner: {e}")
            await self.shutdown()
    
    async def connect_broker(self):
        """Connect to IBKR broker"""
        try:
            self.logger.info("Connecting to IBKR broker...")
            
            connected = await self.ibkr_manager.connect()
            if connected:
                self.broker_status = "connected"
                broker_info = await self.ibkr_manager.get_account_info()
                self.logger.info(f"IBKR connected: {broker_info}")
                
                # Update UI
                await self.ui_manager.update_broker_status(self.broker_status, broker_info)
            else:
                self.broker_status = "error"
                self.logger.error("Failed to connect to IBKR")
                
        except Exception as e:
            self.broker_status = "error"
            self.logger.error(f"Broker connection error: {e}")
    
    async def connect_cloud(self, api_key: str):
        """Establish WebSocket connection to Oriphim Cloud"""
        try:
            self.logger.info("Connecting to Oriphim Cloud...")
            
            self.ws_client = CloudWebSocketClient(
                api_key=api_key,
                on_job_received=self.handle_job_received,
                on_status_request=self.handle_status_request,
                on_connection_change=self.handle_connection_change
            )
            
            connected = await self.ws_client.connect()
            if connected:
                self.connection_status = "connected"
                self.logger.info("Cloud connection established")
                
                # Send initial status
                await self.send_status_update()
            else:
                self.connection_status = "error"
                self.logger.error("Failed to connect to cloud")
                
        except Exception as e:
            self.connection_status = "error"
            self.logger.error(f"Cloud connection error: {e}")
    
    async def handle_job_received(self, job: Dict[str, Any]):
        """Handle new trading job from cloud"""
        try:
            self.logger.info(f"Received job: {job.get('id', 'unknown')}")
            
            if self.is_paused:
                self.logger.warning("Runner is paused - rejecting job")
                await self.ws_client.send_job_status(job['id'], 'rejected', 'Runner paused')
                return
            
            if self.current_job:
                self.logger.warning("Already executing job - queuing new job")
                # TODO: Implement job queue
                return
            
            self.current_job = job
            
            # Update UI
            await self.ui_manager.update_current_job(job)
            
            # Execute job
            result = await self.trading_engine.execute_job(job, self.ibkr_manager)
            
            # Send results back to cloud
            await self.ws_client.send_job_results(job['id'], result)
            
            # Log trade activity
            await self.data_manager.log_trade(job, result)
            
            self.current_job = None
            await self.ui_manager.update_current_job(None)
            
        except Exception as e:
            self.logger.error(f"Error handling job: {e}")
            if self.current_job:
                await self.ws_client.send_job_status(
                    self.current_job['id'], 'error', str(e)
                )
                self.current_job = None
    
    async def handle_status_request(self):
        """Handle status request from cloud"""
        await self.send_status_update()
    
    async def handle_connection_change(self, connected: bool):
        """Handle cloud connection status change"""
        self.connection_status = "connected" if connected else "disconnected"
        await self.ui_manager.update_connection_status(self.connection_status)
        
        if connected:
            self.logger.info("Cloud connection restored")
            await self.send_status_update()
        else:
            self.logger.warning("Cloud connection lost")
    
    async def send_status_update(self):
        """Send comprehensive status update to cloud"""
        try:
            status = {
                'runner_version': '1.0.0',
                'connection_status': self.connection_status,
                'broker_status': self.broker_status,
                'is_paused': self.is_paused,
                'current_job': self.current_job['id'] if self.current_job else None,
                'system_info': {
                    'platform': sys.platform,
                    'python_version': sys.version,
                    'memory_usage': self.get_memory_usage(),
                },
                'timestamp': datetime.now().isoformat()
            }
            
            if self.ws_client:
                await self.ws_client.send_status(status)
                
        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'cpu_percent': process.cpu_percent()
            }
        except ImportError:
            return {'rss_mb': 0, 'vms_mb': 0, 'cpu_percent': 0}
    
    async def main_loop(self):
        """Main application event loop"""
        self.logger.info("Starting main event loop")
        
        while self.is_running:
            try:
                # Periodic heartbeat
                if self.ws_client and self.connection_status == "connected":
                    await self.ws_client.send_heartbeat()
                
                # Update UI with latest logs
                recent_logs = await self.data_manager.get_recent_logs(10)
                await self.ui_manager.update_logs(recent_logs)
                
                # Sleep for 5 seconds
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)  # Longer sleep on error
    
    async def pause(self):
        """Pause the runner"""
        self.is_paused = True
        self.logger.info("Runner paused")
        await self.ui_manager.update_pause_status(True)
        await self.send_status_update()
    
    async def resume(self):
        """Resume the runner"""
        self.is_paused = False
        self.logger.info("Runner resumed")
        await self.ui_manager.update_pause_status(False)
        await self.send_status_update()
    
    async def restart(self):
        """Restart the runner"""
        self.logger.info("Restarting runner...")
        await self.shutdown()
        # Note: In production, this would restart the process
        await self.start()
    
    async def shutdown(self):
        """Graceful shutdown of the runner"""
        self.logger.info("Shutting down Oriphim Runner...")
        
        self.is_running = False
        
        # Close WebSocket connection
        if self.ws_client:
            await self.ws_client.disconnect()
        
        # Disconnect broker
        if self.ibkr_manager:
            await self.ibkr_manager.disconnect()
        
        # Close UI
        if self.ui_manager:
            await self.ui_manager.shutdown()
        
        self.logger.info("Oriphim Runner shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal, closing gracefully...")
    # This would trigger shutdown in the main loop
    sys.exit(0)


async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        runner = OriphimRunner()
        await runner.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    if sys.platform == "win32":
        # Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())