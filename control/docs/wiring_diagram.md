# 🔌 VIGIL-RQ — Complete Wiring & Connection Diagram

> Pin-level wiring reference for every electronic connection on the VIGIL-RQ quadruped robot.
> All connection lines are colour-coded by signal type.

### 🎨 Wire Colour Legend

| Colour | Meaning | Hex |
|--------|---------|-----|
| 🔴 Red | VCC / Power positive | `#ef4444` |
| ⚫ Dark Grey | GND | `#475569` |
| 🔵 Blue | SPI clock / I2C SCL | `#3b82f6` |
| 🟢 Green | SPI MOSI / PWM signals | `#22c55e` |
| 🟡 Yellow | SPI CS / Chip Select | `#eab308` |
| 🟣 Purple | I2C SDA | `#a855f7` |
| 🟠 Orange | Servo signal (5V PWM) | `#f97316` |
| 🩷 Pink | Alert GPIO | `#ec4899` |
| ⬜ Teal | Level-shifted signal | `#14b8a6` |

---

## 1. Full System Overview

```mermaid
graph TB
    classDef rpi fill:#3b82f6,stroke:#1d4ed8,color:#fff,font-weight:bold
    classDef fpga fill:#22c55e,stroke:#15803d,color:#fff,font-weight:bold
    classDef servo fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef sensor fill:#a855f7,stroke:#7c3aed,color:#fff,font-weight:bold
    classDef power fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef ls fill:#14b8a6,stroke:#0f766e,color:#fff,font-weight:bold
    classDef alert fill:#ec4899,stroke:#be185d,color:#fff,font-weight:bold
    classDef bus fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef inaC fill:#eab308,stroke:#ca8a04,color:#fff,font-weight:bold

    BATT["🔋 18650 3S Battery<br/>11.1V"]:::power
    BUCK_S["XL4015 Buck → 6.8V"]:::power
    BUCK_L["LM2596 Buck → 5V"]:::power
    RPI["🍓 Raspberry Pi 4B"]:::rpi
    FPGA["🟢 Tang Nano 9K"]:::fpga
    IMU["🟣 MPU6050 IMU"]:::sensor
    INA["🟡 INA219"]:::inaC
    BUZ["🔊 Buzzer"]:::alert
    RGB["💡 RGB LED"]:::alert
    LS["🔀 3× Level Shifters"]:::ls
    SERVOS["🦿 12× DS3218 Servos"]:::servo
    GND_BUS["⏚ Common GND Bus"]:::bus

    BATT -->|"+11.1V"| BUCK_S
    BATT -->|"+11.1V"| BUCK_L
    BUCK_L -->|"5V USB-C"| RPI
    BUCK_L -->|"5V USB-C"| FPGA
    RPI -->|"SPI Bus"| FPGA
    RPI -->|"I2C SDA+SCL"| IMU
    RPI -->|"I2C SDA+SCL"| INA
    RPI -->|"GPIO 18"| BUZ
    RPI -->|"GPIO 17/27/22"| RGB
    FPGA -->|"12× PWM 3.3V"| LS
    LS -->|"12× PWM 5V"| SERVOS
    BUCK_S -->|"6.8V Power"| SERVOS
    INA -->|"Shunt Sense"| BUCK_S
    BATT --> GND_BUS
    RPI --> GND_BUS
    FPGA --> GND_BUS
    LS --> GND_BUS
    SERVOS --> GND_BUS
    IMU --> GND_BUS
    INA --> GND_BUS

    linkStyle 0 stroke:#ef4444,stroke-width:3px
    linkStyle 1 stroke:#ef4444,stroke-width:3px
    linkStyle 2 stroke:#ef4444,stroke-width:2px
    linkStyle 3 stroke:#ef4444,stroke-width:2px
    linkStyle 4 stroke:#3b82f6,stroke-width:3px
    linkStyle 5 stroke:#a855f7,stroke-width:2px
    linkStyle 6 stroke:#a855f7,stroke-width:2px
    linkStyle 7 stroke:#ec4899,stroke-width:2px
    linkStyle 8 stroke:#ec4899,stroke-width:2px
    linkStyle 9 stroke:#22c55e,stroke-width:3px
    linkStyle 10 stroke:#f97316,stroke-width:3px
    linkStyle 11 stroke:#ef4444,stroke-width:3px
    linkStyle 12 stroke:#eab308,stroke-width:2px
    linkStyle 13 stroke:#475569,stroke-width:2px
    linkStyle 14 stroke:#475569,stroke-width:2px
    linkStyle 15 stroke:#475569,stroke-width:2px
    linkStyle 16 stroke:#475569,stroke-width:2px
    linkStyle 17 stroke:#475569,stroke-width:2px
    linkStyle 18 stroke:#475569,stroke-width:2px
    linkStyle 19 stroke:#475569,stroke-width:2px
```

---

## 2. Power Distribution — Pin-Level Detail

```mermaid
graph LR
    classDef power fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef powerPin fill:#fca5a5,stroke:#ef4444,color:#7f1d1d
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff,font-weight:bold
    classDef gnd fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef load fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f

    subgraph BATTERY["🔋 18650 3S PACK"]
        BAT_POS["+ Positive 11.1V"]:::powerPin
        BAT_NEG["- Negative"]:::powerPin
    end

    subgraph BMS_BLOCK["🛡 3S BMS"]
        BMS_IN["B+ In"]:::powerPin
        BMS_OUT["P+ Out"]:::powerPin
    end

    subgraph FUSE_BLOCK["⚡ 15A FUSE"]
        FUSE_IN["In"]:::powerPin
        FUSE_OUT["Out"]:::powerPin
    end

    subgraph TERMINAL["📦 TERMINAL BLOCK"]
        T_V1["Out 1 → Servo Buck"]:::powerPin
        T_V2["Out 2 → Logic Buck"]:::powerPin
    end

    subgraph SERVO_BUCK["⬇ XL4015 — 6.8V"]
        BS_VIN["VIN"]:::powerPin
        BS_VOUT["VOUT 6.8V"]:::vcc
        BS_GND["GND"]:::gnd
    end

    subgraph LOGIC_BUCK["⬇ LM2596 — 5V"]
        BL_VIN["VIN"]:::powerPin
        BL_VOUT["VOUT 5V"]:::vcc
        BL_GND["GND"]:::gnd
    end

    subgraph LOADS["📤 LOADS"]
        RPI_PWR["RPi 4B USB-C"]:::load
        FPGA_PWR["FPGA USB-C"]:::load
        LS_PWR["Level Shifters HV"]:::load
        SERVO_PWR["12× Servos"]:::load
    end

    GND_STAR["⏚ COMMON GND"]:::gnd

    BAT_POS -->|"14AWG"| BMS_IN
    BMS_OUT -->|"14AWG"| FUSE_IN
    FUSE_OUT -->|"14AWG"| T_V1
    FUSE_OUT -->|"14AWG"| T_V2
    T_V1 -->|"16AWG"| BS_VIN
    T_V2 -->|"16AWG"| BL_VIN
    BS_VOUT -->|"18AWG"| SERVO_PWR
    BL_VOUT -->|"USB-C"| RPI_PWR
    BL_VOUT -->|"USB-C"| FPGA_PWR
    BL_VOUT -->|"22AWG"| LS_PWR

    BAT_NEG --> GND_STAR
    BS_GND --> GND_STAR
    BL_GND --> GND_STAR

    linkStyle 0 stroke:#ef4444,stroke-width:3px
    linkStyle 1 stroke:#ef4444,stroke-width:3px
    linkStyle 2 stroke:#ef4444,stroke-width:3px
    linkStyle 3 stroke:#ef4444,stroke-width:3px
    linkStyle 4 stroke:#ef4444,stroke-width:2px
    linkStyle 5 stroke:#ef4444,stroke-width:2px
    linkStyle 6 stroke:#ef4444,stroke-width:3px
    linkStyle 7 stroke:#ef4444,stroke-width:2px
    linkStyle 8 stroke:#ef4444,stroke-width:2px
    linkStyle 9 stroke:#ef4444,stroke-width:2px
    linkStyle 10 stroke:#475569,stroke-width:3px
    linkStyle 11 stroke:#475569,stroke-width:2px
    linkStyle 12 stroke:#475569,stroke-width:2px
```

---

## 3. SPI Bus — Raspberry Pi ↔ Tang Nano 9K

```mermaid
graph LR
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph RPI_SPI["🍓 RASPBERRY PI 4B — SPI0"]
        R_SCLK["GPIO 11 · Pin 23<br/>SPI0_SCLK"]:::rpiPin
        R_MOSI["GPIO 10 · Pin 19<br/>SPI0_MOSI"]:::rpiPin
        R_CE0["GPIO 8 · Pin 24<br/>SPI0_CE0"]:::rpiPin
        R_GND["GND · Pin 25"]:::gnd
    end

    subgraph FPGA_SPI["🟢 TANG NANO 9K — SPI SLAVE"]
        F_SCLK["Pin 25<br/>spi_sclk"]:::fpgaPin
        F_MOSI["Pin 26<br/>spi_mosi"]:::fpgaPin
        F_CS["Pin 27<br/>spi_cs_n"]:::fpgaPin
        F_GND["GND"]:::gnd
    end

    R_SCLK -->|"SCLK · 22AWG"| F_SCLK
    R_MOSI -->|"MOSI · 22AWG"| F_MOSI
    R_CE0 -->|"CS · 22AWG"| F_CS
    R_GND -->|"GND · 22AWG"| F_GND

    linkStyle 0 stroke:#3b82f6,stroke-width:3px
    linkStyle 1 stroke:#22c55e,stroke-width:3px
    linkStyle 2 stroke:#eab308,stroke-width:3px
    linkStyle 3 stroke:#475569,stroke-width:3px

    style RPI_SPI fill:#1e3a5f,stroke:#3b82f6,color:#93c5fd
    style FPGA_SPI fill:#14532d,stroke:#22c55e,color:#86efac
```

> [!IMPORTANT]
> Both RPi SPI0 and Tang Nano 9K run at **3.3V logic** — no level shifter needed on the SPI bus. SPI Mode 0 (CPOL=0, CPHA=0), Clock: 1 MHz, Frame: 3 bytes per servo command.

---

## 4. I2C Bus — Raspberry Pi ↔ IMU + INA219

```mermaid
graph LR
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef imuPin fill:#d8b4fe,stroke:#a855f7,color:#3b0764
    classDef inaPin fill:#fde047,stroke:#eab308,color:#713f12
    classDef gnd fill:#475569,stroke:#334155,color:#fff
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff

    subgraph RPI_I2C["🍓 RASPBERRY PI 4B — I2C1"]
        R_SDA["GPIO 2 · Pin 3<br/>I2C1_SDA"]:::rpiPin
        R_SCL["GPIO 3 · Pin 5<br/>I2C1_SCL"]:::rpiPin
        R_3V3["3.3V · Pin 1"]:::vcc
        R_GND_I["GND · Pin 9"]:::gnd
    end

    subgraph IMU_BLK["🟣 MPU6050 — Addr 0x68"]
        I_SDA["SDA"]:::imuPin
        I_SCL["SCL"]:::imuPin
        I_VCC["VCC"]:::imuPin
        I_GND["GND"]:::imuPin
        I_AD0["AD0 → GND"]:::imuPin
    end

    subgraph INA_BLK["🟡 INA219 — Addr 0x40"]
        N_SDA["SDA"]:::inaPin
        N_SCL["SCL"]:::inaPin
        N_VCC["VCC"]:::inaPin
        N_GND["GND"]:::inaPin
        N_VP["VIN+"]:::inaPin
        N_VN["VIN-"]:::inaPin
    end

    R_SDA -->|"SDA"| I_SDA
    R_SDA -->|"SDA"| N_SDA
    R_SCL -->|"SCL"| I_SCL
    R_SCL -->|"SCL"| N_SCL
    R_3V3 -->|"3.3V"| I_VCC
    R_3V3 -->|"3.3V"| N_VCC
    R_GND_I -->|"GND"| I_GND
    R_GND_I -->|"GND"| N_GND
    I_AD0 -.->|"Tie low"| I_GND

    linkStyle 0 stroke:#a855f7,stroke-width:3px
    linkStyle 1 stroke:#a855f7,stroke-width:3px
    linkStyle 2 stroke:#3b82f6,stroke-width:3px
    linkStyle 3 stroke:#3b82f6,stroke-width:3px
    linkStyle 4 stroke:#ef4444,stroke-width:2px
    linkStyle 5 stroke:#ef4444,stroke-width:2px
    linkStyle 6 stroke:#475569,stroke-width:2px
    linkStyle 7 stroke:#475569,stroke-width:2px
    linkStyle 8 stroke:#475569,stroke-width:1px,stroke-dasharray:5

    style RPI_I2C fill:#1e3a5f,stroke:#3b82f6,color:#93c5fd
    style IMU_BLK fill:#3b0764,stroke:#a855f7,color:#d8b4fe
    style INA_BLK fill:#713f12,stroke:#eab308,color:#fde047
```

> [!NOTE]
> **I2C pull-ups:** RPi 4B has built-in 1.8kΩ pull-ups. Most breakout boards add their own. If using bare ICs, add **4.7kΩ pull-ups to 3.3V** on SDA and SCL.

---

## 5. PWM — FPGA → Level Shifter 1 → Front Left + FR Hip

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_LS1["🟢 FPGA — Channels 0-3"]
        F28["Pin 28 · pwm 0"]:::fpgaPin
        F29["Pin 29 · pwm 1"]:::fpgaPin
        F30["Pin 30 · pwm 2"]:::fpgaPin
        F31["Pin 31 · pwm 3"]:::fpgaPin
    end

    subgraph LS1_BLK["🔀 LEVEL SHIFTER 1"]
        L1_LV["LV: 3.3V"]:::vcc
        L1_HV["HV: 5V"]:::vcc
        L1_GND["GND"]:::gnd
        L1_A["LV1 → HV1"]:::lsPin
        L1_B["LV2 → HV2"]:::lsPin
        L1_C["LV3 → HV3"]:::lsPin
        L1_D["LV4 → HV4"]:::lsPin
    end

    subgraph SRV_LS1["🦿 SERVOS"]
        S0["DS3218 #0 · FL Hip"]:::servoPin
        S1["DS3218 #1 · FL Thigh"]:::servoPin
        S2["DS3218 #2 · FL Knee"]:::servoPin
        S3["DS3218 #3 · FR Hip"]:::servoPin
    end

    F28 -->|"3.3V PWM"| L1_A
    F29 -->|"3.3V PWM"| L1_B
    F30 -->|"3.3V PWM"| L1_C
    F31 -->|"3.3V PWM"| L1_D
    L1_A -->|"5V Signal"| S0
    L1_B -->|"5V Signal"| S1
    L1_C -->|"5V Signal"| S2
    L1_D -->|"5V Signal"| S3

    linkStyle 0 stroke:#22c55e,stroke-width:2px
    linkStyle 1 stroke:#22c55e,stroke-width:2px
    linkStyle 2 stroke:#22c55e,stroke-width:2px
    linkStyle 3 stroke:#22c55e,stroke-width:2px
    linkStyle 4 stroke:#f97316,stroke-width:3px
    linkStyle 5 stroke:#f97316,stroke-width:3px
    linkStyle 6 stroke:#f97316,stroke-width:3px
    linkStyle 7 stroke:#f97316,stroke-width:3px

    style FPGA_LS1 fill:#14532d,stroke:#22c55e,color:#86efac
    style LS1_BLK fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style SRV_LS1 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

## 6. PWM — FPGA → Level Shifter 2 → FR Thigh/Knee + RL Hip/Thigh

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_LS2["🟢 FPGA — Channels 4-7"]
        F32["Pin 32 · pwm 4"]:::fpgaPin
        F33["Pin 33 · pwm 5"]:::fpgaPin
        F34["Pin 34 · pwm 6"]:::fpgaPin
        F35["Pin 35 · pwm 7"]:::fpgaPin
    end

    subgraph LS2_BLK["🔀 LEVEL SHIFTER 2"]
        L2_LV["LV: 3.3V"]:::vcc
        L2_HV["HV: 5V"]:::vcc
        L2_GND["GND"]:::gnd
        L2_A["LV1 → HV1"]:::lsPin
        L2_B["LV2 → HV2"]:::lsPin
        L2_C["LV3 → HV3"]:::lsPin
        L2_D["LV4 → HV4"]:::lsPin
    end

    subgraph SRV_LS2["🦿 SERVOS"]
        S4["DS3218 #4 · FR Thigh"]:::servoPin
        S5["DS3218 #5 · FR Knee"]:::servoPin
        S6["DS3218 #6 · RL Hip"]:::servoPin
        S7["DS3218 #7 · RL Thigh"]:::servoPin
    end

    F32 -->|"3.3V PWM"| L2_A
    F33 -->|"3.3V PWM"| L2_B
    F34 -->|"3.3V PWM"| L2_C
    F35 -->|"3.3V PWM"| L2_D
    L2_A -->|"5V Signal"| S4
    L2_B -->|"5V Signal"| S5
    L2_C -->|"5V Signal"| S6
    L2_D -->|"5V Signal"| S7

    linkStyle 0 stroke:#22c55e,stroke-width:2px
    linkStyle 1 stroke:#22c55e,stroke-width:2px
    linkStyle 2 stroke:#22c55e,stroke-width:2px
    linkStyle 3 stroke:#22c55e,stroke-width:2px
    linkStyle 4 stroke:#f97316,stroke-width:3px
    linkStyle 5 stroke:#f97316,stroke-width:3px
    linkStyle 6 stroke:#f97316,stroke-width:3px
    linkStyle 7 stroke:#f97316,stroke-width:3px

    style FPGA_LS2 fill:#14532d,stroke:#22c55e,color:#86efac
    style LS2_BLK fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style SRV_LS2 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

## 7. PWM — FPGA → Level Shifter 3 → RL Knee + RR Leg

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_LS3["🟢 FPGA — Channels 8-11"]
        F40["Pin 40 · pwm 8"]:::fpgaPin
        F41["Pin 41 · pwm 9"]:::fpgaPin
        F42["Pin 42 · pwm 10"]:::fpgaPin
        F48["Pin 48 · pwm 11"]:::fpgaPin
    end

    subgraph LS3_BLK["🔀 LEVEL SHIFTER 3"]
        L3_LV["LV: 3.3V"]:::vcc
        L3_HV["HV: 5V"]:::vcc
        L3_GND["GND"]:::gnd
        L3_A["LV1 → HV1"]:::lsPin
        L3_B["LV2 → HV2"]:::lsPin
        L3_C["LV3 → HV3"]:::lsPin
        L3_D["LV4 → HV4"]:::lsPin
    end

    subgraph SRV_LS3["🦿 SERVOS"]
        S8["DS3218 #8 · RL Knee"]:::servoPin
        S9["DS3218 #9 · RR Hip"]:::servoPin
        S10["DS3218 #10 · RR Thigh"]:::servoPin
        S11["DS3218 #11 · RR Knee"]:::servoPin
    end

    F40 -->|"3.3V PWM"| L3_A
    F41 -->|"3.3V PWM"| L3_B
    F42 -->|"3.3V PWM"| L3_C
    F48 -->|"3.3V PWM"| L3_D
    L3_A -->|"5V Signal"| S8
    L3_B -->|"5V Signal"| S9
    L3_C -->|"5V Signal"| S10
    L3_D -->|"5V Signal"| S11

    linkStyle 0 stroke:#22c55e,stroke-width:2px
    linkStyle 1 stroke:#22c55e,stroke-width:2px
    linkStyle 2 stroke:#22c55e,stroke-width:2px
    linkStyle 3 stroke:#22c55e,stroke-width:2px
    linkStyle 4 stroke:#f97316,stroke-width:3px
    linkStyle 5 stroke:#f97316,stroke-width:3px
    linkStyle 6 stroke:#f97316,stroke-width:3px
    linkStyle 7 stroke:#f97316,stroke-width:3px

    style FPGA_LS3 fill:#14532d,stroke:#22c55e,color:#86efac
    style LS3_BLK fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style SRV_LS3 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## 8. GPIO — Buzzer + RGB LED

```mermaid
graph LR
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef alertPin fill:#f9a8d4,stroke:#ec4899,color:#831843
    classDef gnd fill:#475569,stroke:#334155,color:#fff
    classDef res fill:#78716c,stroke:#57534e,color:#fff

    subgraph RPI_GPIO["🍓 RASPBERRY PI 4B"]
        G18["GPIO 18 · Pin 12<br/>Buzzer PWM"]:::rpiPin
        G17["GPIO 17 · Pin 11<br/>Red"]:::rpiPin
        G27["GPIO 27 · Pin 13<br/>Green"]:::rpiPin
        G22["GPIO 22 · Pin 15<br/>Blue"]:::rpiPin
        GG["GND · Pin 14"]:::gnd
    end

    subgraph RESISTORS["🔧 220Ω RESISTORS"]
        R1["R1 220Ω"]:::res
        R2["R2 220Ω"]:::res
        R3["R3 220Ω"]:::res
    end

    subgraph BUZZER_B["🔊 ACTIVE BUZZER"]
        BUZ_P["Signal +"]:::alertPin
        BUZ_N["GND -"]:::alertPin
    end

    subgraph RGB_B["💡 RGB LED — Common Cathode"]
        RGB_R["Red Anode"]:::alertPin
        RGB_G["Green Anode"]:::alertPin
        RGB_BL["Blue Anode"]:::alertPin
        RGB_K["Common Cathode"]:::alertPin
    end

    G18 -->|"PWM"| BUZ_P
    BUZ_N -->|"GND"| GG
    G17 -->|"PWM"| R1
    R1 --> RGB_R
    G27 -->|"PWM"| R2
    R2 --> RGB_G
    G22 -->|"PWM"| R3
    R3 --> RGB_BL
    RGB_K -->|"GND"| GG

    linkStyle 0 stroke:#ec4899,stroke-width:3px
    linkStyle 1 stroke:#475569,stroke-width:2px
    linkStyle 2 stroke:#ef4444,stroke-width:2px
    linkStyle 3 stroke:#ef4444,stroke-width:2px
    linkStyle 4 stroke:#22c55e,stroke-width:2px
    linkStyle 5 stroke:#22c55e,stroke-width:2px
    linkStyle 6 stroke:#3b82f6,stroke-width:2px
    linkStyle 7 stroke:#3b82f6,stroke-width:2px
    linkStyle 8 stroke:#475569,stroke-width:2px

    style RPI_GPIO fill:#1e3a5f,stroke:#3b82f6,color:#93c5fd
    style BUZZER_B fill:#831843,stroke:#ec4899,color:#f9a8d4
    style RGB_B fill:#831843,stroke:#ec4899,color:#f9a8d4
    style RESISTORS fill:#292524,stroke:#78716c,color:#d6d3d1
```

---

## 9. Servo Power — 6.8V Rail to All 12 DS3218 Servos

```mermaid
graph LR
    classDef rail fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef railGnd fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12

    RAIL_P["+6.8V Rail<br/>XL4015 Output"]:::rail
    RAIL_G["GND Rail"]:::railGnd

    subgraph FL["🦿 FRONT LEFT"]
        FL0["FL Hip · Red wire"]:::servoPin
        FL1["FL Thigh · Red wire"]:::servoPin
        FL2["FL Knee · Red wire"]:::servoPin
        FL0G["FL Hip · Brown wire"]:::servoPin
        FL1G["FL Thigh · Brown wire"]:::servoPin
        FL2G["FL Knee · Brown wire"]:::servoPin
    end

    subgraph FR["🦿 FRONT RIGHT"]
        FR0["FR Hip · Red"]:::servoPin
        FR1["FR Thigh · Red"]:::servoPin
        FR2["FR Knee · Red"]:::servoPin
        FR0G["FR Hip · Brown"]:::servoPin
        FR1G["FR Thigh · Brown"]:::servoPin
        FR2G["FR Knee · Brown"]:::servoPin
    end

    subgraph RL["🦿 REAR LEFT"]
        RL0["RL Hip · Red"]:::servoPin
        RL1["RL Thigh · Red"]:::servoPin
        RL2["RL Knee · Red"]:::servoPin
        RL0G["RL Hip · Brown"]:::servoPin
        RL1G["RL Thigh · Brown"]:::servoPin
        RL2G["RL Knee · Brown"]:::servoPin
    end

    subgraph RR["🦿 REAR RIGHT"]
        RR0["RR Hip · Red"]:::servoPin
        RR1["RR Thigh · Red"]:::servoPin
        RR2["RR Knee · Red"]:::servoPin
        RR0G["RR Hip · Brown"]:::servoPin
        RR1G["RR Thigh · Brown"]:::servoPin
        RR2G["RR Knee · Brown"]:::servoPin
    end

    RAIL_P --> FL0 & FL1 & FL2
    RAIL_P --> FR0 & FR1 & FR2
    RAIL_P --> RL0 & RL1 & RL2
    RAIL_P --> RR0 & RR1 & RR2
    RAIL_G --> FL0G & FL1G & FL2G
    RAIL_G --> FR0G & FR1G & FR2G
    RAIL_G --> RL0G & RL1G & RL2G
    RAIL_G --> RR0G & RR1G & RR2G

    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11 stroke:#ef4444,stroke-width:2px
    linkStyle 12,13,14,15,16,17,18,19,20,21,22,23 stroke:#475569,stroke-width:2px

    style FL fill:#7c2d12,stroke:#f97316,color:#fdba74
    style FR fill:#7c2d12,stroke:#f97316,color:#fdba74
    style RL fill:#7c2d12,stroke:#f97316,color:#fdba74
    style RR fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## 10. INA219 — Shunt Resistor Placement

```mermaid
graph LR
    classDef power fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef inaPin fill:#fde047,stroke:#eab308,color:#713f12
    classDef servo fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold

    BUCK["+6.8V<br/>XL4015 Out"]:::power
    VIN_P["INA219 VIN+"]:::inaPin
    SHUNT["0.1Ω Shunt<br/>Resistor"]:::inaPin
    VIN_N["INA219 VIN-"]:::inaPin
    DIST["Servo Power<br/>Distribution"]:::servo

    BUCK -->|"+6.8V"| VIN_P
    VIN_P --> SHUNT
    SHUNT --> VIN_N
    VIN_N -->|"To servos"| DIST

    linkStyle 0 stroke:#ef4444,stroke-width:3px
    linkStyle 1 stroke:#eab308,stroke-width:3px
    linkStyle 2 stroke:#eab308,stroke-width:3px
    linkStyle 3 stroke:#ef4444,stroke-width:3px
```

> [!TIP]
> The 0.1Ω shunt is wired **in series** on the positive servo rail. The INA219 measures voltage drop across it to calculate total servo current. Place it between the XL4015 output and the servo distribution terminal.

---

## 11. Common Ground — Star Topology

```mermaid
graph TB
    classDef gnd fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef imuPin fill:#d8b4fe,stroke:#a855f7,color:#3b0764
    classDef inaPin fill:#fde047,stroke:#eab308,color:#713f12
    classDef alertPin fill:#f9a8d4,stroke:#ec4899,color:#831843
    classDef powerPin fill:#fca5a5,stroke:#ef4444,color:#7f1d1d

    GND_HUB["⏚ COMMON GROUND<br/>STAR POINT<br/>Terminal Block"]:::gnd

    BAT_G["Battery -"]:::powerPin
    BUCKS_G["XL4015 GND"]:::powerPin
    BUCKL_G["LM2596 GND"]:::powerPin
    RPI_G["RPi 4B GND<br/>Pin 6/9/14/20/25"]:::rpiPin
    FPGA_G["Tang Nano 9K GND"]:::fpgaPin
    LS1_G["Level Shifter 1 GND"]:::lsPin
    LS2_G["Level Shifter 2 GND"]:::lsPin
    LS3_G["Level Shifter 3 GND"]:::lsPin
    SRV_G["12× Servo Brown Wire"]:::servoPin
    IMU_G["MPU6050 GND"]:::imuPin
    INA_G["INA219 GND"]:::inaPin
    BUZ_G["Buzzer GND"]:::alertPin
    RGB_G["RGB LED Cathode"]:::alertPin

    GND_HUB --- BAT_G
    GND_HUB --- BUCKS_G
    GND_HUB --- BUCKL_G
    GND_HUB --- RPI_G
    GND_HUB --- FPGA_G
    GND_HUB --- LS1_G
    GND_HUB --- LS2_G
    GND_HUB --- LS3_G
    GND_HUB --- SRV_G
    GND_HUB --- IMU_G
    GND_HUB --- INA_G
    GND_HUB --- BUZ_G
    GND_HUB --- RGB_G

    linkStyle 0 stroke:#475569,stroke-width:3px
    linkStyle 1 stroke:#475569,stroke-width:3px
    linkStyle 2 stroke:#475569,stroke-width:3px
    linkStyle 3 stroke:#475569,stroke-width:3px
    linkStyle 4 stroke:#475569,stroke-width:3px
    linkStyle 5 stroke:#475569,stroke-width:2px
    linkStyle 6 stroke:#475569,stroke-width:2px
    linkStyle 7 stroke:#475569,stroke-width:2px
    linkStyle 8 stroke:#475569,stroke-width:3px
    linkStyle 9 stroke:#475569,stroke-width:2px
    linkStyle 10 stroke:#475569,stroke-width:2px
    linkStyle 11 stroke:#475569,stroke-width:2px
    linkStyle 12 stroke:#475569,stroke-width:2px
```

> [!CAUTION]
> **Ground loops cause servo jitter and SPI errors.** Use a **star ground topology** — all GND wires converge at a single point on the terminal block, not daisy-chained. Use **14 AWG** for main ground, **16 AWG** for buck GNDs, **22 AWG** for signal GNDs.

---

## 12. Complete Pin Reference Tables

### Raspberry Pi 4B — All Used GPIO Pins

| BCM GPIO | Physical Pin | Function | Wire Colour | Connects To | Gauge |
|----------|-------------|----------|-------------|-------------|-------|
| GPIO 2 | 3 | I2C1 SDA | 🟣 Purple | IMU SDA + INA219 SDA | 22 AWG |
| GPIO 3 | 5 | I2C1 SCL | 🔵 Blue | IMU SCL + INA219 SCL | 22 AWG |
| GPIO 8 | 24 | SPI0 CE0 | 🟡 Yellow | FPGA Pin 27 (CS) | 22 AWG |
| GPIO 10 | 19 | SPI0 MOSI | 🟢 Green | FPGA Pin 26 (MOSI) | 22 AWG |
| GPIO 11 | 23 | SPI0 SCLK | 🔵 Blue | FPGA Pin 25 (SCLK) | 22 AWG |
| GPIO 17 | 11 | RGB Red | 🔴 Red | 220Ω → LED Red | 24 AWG |
| GPIO 18 | 12 | Buzzer PWM | 🟠 Orange | Active buzzer + | 24 AWG |
| GPIO 22 | 15 | RGB Blue | 🔵 Blue | 220Ω → LED Blue | 24 AWG |
| GPIO 27 | 13 | RGB Green | 🟢 Green | 220Ω → LED Green | 24 AWG |
| 3.3V | 1, 17 | Power out | 🔴 Red | IMU/INA VCC, LS LV | 22 AWG |
| 5V | 2, 4 | Power in | 🔴 Red | From LM2596 USB-C | — |
| GND | 6,9,14,20,25 | Ground | ⚫ Black | Common ground bus | 16 AWG |

### Tang Nano 9K — All Used Pins

| FPGA Pin | Signal | Dir | Connects To | Wire Colour |
|----------|--------|-----|-------------|-------------|
| 52 | clk_27m | In | On-board oscillator | — (internal) |
| 3 | btn_rst_n | In | On-board S1 button | — (internal) |
| 25 | spi_sclk | In | RPi GPIO 11 | 🔵 Blue |
| 26 | spi_mosi | In | RPi GPIO 10 | 🟢 Green |
| 27 | spi_cs_n | In | RPi GPIO 8 | 🟡 Yellow |
| 28 | pwm_out[0] | Out | LS1 LV1 → FL Hip | 🟢 Green |
| 29 | pwm_out[1] | Out | LS1 LV2 → FL Thigh | 🟢 Green |
| 30 | pwm_out[2] | Out | LS1 LV3 → FL Knee | 🟢 Green |
| 31 | pwm_out[3] | Out | LS1 LV4 → FR Hip | 🟢 Green |
| 32 | pwm_out[4] | Out | LS2 LV1 → FR Thigh | 🟢 Green |
| 33 | pwm_out[5] | Out | LS2 LV2 → FR Knee | 🟢 Green |
| 34 | pwm_out[6] | Out | LS2 LV3 → RL Hip | 🟢 Green |
| 35 | pwm_out[7] | Out | LS2 LV4 → RL Thigh | 🟢 Green |
| 40 | pwm_out[8] | Out | LS3 LV1 → RL Knee | 🟢 Green |
| 41 | pwm_out[9] | Out | LS3 LV2 → RR Hip | 🟢 Green |
| 42 | pwm_out[10] | Out | LS3 LV3 → RR Thigh | 🟢 Green |
| 48 | pwm_out[11] | Out | LS3 LV4 → RR Knee | 🟢 Green |
| 10–16 | led[0:5] | Out | On-board LEDs | — (internal) |

---

## 🔧 Assembly Checklist

- [ ] Solder battery tabs to 18650 3S pack
- [ ] Connect battery → BMS → fuse → terminal block (🔴 14 AWG)
- [ ] Mount 1N5822 diodes on terminal block outputs
- [ ] Wire XL4015 buck — **adjust trimpot to 6.8V before connecting servos!**
- [ ] Wire LM2596 buck — **adjust trimpot to 5.0V before connecting RPi!**
- [ ] Connect all GND wires to star ground point (⚫ 14–16 AWG)
- [ ] Wire 3× level shifters: LV=3.3V, HV=5V
- [ ] Connect 12× FPGA PWM → level shifter LV inputs (🟢 22 AWG)
- [ ] Connect 12× level shifter HV → servo signal wires (🟠 22 AWG)
- [ ] Connect 12× servo red wire to 6.8V rail (🔴 18 AWG pairs)
- [ ] Connect 12× servo brown wire to GND bus (⚫ 18 AWG)
- [ ] Wire SPI: GPIO 8/10/11 → FPGA 25/26/27 (🔵🟢🟡 22 AWG, keep short!)
- [ ] Wire I2C: GPIO 2/3 → IMU + INA219 SDA/SCL (🟣🔵 22 AWG)
- [ ] Place INA219 shunt in series on +6.8V servo rail
- [ ] Wire buzzer: GPIO 18 → buzzer +, buzzer - → GND (🟠 24 AWG)
- [ ] Wire RGB: GPIO 17/27/22 → 220Ω → R/G/B, cathode → GND (24 AWG)
- [ ] Apply heat shrink (1cm, 2cm) to ALL solder joints
- [ ] **Verify all voltages with multimeter BEFORE powering on RPi/FPGA**
