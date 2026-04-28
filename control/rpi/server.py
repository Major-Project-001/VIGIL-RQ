"""
server.py — Main entry point for the VIGIL-RQ remote control server.

Orchestrates all components:
    1. SPI driver     → sends servo commands to FPGA
    2. Gait engine    → converts high-level commands to joint angles
    3. IMU reader     → body orientation sensing
    4. Power monitor  → battery voltage/current monitoring
    5. Alert manager  → buzzer + RGB LED status feedback
    6. WebSocket      → bidirectional communication with mobile app
    7. HTTP server    → serves the mobile web app static files

Run on the Raspberry Pi 4B:
    python server.py

The RPi should be configured as a WiFi AP (SSID: VIGIL-RQ) before running.
See docs/wifi_ap_setup.md for hostapd/dnsmasq configuration.
"""

import asyncio
import signal
import time
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

from config import (
    TELEMETRY_RATE_HZ, GAIT_UPDATE_RATE_HZ,
    WEB_APP_PORT, WEB_APP_DIR,
)
from spi_driver import SpiServoDriver
from gait_engine import GaitEngine
from imu_reader import ImuReader
from power_monitor import PowerMonitor
from alert_manager import AlertManager, STATE_NORMAL, STATE_IDLE, STATE_WARNING, STATE_CRITICAL, STATE_DISCONNECTED, STATE_ESTOP
from websocket_handler import WebSocketHandler


class VIGILServer:
    """
    Main server orchestrating all VIGIL-RQ control subsystems.
    """

    def __init__(self):
        print("=" * 55)
        print("  VIGIL-RQ — Quadruped Remote Control Server")
        print("=" * 55)
        print()

        # ── Initialise subsystems ──
        print("[INIT] Starting subsystems...")

        self.spi = SpiServoDriver()
        self.gait = GaitEngine()
        self.imu = ImuReader()
        self.power = PowerMonitor()
        self.alerts = AlertManager()

        # WebSocket with command callbacks
        self.ws = WebSocketHandler(
            on_command=self._handle_command,
            on_joystick=self._handle_joystick,
            on_estop=self._handle_estop,
            on_connect=lambda: self.alerts.beep_connect(),
        )

        # State
        self._running = True
        self._estop_active = False
        self._watchdog_triggered = False

        print("[INIT] All subsystems ready")
        print()

    def _handle_command(self, action: str, speed: float, direction: float):
        """Handle a gait command from the mobile app."""
        if self._estop_active and action != "stop":
            return  # Ignore commands during E-STOP

        print(f"[CMD] {action} (speed={speed:.1f}, dir={direction:.1f})")

        if action == "stop":
            self._estop_active = False

        self.gait.set_mode(action, speed=speed, direction=direction)
        self._watchdog_triggered = False  # Reset watchdog on any command

        # Update LED state
        if action in ("walk", "run"):
            self.alerts.set_normal()
        else:
            self.alerts.set_idle()

    def _handle_joystick(self, x: float, y: float):
        """Handle joystick input from the mobile app."""
        if self._estop_active:
            return
        self.gait.update_joystick(x, y)
        self._watchdog_triggered = False  # Reset watchdog on joystick input

    def _handle_estop(self):
        """Handle emergency stop."""
        print("[!!!] EMERGENCY STOP activated")
        self._estop_active = True
        angles = self.gait.emergency_stop()
        self.spi.set_joint_angles(angles)
        self.alerts.set_estop()

    async def _control_loop(self):
        """
        Main control loop: runs at GAIT_UPDATE_RATE_HZ.

        1. Tick gait engine → get joint angles
        2. Send angles to FPGA via SPI
        3. Check watchdog timeout
        """
        dt = 1.0 / GAIT_UPDATE_RATE_HZ
        print(f"[LOOP] Control loop running at {GAIT_UPDATE_RATE_HZ} Hz")

        while self._running:
            loop_start = time.time()

            if not self._estop_active:
                # Watchdog check (fire only once)
                if self.ws.watchdog_expired and self.ws.is_connected and not self._watchdog_triggered:
                    print("[WATCHDOG] No commands for 10s — auto-rest")
                    self.gait.set_mode("rest")
                    self.alerts.set_disconnected()
                    self._watchdog_triggered = True

                # Connection status
                if not self.ws.is_connected:
                    self.alerts.set_disconnected()

                # Tick gait engine
                angles = self.gait.tick(dt)

                # Send to FPGA
                self.spi.set_joint_angles(angles)

            # Sleep to maintain target rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, dt - elapsed)
            await asyncio.sleep(sleep_time)

    async def _telemetry_loop(self):
        """
        Telemetry broadcast loop: runs at TELEMETRY_RATE_HZ.

        Reads sensors and broadcasts state to all WebSocket clients.
        """
        dt = 1.0 / TELEMETRY_RATE_HZ
        print(f"[LOOP] Telemetry loop running at {TELEMETRY_RATE_HZ} Hz")

        while self._running:
            loop_start = time.time()

            # Read sensors
            imu_data = self.imu.read()
            power_data = self.power.read()

            # Check power alerts
            power_alert = power_data.get("alert", "none")
            if power_alert == "critical_battery":
                if not self._estop_active:
                    print("[POWER] Critical battery! Auto-rest + servo disable")
                    self.gait.set_mode("rest")
                    self.alerts.set_critical()
            elif power_alert == "low_battery":
                self.alerts.set_warning()

            # Build telemetry message
            telemetry = {
                "type": "telemetry",
                "battery_v": power_data["voltage"],
                "battery_a": power_data["current"],
                "battery_pct": power_data["percent"],
                "imu": imu_data,
                "gait": self.gait.mode,
                "servos_active": not self._estop_active,
                "alert": self.alerts.state,
                "clients": self.ws.client_count,
            }

            # Broadcast to all WebSocket clients
            await self.ws.broadcast(telemetry)

            # Sleep to maintain target rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, dt - elapsed)
            await asyncio.sleep(sleep_time)

    def _start_http_server(self):
        """Start a simple HTTP server to serve the mobile web app."""
        app_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), WEB_APP_DIR)
        )

        if not os.path.isdir(app_dir):
            print(f"[HTTP] Warning: Web app directory not found: {app_dir}")
            return

        class QuietHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=app_dir, **kwargs)

            def log_message(self, format, *args):
                pass  # Suppress access logs

        try:
            httpd = HTTPServer(("0.0.0.0", WEB_APP_PORT), QuietHandler)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            print(f"[HTTP] Serving web app from {app_dir} on port {WEB_APP_PORT}")
        except PermissionError:
            # Port 80 requires root/sudo
            print(f"[HTTP] Cannot bind port {WEB_APP_PORT} (try running with sudo)")
            # Fall back to port 8080
            try:
                httpd = HTTPServer(("0.0.0.0", 8080), QuietHandler)
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                print(f"[HTTP] Serving web app on fallback port 8080")
            except Exception as e:
                print(f"[HTTP] Failed to start: {e}")

    async def run(self):
        """
        Start all loops and run until interrupted.
        """
        # Start HTTP server (serves the web app)
        self._start_http_server()

        # Start WebSocket server
        await self.ws.start()

        # Set initial state
        self.alerts.set_disconnected()

        print()
        print("=" * 55)
        print("  Server running. Connect your phone to VIGIL-RQ WiFi")
        print(f"  Open http://192.168.4.1:{WEB_APP_PORT} in your browser")
        print("  Press Ctrl+C to stop")
        print("=" * 55)
        print()

        # Run control and telemetry loops concurrently
        try:
            await asyncio.gather(
                self._control_loop(),
                self._telemetry_loop(),
            )
        except asyncio.CancelledError:
            pass

    def shutdown(self):
        """Graceful shutdown: neutral servos, LEDs off, close connections."""
        print()
        print("[SHUTDOWN] Shutting down...")
        self._running = False

        # Set all servos to neutral
        self.spi.set_all_neutral()
        print("[SHUTDOWN] Servos set to neutral")

        # Close subsystems
        self.alerts.shutdown()
        self.spi.close()
        self.imu.close()
        self.power.close()
        print("[SHUTDOWN] All subsystems stopped")


def main():
    server = VIGILServer()

    # Handle Ctrl+C gracefully
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def signal_handler(sig, frame):
        server.shutdown()
        loop.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run_until_complete(server.run())
    except KeyboardInterrupt:
        server.shutdown()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
