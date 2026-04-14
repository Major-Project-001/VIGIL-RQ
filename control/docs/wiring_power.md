# ⚡ Power Distribution — Pin-Level Detail

> Part of [VIGIL-RQ Wiring Documentation](wiring_diagram.md)

---

```mermaid
graph LR
    classDef power fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef powerPin fill:#fca5a5,stroke:#ef4444,color:#7f1d1d
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff,font-weight:bold
    classDef gnd fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12

    subgraph BATTERY["🔋 18650 3S PACK — 11.1V"]
        BAT_POS["+ Positive"]:::powerPin
        BAT_NEG["- Negative"]:::powerPin
    end

    subgraph BMS_BLOCK["🛡 3S BMS"]
        BMS_BIN["B+ In"]:::powerPin
        BMS_BMIN["B- In"]:::powerPin
        BMS_POUT["P+ Out"]:::powerPin
        BMS_NOUT["P- Out"]:::powerPin
    end

    subgraph FUSE_BLOCK["⚡ 15A INLINE FUSE"]
        FUSE_IN["Fuse In"]:::powerPin
        FUSE_OUT["Fuse Out"]:::powerPin
    end

    subgraph TERMINAL["📦 SCREW TERMINAL BLOCK"]
        T_VIN["+V In"]:::powerPin
        T_GND["GND In"]:::powerPin
        T_OUT1["+V Out 1"]:::powerPin
        T_OUT2["+V Out 2"]:::powerPin
        T_GND1["GND Out 1"]:::powerPin
        T_GND2["GND Out 2"]:::powerPin
    end

    subgraph DIODES["🔒 SCHOTTKY DIODES"]
        D1_A["1N5822 #1 Anode"]:::powerPin
        D1_K["1N5822 #1 Cathode"]:::powerPin
        D2_A["1N5822 #2 Anode"]:::powerPin
        D2_K["1N5822 #2 Cathode"]:::powerPin
    end

    subgraph BUCK_SERVO["⬇ XL4015 BUCK — 6.8V SERVO RAIL"]
        BS_VIN["VIN"]:::powerPin
        BS_GND["GND"]:::powerPin
        BS_VOUT["VOUT 6.8V"]:::vcc
        BS_GNDO["GND OUT"]:::gnd
    end

    subgraph BUCK_LOGIC["⬇ LM2596 BUCK — 5V LOGIC RAIL"]
        BL_VIN["VIN"]:::powerPin
        BL_GND["GND"]:::powerPin
        BL_VOUT["VOUT 5V"]:::vcc
        BL_GNDO["GND OUT"]:::gnd
    end

    subgraph COMMON_BUS["🔗 COMMON GROUND BUS"]
        GND_BUS["⏚ COMMON GND"]:::gnd
    end

    subgraph LOADS["📤 POWER OUTPUTS"]
        RPI_5V["RPi 4B — USB-C 5V"]:::rpiPin
        FPGA_5V["Tang Nano 9K — USB-C 5V"]:::rpiPin
        LS_HV["Level Shifters — HV 5V"]:::lsPin
        SERVO_PWR["12× Servos — 6.8V Rail"]:::servoPin
    end

    %% Battery → BMS (links 0-1)
    BAT_POS -->|"🔴 14AWG"| BMS_BIN
    BAT_NEG -->|"⚫ 14AWG"| BMS_BMIN

    %% BMS → Fuse/GND (links 2-3)
    BMS_POUT -->|"🔴 14AWG"| FUSE_IN
    BMS_NOUT -->|"⚫ 14AWG"| GND_BUS

    %% Fuse → Terminal (links 4-5)
    FUSE_OUT -->|"🔴 14AWG"| T_VIN
    GND_BUS -->|"⚫ 14AWG"| T_GND

    %% Terminal → Diodes → Bucks (links 6-11)
    T_OUT1 -->|"🔴 16AWG"| D1_A
    D1_K -->|"🔴 16AWG"| BS_VIN
    T_OUT2 -->|"🔴 16AWG"| D2_A
    D2_K -->|"🔴 16AWG"| BL_VIN
    T_GND1 -->|"⚫ 16AWG"| BS_GND
    T_GND2 -->|"⚫ 16AWG"| BL_GND

    %% Buck GND → common (links 12-13)
    BS_GNDO --> GND_BUS
    BL_GNDO --> GND_BUS

    %% Buck outputs → loads (links 14-17)
    BS_VOUT ==>|"🔴 18AWG × 6 pairs"| SERVO_PWR
    BL_VOUT -->|"🔴 USB-C"| RPI_5V
    BL_VOUT -->|"🔴 USB-C"| FPGA_5V
    BL_VOUT -->|"🔴 22AWG"| LS_HV

    linkStyle 0 stroke:#ef4444,stroke-width:3px
    linkStyle 1 stroke:#475569,stroke-width:3px
    linkStyle 2 stroke:#ef4444,stroke-width:3px
    linkStyle 3 stroke:#475569,stroke-width:3px
    linkStyle 4 stroke:#ef4444,stroke-width:3px
    linkStyle 5 stroke:#475569,stroke-width:3px
    linkStyle 6,7,8,9 stroke:#ef4444,stroke-width:2px
    linkStyle 10,11 stroke:#475569,stroke-width:2px
    linkStyle 12,13 stroke:#475569,stroke-width:2px
    linkStyle 14 stroke:#ef4444,stroke-width:3px
    linkStyle 15,16,17 stroke:#ef4444,stroke-width:2px
```

---

## Power Rail Summary

| Rail | Source | Voltage | Current | Wire Gauge | Feeds |
|------|--------|---------|---------|------------|-------|
| Servo | XL4015 | 6.8V | ~15A peak | 18 AWG | 12× DS3218 servos |
| Logic | LM2596 | 5.0V | ~2A | USB-C | RPi 4B, Tang Nano 9K |
| LV Ref | FPGA 3.3V | 3.3V | <50mA | 22 AWG | 3× level shifters (LV side) |
| I2C | RPi 3.3V | 3.3V | <20mA | 22 AWG | IMU, INA219 |

> [!WARNING]
> **Always adjust buck converter trimpots with a multimeter BEFORE connecting any load.** Set XL4015 to 6.8V and LM2596 to 5.0V. Incorrect voltage will destroy the RPi or servos.

---

## 18650 Battery Pack Specifications

| Parameter | Value |
|-----------|-------|
| Chemistry | Li-ion (18650 cells) |
| Configuration | 3S1P (3 cells in series) |
| Nominal voltage | 11.1V (3.7V × 3) |
| Fully charged | 12.6V (4.2V × 3) |
| Low cutoff | 9.0V (3.0V × 3) — BMS disconnects |
| Capacity (typical) | 2500–3500 mAh per cell |
| Max continuous discharge | Depends on cell rating (use 10A+ cells) |

> [!TIP]
> Use high-drain cells like **Samsung 25R** (20A) or **Sony VTC6** (15A) for reliable servo power. Standard laptop-pull 18650s may sag under load and trip the BMS.

---

## Capacitor Recommendations

Add decoupling capacitors to stabilize voltage under servo load transients:

| Location | Capacitor | Purpose |
|----------|-----------|---------|
| XL4015 output | **1000µF 10V electrolytic** | Smooths 6.8V servo rail under surge |
| LM2596 output | **470µF 10V electrolytic** | Stabilizes 5V logic rail |
| Each level shifter VCC | **100nF ceramic** | Decouples high-frequency noise |
| RPi 3.3V rail | **100nF ceramic** | Stabilizes I2C/SPI reference |

> [!NOTE]
> Place the 1000µF cap **as close as possible** to the servo power distribution point (terminal block output). Long leads add inductance and reduce effectiveness.

---

## Buck Converter Setup Procedure

### XL4015 (Servo Rail — 6.8V)

1. **Disconnect all servos** from the output
2. Connect battery → BMS → fuse → terminal → diode → XL4015 VIN
3. Turn the **trimpot clockwise** slowly while measuring VOUT with multimeter
4. Stop when VOUT reads **6.8V ± 0.1V**
5. Verify it holds steady for 30 seconds
6. Only then connect servo power wires

### LM2596 (Logic Rail — 5.0V)

1. **Disconnect RPi and FPGA** USB-C cables
2. Connect battery → BMS → fuse → terminal → diode → LM2596 VIN
3. Turn the **trimpot** while measuring VOUT
4. Stop when VOUT reads **5.0V ± 0.05V**
5. RPi 4B tolerates 4.75V–5.25V; stay centered
6. Only then connect USB-C power cables

---

## Total System Current Budget

| Subsystem | Voltage | Idle | Typical | Peak |
|-----------|---------|------|---------|------|
| 12× DS3218 servos | 6.8V | 1.8A | 6A | 30A |
| Raspberry Pi 4B | 5.0V | 0.6A | 1.0A | 1.2A |
| Tang Nano 9K | 5.0V | 0.05A | 0.1A | 0.15A |
| 3× Level shifters | 5.0V/3.3V | <0.01A | <0.01A | <0.02A |
| IMU + INA219 | 3.3V | <0.01A | <0.01A | <0.01A |
| Buzzer + RGB LED | 3.3V | 0A | 0.03A | 0.05A |
| **Total from battery** | **11.1V** | **~1.5A** | **~4.5A** | **~18A** |

> [!IMPORTANT]
> At typical walking load (~4.5A from battery), a 3000mAh pack gives roughly **40 minutes** of operation. Monitor via the INA219 and set low-battery alert at **10.0V** (in `config.py`).

