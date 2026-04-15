# 🍓 Raspberry Pi 4B — Complete Setup Guide (From Scratch)

> This guide takes a **brand new Raspberry Pi 4B** from unboxing to running the VIGIL-RQ calibration server. Every step is detailed.

---

## What You Need

| Item | Notes |
|------|-------|
| Raspberry Pi 4B (4GB) | The one you already have |
| microSD card (16GB+) | Class 10 / U1 minimum, 32GB recommended |
| microSD card reader | USB adapter for your PC |
| USB-C power supply | 5V 3A (official RPi PSU recommended) for initial setup |
| HDMI micro cable + monitor | For first boot only (can go headless after) |
| USB keyboard + mouse | For first boot only |
| Ethernet cable (optional) | Easier than WiFi for initial setup |
| Your PC/laptop | To flash the SD card |

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
4. Click **"Choose OS"** → Select **Raspberry Pi OS (64-bit)**
   - This is under "Raspberry Pi OS (other)" → **Raspberry Pi OS Lite (64-bit)**
   - Lite = no desktop (we don't need it, saves resources)
   - If you prefer a desktop for comfort, choose the full version instead
5. Click **"Choose Storage"** → Select your microSD card
6. Click the **⚙️ gear icon** (or "Edit Settings") before writing:

### OS Customisation Settings (IMPORTANT):

| Setting | Value |
|---------|-------|
| Set hostname | `vigilrq` |
| Enable SSH | ✅ **Use password authentication** |
| Set username | `pi` |
| Set password | Choose a strong password (remember this!) |
| Configure WiFi | Your home WiFi SSID + password |
| WiFi country | `IN` (India) |
| Set locale | Timezone: `Asia/Kolkata`, Keyboard: `us` |

7. Click **"Save"**
8. Click **"Write"** → Confirm → Wait (takes 5-10 minutes)
9. When done, safely eject the SD card

---

## Step 3: First Boot

1. Insert the microSD card into the RPi 4B
2. Connect:
   - HDMI cable to a monitor
   - USB keyboard and mouse
   - Ethernet cable (if available)
   - USB-C power supply (**plug in last**)
3. The RPi will boot — wait 1-2 minutes for first-time setup
4. If using Lite (no desktop), you'll see a login prompt:
   ```
   vigilrq login: pi
   Password: [your password]
   ```

---

## Step 4: Find Your RPi's IP Address

### Option A: From the RPi terminal
```bash
hostname -I
```
You'll see something like `192.168.1.42` — write this down.

### Option B: From your PC (if RPi is on same network)
```powershell
# On your Windows PC:
ping vigilrq.local
```

---

## Step 5: Enable SSH (if not already)

```bash
sudo raspi-config
```
Navigate: **Interface Options** → **SSH** → **Enable** → **Finish**

Now you can unplug the monitor/keyboard and SSH from your PC:
```powershell
# From your Windows PC:
ssh pi@vigilrq.local
# Or:
ssh pi@192.168.1.42
```

---

## Step 6: Update the System

```bash
sudo apt update && sudo apt upgrade -y
```
This can take 5-15 minutes. Let it finish.

---

## Step 7: Enable SPI & I2C

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

## Step 8: Install Python Dependencies

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

## Step 9: Clone the VIGIL-RQ Repository

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

## Step 10: Set Up WiFi Access Point (for Fieldwork)

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

## Step 11: Test the Calibration Server (No Hardware)

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
