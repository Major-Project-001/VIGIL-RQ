"""
websocket_handler.py — WebSocket server for VIGIL-RQ mobile app communication.

Handles bidirectional communication between the mobile web app and the
robot controller. Receives commands (walk, sit, stand, etc.) and broadcasts
telemetry (battery, IMU, gait state) to all connected clients.

Protocol:
    App → RPi:
        {"type": "command", "action": "walk|run|sit|stand|rest|stop", "speed": 1.0, "direction": 0.0}
        {"type": "joystick", "x": 0.3, "y": 0.8}
        {"type": "estop"}
        {"type": "ping"}

    RPi → App:
        {"type": "telemetry", ...}
        {"type": "pong"}
"""

import json
import asyncio
import time
from config import WEBSOCKET_HOST, WEBSOCKET_PORT, WATCHDOG_TIMEOUT_S

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False
    print("[WS] websockets module not available")


class WebSocketHandler:
    """
    Async WebSocket server for the VIGIL-RQ control protocol.

    Accepts multiple clients, routes commands to callbacks, and
    broadcasts telemetry to all connected clients.
    """

    def __init__(self, on_command=None, on_joystick=None, on_estop=None, on_connect=None):
        """
        Args:
            on_command:  Callback(action: str, speed: float, direction: float)
            on_joystick: Callback(x: float, y: float)
            on_estop:    Callback()
            on_connect:  Callback() — called when a client connects
        """
        self._on_command = on_command
        self._on_joystick = on_joystick
        self._on_estop = on_estop
        self._on_connect = on_connect
        self._clients = set()
        self._server = None
        self._last_message_time = time.time()

    @property
    def last_message_time(self) -> float:
        """Timestamp of the last received message (for watchdog)."""
        return self._last_message_time

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._clients)

    @property
    def is_connected(self) -> bool:
        """Whether any client is currently connected."""
        return len(self._clients) > 0

    @property
    def watchdog_expired(self) -> bool:
        """Whether the watchdog timeout has elapsed since last message."""
        return (time.time() - self._last_message_time) > WATCHDOG_TIMEOUT_S

    async def start(self):
        """Start the WebSocket server."""
        if not WS_AVAILABLE:
            print("[WS] Cannot start — websockets module not available")
            return

        self._server = await websockets.serve(
            self._handle_client,
            WEBSOCKET_HOST,
            WEBSOCKET_PORT,
            ping_interval=5,
            ping_timeout=10,
        )
        print(f"[WS] Server listening on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")

    async def stop(self):
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            print("[WS] Server stopped")

    async def broadcast(self, data: dict):
        """Send a JSON message to all connected clients."""
        if not self._clients:
            return

        message = json.dumps(data)
        # Send to all clients, remove any that fail
        disconnected = set()
        for ws in self._clients:
            try:
                await ws.send(message)
            except Exception:
                disconnected.add(ws)

        self._clients -= disconnected

    async def _handle_client(self, websocket, path=None):
        """Handle a single WebSocket client connection."""
        self._clients.add(websocket)
        remote = websocket.remote_address
        print(f"[WS] Client connected: {remote} (total: {len(self._clients)})")
        if self._on_connect:
            self._on_connect()

        try:
            async for message in websocket:
                self._last_message_time = time.time()
                await self._process_message(message)
        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            print(f"[WS] Error from {remote}: {e}")
        finally:
            self._clients.discard(websocket)
            print(f"[WS] Client disconnected: {remote} (total: {len(self._clients)})")

    async def _process_message(self, raw: str):
        """Parse and route an incoming JSON message."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type", "")

        if msg_type == "command":
            action = msg.get("action", "stand")
            speed = float(msg.get("speed", 1.0))
            direction = float(msg.get("direction", 0.0))
            if self._on_command:
                self._on_command(action, speed, direction)

        elif msg_type == "joystick":
            x = float(msg.get("x", 0.0))
            y = float(msg.get("y", 0.0))
            if self._on_joystick:
                self._on_joystick(x, y)

        elif msg_type == "estop":
            if self._on_estop:
                self._on_estop()

        elif msg_type == "ping":
            # Respond with pong (latency measurement)
            for ws in self._clients:
                try:
                    await ws.send(json.dumps({"type": "pong", "time": time.time()}))
                except Exception:
                    pass
