# 🍓 Raspberry Pi 4B — Complete Setup Guide (From Scratch)

> This guide takes a **brand new Raspberry Pi 4B** from unboxing to running the VIGIL-RQ calibration server. Every step is detailed.

---

## What You Need

| Item | Notes |
|------|-------|
| Raspberry Pi 4B (4GB) | The one you already have |
| microSD card (16GB+) | Class 10 / U1 minimum, 32GB recommended |
| microSD card reader | USB adapter for your PC |
| USB-C power supply | 5V 3A (official RPi PSU recommended) |
| Your PC/laptop | To flash the SD card + SSH in |

> [!TIP]
> **No monitor, keyboard, or mouse needed!** We configure WiFi and SSH in the Raspberry Pi Imager *before* first boot, so the RPi connects to your WiFi automatically and you SSH in from your laptop. Fully headless from the start.

---

## Step 1: Download Raspberry Pi OS

1. Go to **https://www.raspberrypi.com/software/**
2. Download **Raspberry Pi Imager** for Windows
3. Install and run it

---

## Step 2: Flash the SD Card

1. Insert your microSD card into your PC
2. Open **Raspberry Pi Imager**
3. Click **"Choose Device"** → Select **Raspberry Pi 4**
4. Click **"Choose OS"**:
   - Go to **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**
   - **Use Lite** — we run everything headless via SSH. No desktop needed.
   - Lite uses ~200MB RAM vs ~800MB for desktop → more room for our Python server
5. Click **"Choose Storage"** → Select your microSD card
6. Click the **⚙️ gear icon** (or "Edit Settings") before writing:

### OS Customisation Settings (CRITICAL for headless):

| Setting | Value | Why |
|---------|-------|-----|
| Set hostname | `vigilrq` | So you can `ssh pi@vigilrq.local` |
| Enable SSH | ✅ **Use password authentication** | **This is required — no monitor!** |
| Set username | `pi` | Standard RPi username |
| Set password | Choose a strong password (remember this!) | Your SSH login password |
| Configure WiFi | Your home WiFi SSID + password | **This is required — no monitor!** |
| WiFi country | `IN` (India) | Must match your region |
| Set locale | Timezone: `Asia/Kolkata`, Keyboard: `us` | Optional but helpful |

> [!CAUTION]
> **You MUST set WiFi and SSH in this step.** Without a monitor, these are your only way to connect to the RPi after first boot. Double-check your WiFi password!

7. Click **"Save"**
8. Click **"Write"** → Confirm → Wait (takes 5-10 minutes)
9. When done, safely eject the SD card

---

## Step 3: First Boot (Headless)

1. Insert the microSD card into the RPi 4B
2. Plug in the USB-C power supply — **that's it, nothing else to connect**
3. Wait **60-90 seconds** — the RPi is:
   - Expanding the filesystem
   - Connecting to your WiFi
   - Starting the SSH server
4. The green activity LED on the RPi should flicker during boot, then calm down

---

## Step 4: SSH into the RPi from Your Laptop

Open **PowerShell** or **Windows Terminal** on your laptop:

### Option A: Using hostname (recommended)
```powershell
ssh pi@vigilrq.local
```
Type `yes` when asked about the fingerprint, then enter your password.

### Option B: If `.local` doesn't resolve
Find the RPi IP from your **router's admin page** (usually `192.168.1.1`):
- Look for a device named `vigilrq` in the connected devices list
- Note its IP (e.g., `192.168.1.42`)

```powershell
ssh pi@192.168.1.42
```

### Option C: Scan the network
```powershell
# Find all devices on your network
arp -a
```
Look for new entries that appeared after plugging in the RPi.

> [!TIP]
> If SSH still doesn't work after 2 minutes:
> - Make sure your laptop is on the **same WiFi** as the RPi
> - Double-check the WiFi SSID and password you entered in Imager
> - Try power-cycling the RPi (unplug and replug USB-C)
> - As a last resort: re-flash the SD card and verify the WiFi settings

### Once connected, verify:
```bash
# Check you're on the Pi
hostname
# Should output: vigilrq

# Check WiFi connection
hostname -I
# Should show an IP like 192.168.1.42
```

---

## Step 5: Update the System

```bash
sudo apt update && sudo apt upgrade -y
```
This can take 5-15 minutes. Let it finish.

---

## Step 6: Enable SPI & I2C

```bash
sudo raspi-config
```
Navigate to **Interface Options** and enable:
- **SPI** → Enable
- **I2C** → Enable

Then reboot:
```bash
sudo reboot
```

Wait ~30 seconds, then SSH back in.

### Verify SPI is enabled:
```bash
ls /dev/spidev*
```
Expected output:
```
/dev/spidev0.0  /dev/spidev0.1
```

### Verify I2C is enabled:
```bash
ls /dev/i2c*
```
Expected output:
```
/dev/i2c-1
```

---

## Step 7: Install Python Dependencies

```bash
# Ensure pip is installed
sudo apt install -y python3-pip python3-venv git

# Install required Python packages (system-wide for sudo access)
sudo pip3 install websockets spidev smbus2 numpy RPi.GPIO --break-system-packages
```

### Verify installations:
```bash
python3 -c "import spidev; print('spidev OK')"
python3 -c "import websockets; print('websockets OK')"
python3 -c "import RPi.GPIO; print('RPi.GPIO OK')"
python3 -c "import smbus2; print('smbus2 OK')"
python3 -c "import numpy; print('numpy OK')"
```
All should print "OK".

---

## Step 8: Clone the VIGIL-RQ Repository

```bash
cd ~
git clone https://github.com/Major-Project-001/VIGIL-RQ.git
cd VIGIL-RQ
git checkout control
```

### Verify the files are there:
```bash
ls control/calibration/
```
Expected:
```
app.js  calib_server.py  index.html  style.css
```

---

## Step 9: Set Up WiFi Access Point (for Fieldwork)

When you're away from your home WiFi, the RPi creates its own WiFi network that your phone connects to.

```bash
# Create a WiFi hotspot
sudo nmcli device wifi hotspot ifname wlan0 ssid VIGIL-RQ password vigilrq2026

# Make it persistent (auto-start on boot)
sudo nmcli connection modify Hotspot connection.autoconnect yes
```

### To switch back to your home WiFi:
```bash
sudo nmcli connection up "your-home-wifi-name"
```

### To switch back to hotspot mode:
```bash
sudo nmcli connection up Hotspot
```

> [!NOTE]
> When in hotspot mode, the RPi's IP is usually `10.42.0.1`. Your phone connects to the `VIGIL-RQ` WiFi, then opens `http://10.42.0.1:8080` in a browser.

---

## Step 10: Test the Calibration Server (No Hardware)

Even without the FPGA connected, you can test the server in simulation mode:

```bash
cd ~/VIGIL-RQ/control/calibration
python3 calib_server.py
```

You should see:
```
============================================================
  🎯 VIGIL-RQ Servo Calibration Tool
============================================================
[SPI] spidev not available — running in simulation mode
[SPI] Running in simulation mode (no hardware)
[CALIB] All servos set to neutral (1500 µs)
[HTTP] Serving calibration UI on http://0.0.0.0:8080
[WS] WebSocket server on ws://0.0.0.0:8765
```

Open your browser at `http://vigilrq.local:8080` or `http://<rpi-ip>:8080`.

Press `Ctrl+C` to stop.

---

## Quick Reference Card

| Task | Command |
|------|---------|
| SSH into RPi | `ssh pi@vigilrq.local` |
| Check IP | `hostname -I` |
| Start calibration | `cd ~/VIGIL-RQ/control/calibration && sudo python3 calib_server.py` |
| Start hotspot | `sudo nmcli connection up Hotspot` |
| Start home WiFi | `sudo nmcli connection up "your-wifi"` |
| Reboot | `sudo reboot` |
| Shutdown safely | `sudo shutdown -h now` |
| Check SPI | `ls /dev/spidev*` |
| Check I2C | `sudo i2cdetect -y 1` |
| Pull latest code | `cd ~/VIGIL-RQ && git pull` |

---

## What's Next?

Once the RPi is set up:
1. → [Flash the FPGA](fpga_flash_guide.md)
2. → [Run the Calibration Tool](setup_guide.md)
