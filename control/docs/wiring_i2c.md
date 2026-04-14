# 🟣 I2C Bus — Raspberry Pi ↔ IMU + INA219

> Part of [VIGIL-RQ Wiring Documentation](wiring_diagram.md)

---

```mermaid
graph LR
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef imuPin fill:#d8b4fe,stroke:#a855f7,color:#3b0764
    classDef inaPin fill:#fde047,stroke:#eab308,color:#713f12
    classDef gnd fill:#475569,stroke:#334155,color:#fff
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff

    subgraph RPI_I2C["🍓 RASPBERRY PI 4B — I2C1"]
        RPI_SDA["GPIO 2 · Pin 3<br/>I2C1_SDA"]:::rpiPin
        RPI_SCL["GPIO 3 · Pin 5<br/>I2C1_SCL"]:::rpiPin
        RPI_3V3_I2C["3.3V · Pin 1"]:::vcc
        RPI_GND_I2C["GND · Pin 9"]:::gnd
    end

    subgraph IMU_BLOCK["🟣 MPU6050 / MPU9250 — 0x68"]
        IMU_SDA["SDA"]:::imuPin
        IMU_SCL["SCL"]:::imuPin
        IMU_VCC["VCC"]:::imuPin
        IMU_GND["GND"]:::imuPin
        IMU_AD0["AD0 → GND<br/>Addr: 0x68"]:::imuPin
        IMU_INT["INT — NC"]:::imuPin
    end

    subgraph INA_BLOCK["🟡 INA219 — 0x40"]
        INA_SDA["SDA"]:::inaPin
        INA_SCL["SCL"]:::inaPin
        INA_VCC["VCC"]:::inaPin
        INA_GND["GND"]:::inaPin
        INA_VINP["VIN+<br/>Servo rail +"]:::inaPin
        INA_VINN["VIN-<br/>To servos"]:::inaPin
        INA_A0["A0 → GND"]:::inaPin
        INA_A1["A1 → GND"]:::inaPin
    end

    subgraph I2C_BUS["🔗 SHARED I2C BUS"]
        BUS_SDA["SDA Bus"]:::rpiPin
        BUS_SCL["SCL Bus"]:::rpiPin
    end

    %% RPi → I2C bus (links 0-1)
    RPI_SDA ===|"🟣 SDA · 22AWG"| BUS_SDA
    RPI_SCL ===|"🔵 SCL · 22AWG"| BUS_SCL

    %% I2C bus → IMU (links 2-3)
    BUS_SDA ---|"🟣 SDA"| IMU_SDA
    BUS_SCL ---|"🔵 SCL"| IMU_SCL

    %% I2C bus → INA219 (links 4-5)
    BUS_SDA ---|"🟣 SDA"| INA_SDA
    BUS_SCL ---|"🔵 SCL"| INA_SCL

    %% Power (links 6-9)
    RPI_3V3_I2C -->|"🔴 3.3V"| IMU_VCC
    RPI_3V3_I2C -->|"🔴 3.3V"| INA_VCC
    RPI_GND_I2C -->|"⚫ GND"| IMU_GND
    RPI_GND_I2C -->|"⚫ GND"| INA_GND

    %% Address config (links 10-12)
    IMU_AD0 -.-|"Tie to GND"| IMU_GND
    INA_A0 -.-|"Tie to GND"| INA_GND
    INA_A1 -.-|"Tie to GND"| INA_GND

    linkStyle 0 stroke:#a855f7,stroke-width:3px
    linkStyle 1 stroke:#3b82f6,stroke-width:3px
    linkStyle 2 stroke:#a855f7,stroke-width:2px
    linkStyle 3 stroke:#3b82f6,stroke-width:2px
    linkStyle 4 stroke:#a855f7,stroke-width:2px
    linkStyle 5 stroke:#3b82f6,stroke-width:2px
    linkStyle 6,7 stroke:#ef4444,stroke-width:2px
    linkStyle 8,9 stroke:#475569,stroke-width:2px
    linkStyle 10,11,12 stroke:#94a3b8,stroke-width:1px,stroke-dasharray:5

    style RPI_I2C fill:#1e3a5f,stroke:#3b82f6,color:#93c5fd
    style IMU_BLOCK fill:#3b0764,stroke:#a855f7,color:#d8b4fe
    style INA_BLOCK fill:#713f12,stroke:#eab308,color:#fde047
    style I2C_BUS fill:#1e293b,stroke:#475569,color:#94a3b8
```

---

## I2C Device Addresses

| Device | Address | Config | Pins Tied |
|--------|---------|--------|-----------|
| MPU6050/9250 | `0x68` | AD0 → GND | AD0 to GND |
| INA219 | `0x40` | A0,A1 → GND | A0, A1 both to GND |

## I2C Pin Mapping

| RPi GPIO | RPi Pin | Signal | Wire Colour | Connects To |
|----------|---------|--------|-------------|-------------|
| GPIO 2 | 3 | SDA | 🟣 Purple | IMU SDA + INA219 SDA (shared bus) |
| GPIO 3 | 5 | SCL | 🔵 Blue | IMU SCL + INA219 SCL (shared bus) |
| 3.3V | 1 | VCC | 🔴 Red | IMU VCC + INA219 VCC |
| GND | 9 | Ground | ⚫ Black | IMU GND + INA219 GND |

> [!NOTE]
> **I2C pull-ups:** The RPi 4B has built-in 1.8kΩ pull-ups on SDA/SCL. Most breakout boards add their own. If using bare ICs, add **4.7kΩ pull-ups to 3.3V** on both SDA and SCL.

> [!TIP]
> Run `i2cdetect -y 1` on the RPi to verify both devices are detected at addresses `0x68` (IMU) and `0x40` (INA219) before running the server.

---

## IMU Mounting Orientation

The MPU6050/9250 must be mounted with the correct axis alignment for the gait engine to work properly:

```
    FRONT of robot
         ↑
         +X axis
         |
  +Y ←───┼──→ -Y
  (Left)  |   (Right)
         +Z axis (UP from board)
```

| IMU Axis | Robot Direction | Notes |
|----------|-----------------|-------|
| +X | Forward | Towards the head |
| +Y | Left | Towards FL/RL legs |
| +Z | Up | Away from the ground |
| Gyro X | Roll | Body tilt left/right |
| Gyro Y | Pitch | Body tilt forward/back |
| Gyro Z | Yaw | Body rotation |

> [!IMPORTANT]
> Mount the IMU **flat on the body center plate**, aligned with the long axis of the robot. Secure with double-sided foam tape to dampen servo vibration. Do **not** mount near servos or power wires.

---

## INA219 Shunt Wiring Detail

The INA219 has **two separate circuits** — I2C communication and high-side current sensing:

| Pin | Function | Connects To |
|-----|----------|-------------|
| VCC | Logic power (3.3V) | RPi Pin 1 (3.3V) |
| GND | Logic ground | Common GND bus |
| SDA | I2C data | Shared SDA bus |
| SCL | I2C clock | Shared SCL bus |
| VIN+ | High-side sense (+) | XL4015 output (+6.8V) |
| VIN- | High-side sense (-) | Servo distribution terminal |
| A0 | Address bit 0 | Tie to GND → address 0x40 |
| A1 | Address bit 1 | Tie to GND → address 0x40 |

> [!WARNING]
> **VIN+ and VIN- carry the full servo current** (up to 30A peak). Use **18 AWG wires** and ensure the 0.1Ω shunt resistor is rated for at least **3W**. The default TI shunt on breakout boards handles ~3.2A max — replace it with a **0.01Ω 5W shunt** if you need to measure higher currents.

---

## I2C Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `i2cdetect` shows nothing | Wrong bus or I2C not enabled | `sudo raspi-config` → Interface → enable I2C |
| Address 0x68 missing | AD0 not tied to GND | Solder/jumper AD0 → GND |
| Address 0x40 missing | A0/A1 floating | Tie A0 and A1 to GND |
| Garbage readings from IMU | Servo vibration coupling | Mount IMU on foam tape, away from servos |
| INA219 reads 0 current | Shunt not in series | Verify VIN+ comes from buck, VIN- goes to servos |
| I2C hangs / freezes | Bus collision or bad pull-ups | Check for shorted SDA/SCL; add 4.7kΩ pull-ups |

### Quick I2C Verification

```bash
# Enable I2C (one-time)
sudo raspi-config nonint do_i2c 0

# Scan for devices
sudo i2cdetect -y 1

# Expected output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 30:  -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40:  40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 50:  -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60:  -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --

# Read IMU WHO_AM_I register
sudo i2cget -y 1 0x68 0x75
# Should return 0x68 (MPU6050) or 0x71 (MPU9250)
```

