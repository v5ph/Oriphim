"""
Oriphim Runner - Cloud WebSocket Client

Manages secure WebSocket connection to Supabase Realtime channels.
Handles authentication, job reception, status updates, and heartbeats.
"""

import asyncio
import json
import logging
import websockets
import ssl
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import uuid

logger = logging.getLogger('oriphim_runner.websocket')


class CloudWebSocketClient:
    """
    WebSocket client for Oriphim Cloud communication
    
    Features:
    - Secure authentication via API key
    - Job reception and status reporting
    - Real-time log streaming
    - Automatic reconnection
    - Heartbeat management
    """
    
    def __init__(self, api_key: str, 
                 on_job_received: Callable = None,
                 on_status_request: Callable = None,
                 on_connection_change: Callable = None):
        self.api_key = api_key
        self.on_job_received = on_job_received
        self.on_status_request = on_status_request  
        self.on_connection_change = on_connection_change
        
        # Connection settings
        self.ws_url = "wss://your-supabase-project.supabase.co/realtime/v1/websocket"
        self.channel_topic = f"runner:{self.get_device_id()}"
        
        # Connection state
        self.websocket = None
        self.is_connected = False
        self.is_authenticated = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # Message handling
        self.pending_messages = []
        self.message_callbacks = {}
        
        logger.info(f"WebSocket client initialized for channel: {self.channel_topic}")
    
    def get_device_id(self) -> str:
        """Get unique device identifier"""
        import platform
        import hashlib
        
        # Create device ID from hostname + API key hash
        hostname = platform.node()
        api_hash = hashlib.sha256(self.api_key.encode()).hexdigest()[:8]
        return f"{hostname}_{api_hash}"
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to Oriphim Cloud"""
        try:
            logger.info("Connecting to Oriphim Cloud...")
            
            # Create SSL context for secure connection
            ssl_context = ssl.create_default_context()
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                self.ws_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            
            self.is_connected = True
            logger.info("WebSocket connected")
            
            # Start message handling
            asyncio.create_task(self.message_handler())
            
            # Authenticate
            await self.authenticate()
            
            # Subscribe to runner channel
            await self.subscribe_to_channel()
            
            if self.on_connection_change:
                await self.on_connection_change(True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to cloud: {e}")
            self.is_connected = False
            
            if self.on_connection_change:
                await self.on_connection_change(False)
            
            return False
    
    async def authenticate(self):
        """Authenticate with API key"""
        try:
            auth_message = {
                "topic": "phoenix",
                "event": "phx_join",
                "payload": {
                    "api_key": self.api_key,
                    "device_id": self.get_device_id(),
                    "runner_version": "1.0.0"
                },
                "ref": str(uuid.uuid4())
            }
            
            await self.send_raw_message(auth_message)
            
            # Wait for auth response (simplified - in production would wait for actual response)
            await asyncio.sleep(1)
            self.is_authenticated = True
            logger.info("Authentication successful")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def subscribe_to_channel(self):
        """Subscribe to runner-specific channel"""
        try:
            subscribe_message = {
                "topic": self.channel_topic,
                "event": "phx_join",
                "payload": {},
                "ref": str(uuid.uuid4())
            }
            
            await self.send_raw_message(subscribe_message)
            logger.info(f"Subscribed to channel: {self.channel_topic}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to channel: {e}")
            raise
    
    async def message_handler(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                await self.process_message(json.loads(message))
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
            await self.handle_disconnection()
            
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            await self.handle_disconnection()
    
    async def process_message(self, message: Dict[str, Any]):
        """Process incoming message from cloud"""
        try:
            event = message.get('event')
            payload = message.get('payload', {})
            topic = message.get('topic')
            
            logger.debug(f"Received message: {event} on {topic}")
            
            if event == "new_job":
                # New trading job received
                if self.on_job_received:
                    await self.on_job_received(payload)
            
            elif event == "status_request":
                # Cloud requesting status update
                if self.on_status_request:
                    await self.on_status_request()
            
            elif event == "pause_runner":
                # Cloud requesting pause
                logger.info("Pause request received from cloud")
                # This would be handled by main app
            
            elif event == "resume_runner":
                # Cloud requesting resume
                logger.info("Resume request received from cloud")
                # This would be handled by main app
            
            elif event == "heartbeat_response":
                # Heartbeat acknowledgment
                logger.debug("Heartbeat acknowledged")
            
            else:
                logger.debug(f"Unhandled message event: {event}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def send_raw_message(self, message: Dict[str, Any]):
        """Send raw message to WebSocket"""
        if not self.websocket or not self.is_connected:
            logger.warning("Cannot send message - not connected")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_job_status(self, job_id: str, status: str, message: str = ""):
        """Send job execution status to cloud"""
        message_data = {
            "topic": self.channel_topic,
            "event": "job_status",
            "payload": {
                "job_id": job_id,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            },
            "ref": str(uuid.uuid4())
        }
        
        await self.send_raw_message(message_data)
        logger.info(f"Sent job status: {job_id} -> {status}")
    
    async def send_job_results(self, job_id: str, results: Dict[str, Any]):
        """Send job execution results to cloud"""
        message_data = {
            "topic": self.channel_topic,
            "event": "job_results",
            "payload": {
                "job_id": job_id,
                "results": results,
                "timestamp": datetime.now().isoformat()
            },
            "ref": str(uuid.uuid4())
        }
        
        await self.send_raw_message(message_data)
        logger.info(f"Sent job results: {job_id}")
    
    async def send_status(self, status: Dict[str, Any]):
        """Send runner status update to cloud"""
        message_data = {
            "topic": self.channel_topic,
            "event": "runner_status",
            "payload": status,
            "ref": str(uuid.uuid4())
        }
        
        await self.send_raw_message(message_data)
        logger.debug("Sent status update")
    
    async def send_heartbeat(self):
        """Send heartbeat to maintain connection"""
        message_data = {
            "topic": "phoenix",
            "event": "heartbeat",
            "payload": {},
            "ref": str(uuid.uuid4())
        }
        
        await self.send_raw_message(message_data)
    
    async def send_log_stream(self, log_entries: list):
        """Stream log entries to cloud dashboard"""
        message_data = {
            "topic": self.channel_topic,
            "event": "log_stream",
            "payload": {
                "logs": log_entries,
                "timestamp": datetime.now().isoformat()
            },
            "ref": str(uuid.uuid4())
        }
        
        await self.send_raw_message(message_data)
    
    async def handle_disconnection(self):
        """Handle WebSocket disconnection"""
        self.is_connected = False
        self.is_authenticated = False
        
        if self.on_connection_change:
            await self.on_connection_change(False)
        
        # Attempt reconnection
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            await asyncio.sleep(min(self.reconnect_attempts * 2, 30))  # Exponential backoff
            await self.connect()
        else:
            logger.error("Max reconnection attempts reached")
    
    async def disconnect(self):
        """Gracefully disconnect from cloud"""
        logger.info("Disconnecting from cloud...")
        
        self.is_connected = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
        
        logger.info("Cloud disconnection complete")


# For testing/development - simulate cloud connection
class MockCloudWebSocketClient(CloudWebSocketClient):
    """Mock WebSocket client for testing without cloud connection"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_jobs = []
    
    async def connect(self) -> bool:
        """Simulate connection"""
        logger.info("Mock cloud connection established")
        self.is_connected = True
        self.is_authenticated = True
        
        if self.on_connection_change:
            await self.on_connection_change(True)
        
        # Simulate periodic status requests
        asyncio.create_task(self.mock_status_requests())
        
        return True
    
    async def mock_status_requests(self):
        """Simulate periodic status requests from cloud"""
        while self.is_connected:
            await asyncio.sleep(30)  # Every 30 seconds
            if self.on_status_request:
                await self.on_status_request()
    
    async def send_raw_message(self, message: Dict[str, Any]):
        """Mock message sending"""
        logger.debug(f"Mock send: {message.get('event')}")
        return True
    
    def add_mock_job(self, job: Dict[str, Any]):
        """Add mock job for testing"""
        self.mock_jobs.append(job)
        
        async def send_job():
            await asyncio.sleep(5)  # Delay
            if self.on_job_received:
                await self.on_job_received(job)
        
        asyncio.create_task(send_job())