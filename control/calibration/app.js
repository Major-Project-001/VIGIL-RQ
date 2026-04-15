/**
 * VIGIL-RQ Servo Calibrator — WebSocket Client & Slider Logic
 */

// ── Configuration ──
const WS_PORT = 8765;
const PULSE_MIN = 500;
const PULSE_MAX = 2500;
const PULSE_NEUTRAL = 1500;
const ANGLE_MIN = -135;
const ANGLE_MAX = 135;

// ── Joint name lookup ──
const JOINT_NAMES = [
    "FL Hip", "FL Thigh", "FL Knee",
    "FR Hip", "FR Thigh", "FR Knee",
    "RL Hip", "RL Thigh", "RL Knee",
    "RR Hip", "RR Thigh", "RR Knee",
];

// ── DOM Elements ──
const servoSelect = document.getElementById("servoSelect");
const angleSlider = document.getElementById("angleSlider");
const angleLabel = document.getElementById("angleLabel");
const pulseLabel = document.getElementById("pulseLabel");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");
const btnCenter = document.getElementById("btnCenter");
const btnCenterAll = document.getElementById("btnCenterAll");
const btnSave = document.getElementById("btnSave");
const statusEl = document.getElementById("connectionStatus");
const statusText = statusEl.querySelector(".status-text");

const infoChannel = document.getElementById("infoChannel");
const infoJoint = document.getElementById("infoJoint");
const infoAngle = document.getElementById("infoAngle");
const infoPulse = document.getElementById("infoPulse");
const infoOffset = document.getElementById("infoOffset");
const infoStatus = document.getElementById("infoStatus");

// ── State ──
let ws = null;
let currentChannel = 0;
let servoPositions = new Array(12).fill(PULSE_NEUTRAL);
let reconnectTimer = null;

// ── Conversion Helpers ──
function angleToPulse(angleDeg) {
    // Linear: -135° → 500µs, 0° → 1500µs, +135° → 2500µs
    const normalized = (angleDeg - ANGLE_MIN) / (ANGLE_MAX - ANGLE_MIN);
    return Math.round(PULSE_MIN + normalized * (PULSE_MAX - PULSE_MIN));
}

function pulseToAngle(pulseUs) {
    const normalized = (pulseUs - PULSE_MIN) / (PULSE_MAX - PULSE_MIN);
    return ANGLE_MIN + normalized * (ANGLE_MAX - ANGLE_MIN);
}

// ── UI Update ──
function updateDisplay() {
    const angle = parseFloat(angleSlider.value);
    const pulse = angleToPulse(angle);
    const offset = pulse - PULSE_NEUTRAL;

    // Large display
    const sign = angle >= 0 ? "+" : "";
    angleLabel.textContent = `${sign}${angle.toFixed(1)}°`;
    pulseLabel.textContent = `${pulse} µs`;

    // Info grid
    infoChannel.textContent = currentChannel;
    infoJoint.textContent = JOINT_NAMES[currentChannel] || `Ch ${currentChannel}`;
    infoAngle.textContent = `${sign}${angle.toFixed(1)}°`;
    infoPulse.textContent = `${pulse} µs`;

    const offsetSign = offset >= 0 ? "+" : "";
    infoOffset.textContent = `${offsetSign}${offset} µs`;
    infoOffset.style.color = offset === 0
        ? "var(--green)"
        : Math.abs(offset) > 500
            ? "var(--red)"
            : "var(--orange)";

    // Color the angle label based on position
    const absAngle = Math.abs(angle);
    if (absAngle < 5) {
        angleLabel.style.color = "var(--green)";
    } else if (absAngle < 45) {
        angleLabel.style.color = "var(--accent-bright)";
    } else if (absAngle < 90) {
        angleLabel.style.color = "var(--orange)";
    } else {
        angleLabel.style.color = "var(--red)";
    }

    // Store position
    servoPositions[currentChannel] = pulse;
}

function selectChannel(ch) {
    currentChannel = Math.max(0, Math.min(11, ch));
    servoSelect.value = currentChannel;

    // Restore saved position or default to center
    const savedPulse = servoPositions[currentChannel];
    const angle = pulseToAngle(savedPulse);
    angleSlider.value = angle;

    updateDisplay();
}

// ── WebSocket ──
function connect() {
    const host = window.location.hostname || "localhost";
    const url = `ws://${host}:${WS_PORT}`;

    infoStatus.textContent = "Connecting...";
    ws = new WebSocket(url);

    ws.onopen = () => {
        statusEl.classList.add("connected");
        statusText.textContent = "Connected";
        infoStatus.textContent = "Connected";
        infoStatus.style.color = "var(--green)";
        if (reconnectTimer) clearTimeout(reconnectTimer);
        console.log("[WS] Connected to", url);
    };

    ws.onclose = () => {
        statusEl.classList.remove("connected");
        statusText.textContent = "Disconnected";
        infoStatus.textContent = "Disconnected";
        infoStatus.style.color = "var(--red)";
        console.log("[WS] Disconnected — reconnecting in 2s");
        reconnectTimer = setTimeout(connect, 2000);
    };

    ws.onerror = (err) => {
        console.error("[WS] Error:", err);
        ws.close();
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === "state") {
                // Initial state from server
                if (data.positions) {
                    for (const [ch, us] of Object.entries(data.positions)) {
                        servoPositions[parseInt(ch)] = us;
                    }
                }
                selectChannel(currentChannel);
            }

            if (data.type === "centered") {
                servoPositions[data.ch] = data.us;
                if (data.ch === currentChannel) {
                    angleSlider.value = 0;
                    updateDisplay();
                }
                showToast(`Ch ${data.ch} centered`);
            }

            if (data.type === "centered_all") {
                servoPositions.fill(PULSE_NEUTRAL);
                angleSlider.value = 0;
                updateDisplay();
                showToast("All servos centered ⊙");
            }

            if (data.type === "offsets_saved") {
                showToast("💾 Offsets saved!");
                console.log("Saved offsets:", data.offsets);
            }

        } catch (e) {
            console.error("[WS] Parse error:", e);
        }
    };
}

function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
    }
}

// ── Event Handlers ──
angleSlider.addEventListener("input", () => {
    updateDisplay();
    const pulse = angleToPulse(parseFloat(angleSlider.value));
    send({ cmd: "servo", ch: currentChannel, us: pulse });
});

servoSelect.addEventListener("change", () => {
    selectChannel(parseInt(servoSelect.value));
});

btnPrev.addEventListener("click", () => {
    selectChannel(currentChannel - 1);
});

btnNext.addEventListener("click", () => {
    selectChannel(currentChannel + 1);
});

btnCenter.addEventListener("click", () => {
    angleSlider.value = 0;
    updateDisplay();
    send({ cmd: "center", ch: currentChannel });
});

btnCenterAll.addEventListener("click", () => {
    send({ cmd: "center_all" });
});

btnSave.addEventListener("click", () => {
    send({ cmd: "save_offsets" });
});

// ── Keyboard shortcuts ──
document.addEventListener("keydown", (e) => {
    switch (e.key) {
        case "ArrowLeft":
            angleSlider.value = parseFloat(angleSlider.value) - (e.shiftKey ? 5 : 0.5);
            angleSlider.dispatchEvent(new Event("input"));
            break;
        case "ArrowRight":
            angleSlider.value = parseFloat(angleSlider.value) + (e.shiftKey ? 5 : 0.5);
            angleSlider.dispatchEvent(new Event("input"));
            break;
        case "ArrowUp":
            e.preventDefault();
            selectChannel(currentChannel - 1);
            break;
        case "ArrowDown":
            e.preventDefault();
            selectChannel(currentChannel + 1);
            break;
        case " ":
        case "0":
            e.preventDefault();
            btnCenter.click();
            break;
    }
});

// ── Toast ──
function showToast(message) {
    let toast = document.querySelector(".toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.className = "toast";
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2000);
}

// ── Init ──
updateDisplay();
connect();
