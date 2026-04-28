"""
alert_manager.py — Buzzer + RGB LED alert system for VIGIL-RQ.

Controls a buzzer and RGB LED on GPIO pins to provide audio/visual
status feedback on the robot body. Patterns run in a background thread.

Status states:
    normal      → Green LED solid, no buzzer
    idle        → Blue LED breathing
    warning     → Yellow LED blink + double beep
    critical    → Red LED fast blink + alarm buzzer
    disconnected → Purple LED pulse
    estop       → Red LED solid + continuous buzzer

Usage:
    from alert_manager import AlertManager
    alerts = AlertManager()
    alerts.set_normal()
    alerts.set_warning()
    alerts.shutdown()
"""

import time
import threading
from config import BUZZER_PIN, RGB_RED_PIN, RGB_GREEN_PIN, RGB_BLUE_PIN

# Try to import RPi.GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[ALERT] RPi.GPIO not available — running in simulation mode")


# ── Alert states ──
STATE_NORMAL = "normal"
STATE_IDLE = "idle"
STATE_WARNING = "warning"
STATE_CRITICAL = "critical"
STATE_DISCONNECTED = "disconnected"
STATE_ESTOP = "estop"


class AlertManager:
    """
    Manages buzzer and RGB LED patterns on GPIO pins.

    Runs pattern updates in a background thread so they don't
    block the main control loop.
    """

    def __init__(self):
        self._state = STATE_IDLE
        self._running = True
        self._lock = threading.Lock()

        # GPIO PWM objects
        self._pwm_red = None
        self._pwm_green = None
        self._pwm_blue = None
        self._pwm_buzzer = None

        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # RGB LED pins (output, PWM at 1 kHz)
            GPIO.setup(RGB_RED_PIN, GPIO.OUT)
            GPIO.setup(RGB_GREEN_PIN, GPIO.OUT)
            GPIO.setup(RGB_BLUE_PIN, GPIO.OUT)
            self._pwm_red = GPIO.PWM(RGB_RED_PIN, 1000)
            self._pwm_green = GPIO.PWM(RGB_GREEN_PIN, 1000)
            self._pwm_blue = GPIO.PWM(RGB_BLUE_PIN, 1000)
            self._pwm_red.start(0)
            self._pwm_green.start(0)
            self._pwm_blue.start(0)

            # Buzzer pin (PWM for tone control)
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            self._pwm_buzzer = GPIO.PWM(BUZZER_PIN, 2000)  # 2 kHz tone
            self._pwm_buzzer.start(0)  # Off initially

            print("[ALERT] GPIO initialised")
        else:
            print("[ALERT] Running in simulation mode")

        # Start background pattern thread
        self._thread = threading.Thread(target=self._pattern_loop, daemon=True)
        self._thread.start()

    @property
    def state(self) -> str:
        """Current alert state."""
        with self._lock:
            return self._state

    def set_normal(self):
        """Green solid — normal operation."""
        with self._lock:
            self._state = STATE_NORMAL

    def set_idle(self):
        """Blue breathing — connected, idle."""
        with self._lock:
            self._state = STATE_IDLE

    def set_warning(self):
        """Yellow blink + double beep — low battery."""
        with self._lock:
            self._state = STATE_WARNING

    def set_critical(self):
        """Red fast blink + alarm — critical battery or overcurrent."""
        with self._lock:
            self._state = STATE_CRITICAL

    def set_disconnected(self):
        """Purple pulse — no client connected."""
        with self._lock:
            self._state = STATE_DISCONNECTED

    def set_estop(self):
        """Red solid + continuous buzzer — emergency stop."""
        with self._lock:
            self._state = STATE_ESTOP

    def beep_connect(self):
        """Play a short double-beep to signal client connected."""
        if not GPIO_AVAILABLE:
            return
        def _beep():
            self._set_buzzer(30)
            time.sleep(0.08)
            self._set_buzzer(0)
            time.sleep(0.06)
            self._set_buzzer(30)
            time.sleep(0.08)
            self._set_buzzer(0)
        threading.Thread(target=_beep, daemon=True).start()

    def _set_rgb(self, r: float, g: float, b: float):
        """Set RGB LED colour (0.0–100.0 for each channel).
        
        Inverted for common-anode LED: 100% duty = OFF, 0% duty = full ON.
        """
        if not GPIO_AVAILABLE:
            return
        self._pwm_red.ChangeDutyCycle(100 - r)
        self._pwm_green.ChangeDutyCycle(100 - g)
        self._pwm_blue.ChangeDutyCycle(100 - b)

    def _set_buzzer(self, duty: float):
        """Set buzzer duty cycle (0 = off, 50 = full volume)."""
        if not GPIO_AVAILABLE:
            return
        self._pwm_buzzer.ChangeDutyCycle(duty)

    def _pattern_loop(self):
        """Background thread: run LED/buzzer patterns continuously."""
        cycle = 0
        while self._running:
            with self._lock:
                state = self._state

            if state == STATE_NORMAL:
                # Green solid
                self._set_rgb(0, 80, 0)
                self._set_buzzer(0)
                time.sleep(0.1)

            elif state == STATE_IDLE:
                # Blue breathing (sine wave brightness)
                import math
                brightness = 40 + 40 * math.sin(cycle * 0.05)
                self._set_rgb(0, 0, brightness)
                self._set_buzzer(0)
                time.sleep(0.03)

            elif state == STATE_WARNING:
                # Yellow blink + double beep every 2 seconds
                phase = cycle % 100
                if phase < 15:
                    self._set_rgb(80, 60, 0)  # Yellow on
                elif phase < 30:
                    self._set_rgb(0, 0, 0)    # Off
                elif phase < 45:
                    self._set_rgb(80, 60, 0)  # Yellow on
                else:
                    self._set_rgb(0, 0, 0)    # Off

                # Double beep
                if phase == 0 or phase == 15:
                    self._set_buzzer(30)
                elif phase == 5 or phase == 20:
                    self._set_buzzer(0)

                time.sleep(0.02)

            elif state == STATE_CRITICAL:
                # Red fast blink + alarm
                if cycle % 10 < 5:
                    self._set_rgb(100, 0, 0)
                    self._set_buzzer(40)
                else:
                    self._set_rgb(0, 0, 0)
                    self._set_buzzer(0)
                time.sleep(0.05)

            elif state == STATE_DISCONNECTED:
                # Purple pulse
                import math
                brightness = 30 + 30 * math.sin(cycle * 0.08)
                self._set_rgb(brightness, 0, brightness)
                self._set_buzzer(0)
                time.sleep(0.03)

            elif state == STATE_ESTOP:
                # Red solid + continuous buzzer
                self._set_rgb(100, 0, 0)
                self._set_buzzer(50)
                time.sleep(0.1)

            else:
                # Unknown state: all off
                self._set_rgb(0, 0, 0)
                self._set_buzzer(0)
                time.sleep(0.1)

            cycle += 1

    def shutdown(self):
        """Stop all outputs and clean up GPIO."""
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._set_rgb(0, 0, 0)
        self._set_buzzer(0)

        if GPIO_AVAILABLE:
            self._pwm_red.stop()
            self._pwm_green.stop()
            self._pwm_blue.stop()
            self._pwm_buzzer.stop()
            GPIO.cleanup()
            print("[ALERT] GPIO cleaned up")
