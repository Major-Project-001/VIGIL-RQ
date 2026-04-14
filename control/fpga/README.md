# VIGIL-RQ — FPGA PWM Controller

## Tang Nano 9K (GW1NR-9C) — 12-Channel Servo PWM Generator

This module generates 12 independent, hardware-precise PWM signals for DS3218 servos. The Raspberry Pi 4B sends servo position commands over SPI, and the FPGA converts them into jitter-free PWM outputs.

### Architecture

```
RPi 4B (SPI Master) → SPI Slave → Channel Registers → 12× PWM Generators → Level Shifters → Servos
```

### Files

| File | Description |
|------|-------------|
| `src/top.sv` | Top-level: clock, reset, pin mapping |
| `src/spi_slave.sv` | SPI Mode 0 slave receiver (3-byte frames) |
| `src/pwm_channel.sv` | Single PWM channel (50 Hz, configurable pulse width) |
| `src/pwm_controller.sv` | 12-channel integration + SPI + watchdog |
| `tb/tb_pwm_controller.sv` | Testbench with SPI transaction simulation |
| `constraints/tangnano9k.cst` | Pin assignments for Tang Nano 9K |

### SPI Protocol

- **Mode:** SPI Mode 0 (CPOL=0, CPHA=0)
- **Clock:** 1 MHz
- **Frame:** 3 bytes — `[channel_id (8-bit)] [pulse_us_hi] [pulse_us_lo]`
- **Channel IDs:** 0–11 (FL Hip, FL Thigh, FL Knee, FR Hip, ...)

### Building with Gowin EDA

1. Create a new project targeting **GW1NR-9C** (QFN88P package)
2. Add all `.sv` files from `src/`
3. Add `constraints/tangnano9k.cst`
4. Set top module to `top`
5. Synthesize → Place & Route → Generate bitstream
6. Program via Gowin Programmer (USB-JTAG)

### On-board LED Indicators

| LED | Meaning |
|-----|---------|
| LED[0] | Heartbeat (~1.6 Hz blink = FPGA running) |
| LED[1] | SPI activity (lit during CS active) |
| LED[2–5] | Unused (off) |

### Safety: Watchdog Timer

If no SPI command is received within **500 ms**, all 12 channels automatically reset to neutral (1500 µs). This prevents servo runaway if the RPi crashes or loses connection.
