/**
 * app.js — Main application logic for VIGIL-RQ mobile controller.
 *
 * Manages WebSocket connection, command sending, telemetry display,
 * and UI state. Auto-reconnects on disconnect.
 */

// ── Configuration ──
const WS_PORT = 8765;
const WS_RECONNECT_DELAY_MS = 2000;
const JOYSTICK_SEND_RATE_MS = 50;  // Send joystick data at 20 Hz

// ── State ──
let ws = null;
let isConnected = false;
let activeMode = 'stand';
let estopActive = false;
let reconnectTimer = null;
let joystickTimer = null;
let lastJoystickX = 0;
let lastJoystickY = 0;
let lastJoystick2X = 0;
let lastJoystick2Y = 0;

// ── DOM Elements ──
const statusDot = document.getElementById('statusDot');
const connectionLabel = document.getElementById('connectionLabel');
const batteryBadge = document.getElementById('batteryBadge');
const alertBanner = document.getElementById('alertBanner');
const alertIcon = document.getElementById('alertIcon');
const alertText = document.getElementById('alertText');
const btnEstop = document.getElementById('btnEstop');
const speedSlider = document.getElementById('speedSlider');
const speedValue = document.getElementById('speedValue');

const telBatteryV = document.getElementById('telBatteryV');
const telBatteryA = document.getElementById('telBatteryA');
const telRoll = document.getElementById('telRoll');
const telPitch = document.getElementById('telPitch');
const telYaw = document.getElementById('telYaw');
const batteryBar = document.getElementById('batteryBar');

const presetButtons = document.querySelectorAll('.preset-btn');


// ══════════════════════════════════════════════════════════════════════════════
// WebSocket Connection
// ══════════════════════════════════════════════════════════════════════════════

function getWebSocketUrl() {
    // Connect to the same host that served this page
    const host = window.location.hostname || '192.168.4.1';
    return `ws://${host}:${WS_PORT}`;
}

function connect() {
    if (ws && ws.readyState < 2) return; // Already connecting/open

    const url = getWebSocketUrl();
    console.log(`[WS] Connecting to ${url}...`);

    ws = new WebSocket(url);

    ws.onopen = () => {
        console.log('[WS] Connected');
        isConnected = true;
        updateConnectionUI(true);

        // Start joystick send timer
        startJoystickTimer();

        // Request current state
        sendCommand('stand');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleMessage(data);
        } catch (e) {
            console.warn('[WS] Bad message:', e);
        }
    };

    ws.onclose = () => {
        console.log('[WS] Disconnected');
        isConnected = false;
        updateConnectionUI(false);
        stopJoystickTimer();
        scheduleReconnect();
    };

    ws.onerror = (err) => {
        console.error('[WS] Error:', err);
    };
}

function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connect();
    }, WS_RECONNECT_DELAY_MS);
}

function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
    }
}


// ══════════════════════════════════════════════════════════════════════════════
// Command Sending
// ══════════════════════════════════════════════════════════════════════════════

function sendCommand(action) {
    const speed = parseFloat(speedSlider.value) / 100;
    send({
        type: 'command',
        action: action,
        speed: speed,
        direction: 0.0
    });
}

function sendJoystick(x, y, x2, y2) {
    send({
        type: 'joystick',
        x: x,
        y: y,
        x2: x2,
        y2: y2
    });
}

function sendEstop() {
    send({ type: 'estop' });
}


// ══════════════════════════════════════════════════════════════════════════════
// Joystick
// ══════════════════════════════════════════════════════════════════════════════

const joystick = new VirtualJoystick('joystickCanvas', (x, y) => {
    lastJoystickX = x;
    lastJoystickY = y;
});

const joystick2 = new VirtualJoystick('joystickCanvas2', (x, y) => {
    lastJoystick2X = x;
    lastJoystick2Y = y;
});

function startJoystickTimer() {
    if (joystickTimer) return;
    joystickTimer = setInterval(() => {
        // Only send if either joystick is not at center
        if (lastJoystickX !== 0 || lastJoystickY !== 0 || lastJoystick2X !== 0 || lastJoystick2Y !== 0) {
            sendJoystick(lastJoystickX, lastJoystickY, lastJoystick2X, lastJoystick2Y);
        }
    }, JOYSTICK_SEND_RATE_MS);
}

function stopJoystickTimer() {
    if (joystickTimer) {
        clearInterval(joystickTimer);
        joystickTimer = null;
    }
}


// ══════════════════════════════════════════════════════════════════════════════
// Message Handling
// ══════════════════════════════════════════════════════════════════════════════

function handleMessage(data) {
    if (data.type === 'telemetry') {
        updateTelemetry(data);
    } else if (data.type === 'pong') {
        // Latency measurement (future use)
    }
}

function updateTelemetry(data) {
    // Battery
    const voltage = data.battery_v || 0;
    const current = data.battery_a || 0;
    const percent = data.battery_pct || 0;

    telBatteryV.textContent = voltage.toFixed(1);
    telBatteryA.textContent = `${current.toFixed(1)} A`;
    batteryBadge.textContent = `${voltage.toFixed(1)}V`;

    // Battery bar
    batteryBar.style.width = `${percent}%`;
    batteryBar.className = 'battery-bar';
    batteryBadge.className = 'battery-badge';

    if (percent < 15) {
        batteryBar.classList.add('critical');
        batteryBadge.classList.add('critical');
    } else if (percent < 35) {
        batteryBar.classList.add('warning');
        batteryBadge.classList.add('warning');
    }

    // IMU
    if (data.imu) {
        telRoll.textContent = (data.imu.roll || 0).toFixed(1);
        telPitch.textContent = (data.imu.pitch || 0).toFixed(1);
        telYaw.textContent = (data.imu.yaw || 0).toFixed(1);
    }

    // Alert banner
    const alert = data.alert || 'none';
    updateAlertBanner(alert);

    // Update active gait mode button
    if (data.gait) {
        setActivePreset(data.gait);
    }

    // E-STOP state
    if (!data.servos_active) {
        btnEstop.classList.add('active');
        estopActive = true;
    } else {
        btnEstop.classList.remove('active');
        estopActive = false;
    }
}


// ══════════════════════════════════════════════════════════════════════════════
// UI Updates
// ══════════════════════════════════════════════════════════════════════════════

function updateConnectionUI(connected) {
    if (connected) {
        statusDot.classList.add('connected');
        connectionLabel.textContent = 'Connected';
    } else {
        statusDot.classList.remove('connected');
        connectionLabel.textContent = 'Reconnecting...';
    }
}

function setActivePreset(mode) {
    activeMode = mode;
    presetButtons.forEach(btn => {
        if (btn.dataset.action === mode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function updateAlertBanner(alert) {
    if (alert === 'none' || alert === 'normal' || alert === 'idle') {
        alertBanner.style.display = 'none';
        return;
    }

    alertBanner.style.display = 'flex';

    if (alert === 'critical_battery' || alert === 'critical') {
        alertBanner.className = 'alert-banner critical';
        alertIcon.textContent = '🔴';
        alertText.textContent = 'CRITICAL: Battery critically low!';
    } else if (alert === 'low_battery' || alert === 'warning') {
        alertBanner.className = 'alert-banner warning';
        alertIcon.textContent = '⚠️';
        alertText.textContent = 'Low battery warning';
    } else if (alert === 'disconnected') {
        alertBanner.className = 'alert-banner warning';
        alertIcon.textContent = '📡';
        alertText.textContent = 'Watchdog: No commands received';
    } else if (alert === 'estop') {
        alertBanner.className = 'alert-banner critical';
        alertIcon.textContent = '⛔';
        alertText.textContent = 'EMERGENCY STOP ACTIVE';
    }
}


// ══════════════════════════════════════════════════════════════════════════════
// Event Listeners
// ══════════════════════════════════════════════════════════════════════════════

// Preset buttons
presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        setActivePreset(action);
        sendCommand(action);

        // Haptic feedback
        if (navigator.vibrate) navigator.vibrate(20);
    });
});

// Speed slider
speedSlider.addEventListener('input', () => {
    const speed = parseFloat(speedSlider.value) / 100;
    speedValue.textContent = `${speed.toFixed(1)}x`;

    // Re-send current mode with updated speed
    if (activeMode && isConnected) {
        sendCommand(activeMode);
    }
});

// E-STOP button
btnEstop.addEventListener('click', () => {
    if (estopActive) {
        // Release E-STOP: go to stand
        estopActive = false;
        btnEstop.classList.remove('active');
        sendCommand('stand');
    } else {
        // Activate E-STOP
        estopActive = true;
        btnEstop.classList.add('active');
        sendEstop();
    }

    // Strong haptic
    if (navigator.vibrate) navigator.vibrate([50, 30, 50]);
});

// Prevent double-tap zoom on mobile
document.addEventListener('dblclick', (e) => e.preventDefault());


// ══════════════════════════════════════════════════════════════════════════════
// Initialise
// ══════════════════════════════════════════════════════════════════════════════

// Set initial UI state
setActivePreset('stand');
updateConnectionUI(false);

// Connect to WebSocket
connect();
