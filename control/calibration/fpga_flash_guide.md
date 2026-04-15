# 🟢 Tang Nano 9K — FPGA Flash Guide

> Step-by-step guide to synthesize and flash the VIGIL-RQ PWM controller onto the Tang Nano 9K (GW1NR-9C) using Gowin EDA.

---

## What You Need

| Item | Notes |
|------|-------|
| Tang Nano 9K board | Sipeed Tang Nano 9K (GW1NR-9C, QFN88P) |
| USB-C cable | For programming (USB-JTAG) and power |
| Your PC (Windows) | Gowin EDA runs on Windows |
| Gowin EDA IDE | Free version (Educational/Standard) |

---

## Step 1: Install Gowin EDA

1. Go to **https://www.gowinsemi.com/en/support/download_eda/**
2. Download **Gowin EDA (Standard) for Windows**
   - You'll need to create a free account
3. Also download a **free license** from the same page:
   - Click "Apply for License" → fill form → get license file via email
4. Install Gowin EDA (default location is fine)
5. On first launch, point it to your license file:
   - **Tools** → **License Manager** → Browse to your `.lic` file

---

## Step 2: Install USB Driver (if not auto-detected)

1. Plug in the Tang Nano 9K via USB-C
2. Windows should detect it as a USB device
3. If not recognized:
   - Download **Zadig** from https://zadig.akeo.ie/
   - Open Zadig → **Options** → **List All Devices**
   - Find **"JTAG Debugger"** or **"FTDI"** in the dropdown
   - Select **WinUSB** driver → Click **"Install Driver"**
4. Verify: in Device Manager, you should see the device under "Universal Serial Bus devices"

---

## Step 3: Create a New Project

1. Open **Gowin EDA**
2. **File** → **New** → **FPGA Design Project**
3. Set project name: `vigil_rq_pwm`
4. Set project location: choose a convenient folder (e.g., `D:\FPGA\vigil_rq_pwm`)
5. Click **Next**
6. **Select Device:**

   | Parameter | Value |
   |-----------|-------|
   | Series | GW1NR |
   | Device | GW1NR-9C |
   | Package | QFN88P |
   | Speed | C6/I5 |

7. Click **Next** → **Finish**

---

## Step 4: Add Source Files

1. In the Project pane (left side), right-click **"Design"** → **"Add Files..."**
2. Navigate to your `VIGIL-RQ/control/fpga/src/` folder
3. Select **all 4 files**:
   - `top.sv`
   - `pwm_controller.sv`
   - `pwm_channel.sv`
   - `spi_slave.sv`
4. Click **Open** (they should appear in the Design hierarchy)

### Set Top Module:
5. Right-click on `top.sv` → **"Set as Top Module"**
   - Or: **Project** → **Configuration** → **Synthesize** → Top Module: `top`

---

## Step 5: Add Constraints File

1. Right-click **"Design"** → **"Add Files..."**
2. Navigate to `VIGIL-RQ/control/fpga/constraints/`
3. Select `tangnano9k.cst`
4. Click **Open**

This maps our signal names to physical FPGA pins.

---

## Step 6: Synthesize

1. Click the **"Synthesize"** button (or **Process** → **Synthesize**)
2. Wait for the synthesis to complete (takes ~10-30 seconds)
3. Check the **Console** pane at the bottom:
   - ✅ Should say "Synthesize completed successfully"
   - ❌ If errors, double-check :
     - Top module is set to `top`
     - All 4 `.sv` files are added
     - Device is GW1NR-9C

### Check resource usage (Console output):
```
Resource Usage:
  Logic:     ~350 / 8640 LUT (4%)
  Register:  ~250 / 6693 FF  (3%)
  BRAM:      0 / 26
```
Our design is tiny — plenty of room left.

---

## Step 7: Place & Route

1. Click the **"Place & Route"** button (or **Process** → **Place & Route**)
2. Wait for completion (~10-20 seconds)
3. Console should say "Place & Route completed successfully"

---

## Step 8: Generate Bitstream

1. **Process** → **Generate Bitstream** (or the corresponding toolbar button)
2. Wait a few seconds
3. Console: "Generate Bitstream completed successfully"
4. The bitstream file is at: `impl/pnr/vigil_rq_pwm.fs`

---

## Step 9: Program the FPGA

1. Ensure the Tang Nano 9K is plugged in via USB-C
2. Open **Gowin Programmer**:
   - **Tools** → **Programmer** (or launch it separately from Start Menu)
3. Click **"Scan Device"** — it should detect the GW1NR-9C
4. Configure programming:

   | Setting | Value |
   |---------|-------|
   | Access Mode | **SRAM Program** (for testing) |
   | Operation | Programming |
   | File | Browse to `impl/pnr/vigil_rq_pwm.fs` |

   > **SRAM Program** = temporary, lost on power cycle (good for testing)
   > **External Flash** = permanent, survives power cycle (for production)

5. Click **"Program/Configure"**
6. Wait 2-5 seconds → "Programming Completed Successfully"

### For permanent flash (after testing):
- Change **Access Mode** to **External Flash Mode**
- This writes to the onboard SPI flash — survives power cycles

---

## Step 10: Verify the FPGA is Running

After programming, you should see:

| What to Check | Expected |
|----------------|----------|
| LED[0] on the board | **Blinking ~1.6 Hz** (heartbeat) |
| LED[1] | Off (no SPI activity yet) |
| Board power LED | Solid on |

If LED[0] is blinking, the FPGA is running the PWM controller! 🎉

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Gowin Programmer doesn't detect board | Reinstall USB driver with Zadig (WinUSB) |
| Synthesis errors about missing module | Check all 4 `.sv` files are added to project |
| "Top module not found" | Right-click `top.sv` → Set as Top Module |
| LED[0] not blinking after programming | Re-flash; make sure you selected the correct `.fs` file |
| Board not powering on | Try a different USB-C cable (some are charge-only) |
| License error | Re-download license from Gowin website; check expiry |

---

## File Reference

| File | Purpose |
|------|---------|
| `src/top.sv` | Top-level: clock, reset, heartbeat, pin mapping |
| `src/pwm_controller.sv` | 12-channel PWM with SPI receiver + watchdog |
| `src/pwm_channel.sv` | Single 50Hz PWM generator |
| `src/spi_slave.sv` | SPI Mode 0 slave (3-byte frame decoder) |
| `constraints/tangnano9k.cst` | Pin assignments for Tang Nano 9K |
| `tb/tb_pwm_controller.sv` | Testbench (simulation only) |

---

## What's Next?

Once the FPGA is flashed and LED[0] is blinking:
1. → [Set up the Raspberry Pi](rpi_setup_guide.md) (if not done)
2. → [Run the Calibration Tool](setup_guide.md)
