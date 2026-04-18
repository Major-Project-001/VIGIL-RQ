# 🔌 VIGIL-RQ — Complete Wiring & Connection Diagram

> Pin-level wiring reference for every electronic connection on the VIGIL-RQ quadruped robot.
> All nodes are color-coded by module, all connection lines are color-coded by signal type.

---

## 📁 Wiring Documentation Index

| # | Section | File | Diagrams |
|---|---------|------|----------|
| 1 | **System Overview** | This file | Full system block diagram |
| 2 | **Power Distribution** | [wiring_power.md](wiring_power.md) | Battery → BMS → Fuse → Bucks |
| 3 | **SPI Bus** | [wiring_spi.md](wiring_spi.md) | RPi ↔ FPGA pin-level + frame format |
| 4 | **I2C Bus** | [wiring_i2c.md](wiring_i2c.md) | RPi ↔ IMU + INA219 shared bus |
| 5 | **PWM Outputs** | [wiring_pwm.md](wiring_pwm.md) | FPGA → 3 Level Shifters → 12 Servos |
| 6 | **GPIO Alerts** | [wiring_gpio.md](wiring_gpio.md) | Buzzer + RGB LED + colour codes |
| 7 | **Servo Power** | [wiring_servo_power.md](wiring_servo_power.md) | 6.8V rail to all 12 DS3218 (per leg) |
| 8-10 | **Reference** | [wiring_reference.md](wiring_reference.md) | INA219 shunt, GND bus, pin tables, checklist |

---

### 🎨 Wire Colour Legend

| Line Colour | Meaning | Used On |
|-------------|---------|---------|
| 🔴 Red `━━` | VCC / Power positive | Battery, buck outputs, 3.3V, 5V rails |
| ⚫ Grey `━━` | GND | All ground connections |
| 🔵 Blue `━━` | SPI SCLK / I2C SCL | Clock signals |
| 🟢 Green `━━` | SPI MOSI / PWM 3.3V | Data & PWM from FPGA |
| 🟡 Yellow `━━` | SPI CS / Sense | Chip select, INA219 shunt |
| 🟣 Purple `━━` | I2C SDA | Data bus |
| 🟠 Orange `━━` | Servo signal 5V | Post-level-shift PWM to servos |
| 🩷 Pink `━━` | Alert GPIO | Buzzer, RGB LED |
| ⬜ Grey dashed `╌╌` | Config / tie | Address pin ties |

### 🎨 Module Colour Legend

| Module | Block | Pin (lighter) |
|--------|-------|---------------|
| Raspberry Pi 4B | `#3b82f6` 🟦 | `#93c5fd` |
| Tang Nano 9K FPGA | `#22c55e` 🟩 | `#86efac` |
| Level Shifters | `#14b8a6` 🟦 teal | `#5eead4` |
| DS3218 Servos | `#f97316` 🟧 | `#fdba74` |
| MPU9250 IMU | `#a855f7` 🟪 | `#d8b4fe` |
| INA219 Power | `#eab308` 🟨 | `#fde047` |
| Battery & Bucks | `#ef4444` 🟥 | `#fca5a5` |
| Buzzer & RGB LED | `#ec4899` 🩷 | `#f9a8d4` |
| GND / Bus | `#475569` ⬛ | `#94a3b8` |

---

## 1. Full System Overview

```mermaid
graph TB
    classDef rpi fill:#3b82f6,stroke:#1d4ed8,color:#fff,font-weight:bold
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f,font-size:11px
    classDef fpga fill:#22c55e,stroke:#15803d,color:#fff,font-weight:bold
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d,font-size:11px
    classDef servo fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12,font-size:11px
    classDef sensor fill:#a855f7,stroke:#7c3aed,color:#fff,font-weight:bold
    classDef sensorPin fill:#d8b4fe,stroke:#a855f7,color:#3b0764,font-size:11px
    classDef power fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef powerPin fill:#fca5a5,stroke:#ef4444,color:#7f1d1d,font-size:11px
    classDef levelshift fill:#14b8a6,stroke:#0f766e,color:#fff,font-weight:bold
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a,font-size:11px
    classDef alert fill:#ec4899,stroke:#be185d,color:#fff,font-weight:bold
    classDef alertPin fill:#f9a8d4,stroke:#ec4899,color:#831843,font-size:11px
    classDef bus fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef inaC fill:#eab308,stroke:#ca8a04,color:#fff,font-weight:bold

    subgraph POWER["⚡ POWER SYSTEM"]
        BATT["🔋 18650 3S Battery<br/>11.1V nominal"]:::power
        BMS["3S BMS<br/>10-20A"]:::powerPin
        FUSE["15A Blade Fuse"]:::powerPin
        TERM["Screw Terminal Block"]:::powerPin
        D1["1N5822 Diode 1"]:::powerPin
        D2["1N5822 Diode 2"]:::powerPin
        BUCK_S["XL4015 Buck<br/>→ 6.8V Servo Rail"]:::power
        BUCK_L["LM2596 Buck<br/>→ 5V Logic Rail"]:::power
    end

    subgraph CTRL["🎮 CONTROLLERS"]
        RPI["🍓 Raspberry Pi 4B<br/>4GB RAM"]:::rpi
        FPGA_MAIN["🟢 Tang Nano 9K<br/>GW1NR-9C"]:::fpga
    end

    subgraph SENSE["📡 SENSORS"]
        IMU_MAIN["🟣 MPU9250<br/>IMU"]:::sensor
        INA_MAIN["🟡 INA219<br/>Power Monitor"]:::inaC
    end

    subgraph ALERTS["🔔 ALERTS"]
        BUZ_MAIN["🔊 Buzzer"]:::alert
        RGB_MAIN["💡 RGB LED"]:::alert
    end

    subgraph LS_ALL["🔀 LEVEL SHIFTERS"]
        LS1_MAIN["LS1: Ch 0-3"]:::levelshift
        LS2_MAIN["LS2: Ch 4-7"]:::levelshift
        LS3_MAIN["LS3: Ch 8-11"]:::levelshift
    end

    subgraph SERVOS["🦿 12× DS3218 SERVOS"]
        S_FL["FL Leg: Hip/Thigh/Knee"]:::servo
        S_FR["FR Leg: Hip/Thigh/Knee"]:::servo
        S_RL["RL Leg: Hip/Thigh/Knee"]:::servo
        S_RR["RR Leg: Hip/Thigh/Knee"]:::servo
    end

    %% Power flow (links 0-8)
    BATT -->|"+"| BMS
    BMS -->|"+"| FUSE
    FUSE --> TERM
    TERM --> D1
    D1 --> BUCK_S
    TERM --> D2
    D2 --> BUCK_L
    BUCK_L -.->|"5V USB-C"| RPI
    BUCK_L -.->|"5V USB-C"| FPGA_MAIN

    %% Communication (links 9-13)
    RPI ==>|"SPI Bus"| FPGA_MAIN
    RPI -.->|"I2C Bus"| IMU_MAIN
    RPI -.->|"I2C Bus"| INA_MAIN
    RPI -->|"GPIO"| BUZ_MAIN
    RPI -->|"GPIO PWM"| RGB_MAIN

    %% PWM routing (links 14-22)
    FPGA_MAIN ==>|"PWM 0-3"| LS1_MAIN
    FPGA_MAIN ==>|"PWM 4-7"| LS2_MAIN
    FPGA_MAIN ==>|"PWM 8-11"| LS3_MAIN
    LS1_MAIN -->|"5V Signal"| S_FL
    LS1_MAIN -->|"5V Signal"| S_FR
    LS2_MAIN -->|"5V Signal"| S_FR
    LS2_MAIN -->|"5V Signal"| S_RL
    LS3_MAIN -->|"5V Signal"| S_RL
    LS3_MAIN -->|"5V Signal"| S_RR

    %% Servo power (links 23-26)
    BUCK_S ==>|"6.8V"| S_FL
    BUCK_S ==>|"6.8V"| S_FR
    BUCK_S ==>|"6.8V"| S_RL
    BUCK_S ==>|"6.8V"| S_RR

    %% INA219 shunt (link 27)
    INA_MAIN -.-|"Shunt Sense"| BUCK_S

    linkStyle 0,1,2,3,4,5,6 stroke:#ef4444,stroke-width:2px
    linkStyle 7,8 stroke:#ef4444,stroke-width:2px
    linkStyle 9 stroke:#3b82f6,stroke-width:3px
    linkStyle 10,11 stroke:#a855f7,stroke-width:2px
    linkStyle 12,13 stroke:#ec4899,stroke-width:2px
    linkStyle 14,15,16 stroke:#22c55e,stroke-width:3px
    linkStyle 17,18,19,20,21,22 stroke:#f97316,stroke-width:2px
    linkStyle 23,24,25,26 stroke:#ef4444,stroke-width:3px
    linkStyle 27 stroke:#eab308,stroke-width:2px
```
