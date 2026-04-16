"""
calib_server.py — Minimal servo calibration server for VIGIL-RQ.

Serves a web UI on port 8080 and accepts WebSocket commands on port 8765
to control individual servos via the FPGA PWM controller over SPI.

Usage (on Raspberry Pi):
    cd control/calibration
    sudo python calib_server.py

Usage (PC simulation — no SPI hardware):
    python calib_server.py
"""

import asyncio
import json
import os
import sys
import signal
import http.server
import threading
from pathlib import Path

# ── Import SPI driver & config from ../rpi/ ──
RPI_DIR = str(Path(__file__).resolve().parent.parent / "rpi")
sys.path.insert(0, RPI_DIR)

from spi_driver import SpiServoDriver
from config import (
    SERVO_CHANNELS, CHANNEL_NAMES,
    SERVO_PULSE_MIN_US, SERVO_PULSE_MAX_US, SERVO_PULSE_NEUTRAL_US,
)

# Try websockets import
try:
    import websockets
except ImportError:
    print("ERROR: 'websockets' not installed. Run: pip install websockets")
    sys.exit(1)

# ── Constants ──
HTTP_PORT = 8080
WS_PORT = 8765
STATIC_DIR = Path(__file__).resolve().parent

# ── Global state ──
driver = None
connected_clients = set()
servo_positions = {ch: SERVO_PULSE_NEUTRAL_US for ch in range(12)}


def start_http_server():
    """Serve static files (HTML/CSS/JS) on HTTP_PORT."""

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

        def log_message(self, format, *args):
            pass  # Suppress access logs

    httpd = http.server.HTTPServer(("0.0.0.0", HTTP_PORT), QuietHandler)
    print(f"[HTTP] Serving calibration UI on http://0.0.0.0:{HTTP_PORT}")
    httpd.serve_forever()


async def handle_client(websocket):
    """Handle a single WebSocket client connection."""
    client_addr = websocket.remote_address
    connected_clients.add(websocket)
    print(f"[WS] Client connected: {client_addr}")

    # Send current state
    state = {
        "type": "state",
        "channels": CHANNEL_NAMES,
        "positions": servo_positions,
        "pulse_min": SERVO_PULSE_MIN_US,
        "pulse_max": SERVO_PULSE_MAX_US,
        "pulse_neutral": SERVO_PULSE_NEUTRAL_US,
    }
    await websocket.send(json.dumps(state))

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                cmd = data.get("cmd")

                if cmd == "servo":
                    ch = int(data["ch"])
                    us = int(data["us"])
                    us = max(SERVO_PULSE_MIN_US, min(SERVO_PULSE_MAX_US, us))
                    servo_positions[ch] = us
                    driver.set_servo(ch, us)

                elif cmd == "center":
                    ch = int(data.get("ch", 0))
                    servo_positions[ch] = SERVO_PULSE_NEUTRAL_US
                    driver.set_servo(ch, SERVO_PULSE_NEUTRAL_US)
                    await websocket.send(json.dumps({
                        "type": "centered",
                        "ch": ch,
                        "us": SERVO_PULSE_NEUTRAL_US,
                    }))

                elif cmd == "center_all":
                    for ch in range(12):
                        servo_positions[ch] = SERVO_PULSE_NEUTRAL_US
                        driver.set_servo(ch, SERVO_PULSE_NEUTRAL_US)
                    await websocket.send(json.dumps({
                        "type": "centered_all",
                        "us": SERVO_PULSE_NEUTRAL_US,
                    }))

                elif cmd == "save_offsets":
                    offsets = {}
                    for ch in range(12):
                        name = CHANNEL_NAMES.get(ch, f"ch_{ch}")
                        offsets[name] = servo_positions[ch] - SERVO_PULSE_NEUTRAL_US
                    
                    offsets_path = STATIC_DIR / "servo_offsets.json"
                    with open(offsets_path, "w") as f:
                        json.dump(offsets, f, indent=2)
                    
                    print(f"[CALIB] Offsets saved to {offsets_path}")
                    await websocket.send(json.dumps({
                        "type": "offsets_saved",
                        "offsets": offsets,
                        "path": str(offsets_path),
                    }))

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[WS] Bad message: {e}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Client disconnected: {client_addr}")


async def main():
    global driver

    print("=" * 60)
    print("  🎯 VIGIL-RQ Servo Calibration Tool")
    print("=" * 60)

    # Init SPI servo driver
    driver = SpiServoDriver()
    driver.set_all_neutral()
    print("[CALIB] All servos set to neutral (1500 µs)")

    # Start HTTP server in background thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    # Start WebSocket server
    print(f"[WS] WebSocket server on ws://0.0.0.0:{WS_PORT}")
    print()
    print("  Open in browser:  http://<rpi-ip>:8080")
    print("  Or on same machine: http://localhost:8080")
    print("  Press Ctrl+C to stop.")
    print()

    server = await websockets.serve(handle_client, "0.0.0.0", WS_PORT)

    # Wait until Ctrl+C
    stop = asyncio.get_event_loop().create_future()

    def _stop():
        if not stop.done():
            stop.set_result(None)

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            pass  # Windows

    try:
        await stop
    except asyncio.CancelledError:
        pass

    # Graceful shutdown
    print("\n[CALIB] Shutting down...")
    server.close()
    await server.wait_closed()

    print("[CALIB] Centering all servos...")
    driver.set_all_neutral()
    driver.close()
    print("[CALIB] Done. Bye!")


def cleanup():
    """Emergency cleanup if asyncio didn't finish."""
    global driver
    if driver:
        try:
            driver.set_all_neutral()
            driver.close()
        except Exception:
            pass
        driver = None


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[CALIB] Force quit — cleaning up...")
        cleanup()
        print("[CALIB] Done.")
    finally:
        sys.exit(0)

