#!/usr/bin/env python3
"""
Oriphim Runner - Desktop agent for executing trading bots locally

The Runner connects to Oriphim Cloud for job coordination while keeping
all broker credentials and trading data on the user's local machine.
"""

import os
import sys
import json
import asyncio
import logging
import signal
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Third-party imports
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

# Add ibkr_bots to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ibkr_bots'))
from bots.bot_interface import run_bot

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OriphimRunner')


@dataclass
class RunnerConfig:
    """Runner configuration"""
    api_key: str
    supabase_url: str
    supabase_anon_key: str
    cloud_endpoint: str = "https://your-project.supabase.co/functions/v1"


class OriphimRunner:
    """Main Runner application"""
    
    def __init__(self, config: RunnerConfig):
        self.config = config
        self.authenticated = False
        self.user_info = None
        self.supabase: Optional[Client] = None
        self.jwt_token = None
        self.running = False
        self.current_runs = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def start(self):
        """Start the Runner"""
        logger.info("🚀 Starting Oriphim Runner...")
        
        try:
            # Authenticate with Oriphim Cloud
            if not await self._authenticate():
                logger.error("❌ Authentication failed")
                return
            
            logger.info(f"✅ Authenticated as {self.user_info.get('email')}")
            logger.info(f"📊 Plan: {self.user_info.get('plan_tier', 'free')}")
            
            # Initialize Supabase client with JWT
            await self._init_supabase()
            
            # Start listening for jobs
            self.running = True
            await self._listen_for_jobs()
            
        except Exception as e:
            logger.error(f"❌ Runner startup failed: {e}")
        finally:
            await self._cleanup()
    
    async def _authenticate(self) -> bool:
        """Authenticate with Oriphim Cloud using API key"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.cloud_endpoint}/exchange-device-token",
                    json={"api_key": self.config.api_key},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.jwt_token = data['token']
                    self.user_info = {
                        'user_id': data['user_id'],
                        'email': data['email'],
                        'plan_tier': data['plan_tier'],
                        'device_name': data['device_name']
                    }
                    self.authenticated = True
                    return True
                else:
                    logger.error(f"Authentication failed: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def _init_supabase(self):
        """Initialize Supabase client with JWT token"""
        try:
            self.supabase = create_client(
                self.config.supabase_url,
                self.config.supabase_anon_key
            )
            
            # Set authorization header
            self.supabase.postgrest.auth(self.jwt_token)
            
        except Exception as e:
            logger.error(f"Supabase initialization failed: {e}")
            raise
    
    async def _listen_for_jobs(self):
        """Listen for job notifications from Oriphim Cloud"""
        logger.info("👂 Listening for job notifications...")
        
        # Subscribe to user's job channel
        channel_name = f"jobs:{self.user_info['user_id']}"
        
        try:
            # For now, simulate listening - in real implementation,
            # you'd use Supabase realtime subscriptions
            while self.running:
                # Check for pending runs in database
                await self._check_pending_runs()
                
                # Heartbeat and status update
                await self._send_heartbeat()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            logger.error(f"Error in job listener: {e}")
    
    async def _check_pending_runs(self):
        """Check for pending runs and start them"""
        try:
            # Query for pending runs
            response = self.supabase.table('runs').select('*').eq(
                'user_id', self.user_info['user_id']
            ).eq('status', 'pending').execute()
            
            pending_runs = response.data
            
            for run_data in pending_runs:
                if run_data['id'] not in self.current_runs:
                    await self._start_bot_run(run_data)
                    
        except Exception as e:
            logger.error(f"Error checking pending runs: {e}")
    
    async def _start_bot_run(self, run_data: Dict[str, Any]):
        """Start a bot run"""
        run_id = run_data['id']
        bot_kind = run_data['metadata']['bot_kind']
        config = run_data['metadata']['config']
        mode = run_data['mode']
        
        logger.info(f"🤖 Starting {bot_kind} bot (Run ID: {run_id})")
        
        try:
            # Update run status to running
            self.supabase.table('runs').update({
                'status': 'running'
            }).eq('id', run_id).execute()
            
            # Start bot execution in background task
            task = asyncio.create_task(
                self._execute_bot(run_id, bot_kind, config, mode)
            )
            self.current_runs[run_id] = {
                'task': task,
                'bot_kind': bot_kind,
                'started_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to start bot run {run_id}: {e}")
            await self._log_to_run(run_id, 'error', f"Failed to start: {e}")
    
    async def _execute_bot(self, run_id: str, bot_kind: str, config: Dict[str, Any], mode: str):
        """Execute bot and stream logs"""
        try:
            await self._log_to_run(run_id, 'info', f"Starting {bot_kind} execution")
            
            # Execute bot and stream messages
            for message_json in run_bot(bot_kind, config, mode):
                message = json.loads(message_json)
                
                # Stream log to Supabase
                await self._log_to_run(
                    run_id, 
                    message['level'], 
                    message['message'],
                    message.get('context', {})
                )
                
                # Check if run should be stopped
                if not self.running or run_id not in self.current_runs:
                    break
            
            # Mark run as completed
            await self._complete_run(run_id, 'completed')
            
        except Exception as e:
            logger.error(f"Bot execution failed for run {run_id}: {e}")
            await self._log_to_run(run_id, 'error', f"Execution failed: {e}")
            await self._complete_run(run_id, 'failed')
        finally:
            # Clean up
            if run_id in self.current_runs:
                del self.current_runs[run_id]
    
    async def _log_to_run(self, run_id: str, level: str, message: str, context: Dict[str, Any] = None):
        """Send log message to Supabase"""
        try:
            self.supabase.table('run_logs').insert({
                'run_id': run_id,
                'level': level,
                'message': message,
                'context': context or {}
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log to run {run_id}: {e}")
    
    async def _complete_run(self, run_id: str, status: str):
        """Mark run as completed"""
        try:
            self.supabase.table('runs').update({
                'status': status,
                'ended_at': datetime.now().isoformat()
            }).eq('id', run_id).execute()
            
            logger.info(f"✅ Run {run_id} completed with status: {status}")
            
        except Exception as e:
            logger.error(f"Failed to complete run {run_id}: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat to indicate Runner is alive"""
        try:
            # Update API key last_used_at as heartbeat
            self.supabase.table('api_keys').update({
                'last_used_at': datetime.now().isoformat()
            }).eq('token', self.config.api_key).execute()
            
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up Runner resources...")
        
        # Stop all running bots
        for run_id, run_info in list(self.current_runs.items()):
            logger.info(f"Stopping run {run_id}")
            run_info['task'].cancel()
            await self._complete_run(run_id, 'stopped')
        
        self.current_runs.clear()
        logger.info("👋 Runner stopped")


async def main():
    """Main entry point"""
    # Load configuration
    api_key = os.getenv('ORIPHIM_API_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not all([api_key, supabase_url, supabase_anon_key]):
        logger.error("❌ Missing required environment variables")
        logger.error("Please set: ORIPHIM_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY")
        return
    
    config = RunnerConfig(
        api_key=api_key,
        supabase_url=supabase_url,
        supabase_anon_key=supabase_anon_key
    )
    
    # Start Runner
    runner = OriphimRunner(config)
    await runner.start()


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════╗
    ║         🔥 Oriphim Runner 🔥          ║
    ║   AI-Powered Options Trading Agent    ║
    ╚═══════════════════════════════════════╝
    """)
    
    asyncio.run(main())