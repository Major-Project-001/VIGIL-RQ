# 🟢 PWM Outputs — FPGA → Level Shifters → Servos

> Part of [VIGIL-RQ Wiring Documentation](wiring_diagram.md)

---

## Leg Orientation — Top View

Use this diagram to identify which leg is **FR, FL, RL, RR** when looking down at the robot from above:

```mermaid
graph TB
    classDef body fill:#1e293b,stroke:#475569,color:#e2e8f0,font-weight:bold
    classDef front fill:#3b82f6,stroke:#1d4ed8,color:#fff,font-weight:bold
    classDef rear fill:#475569,stroke:#334155,color:#fff,font-weight:bold
    classDef legFL fill:#22c55e,stroke:#15803d,color:#fff,font-weight:bold
    classDef legFR fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef legRL fill:#a855f7,stroke:#7c3aed,color:#fff,font-weight:bold
    classDef legRR fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef dir fill:#0f172a,stroke:#334155,color:#94a3b8,font-size:11px

    FRONT["⬆ FRONT"]:::front

    FL["🟢 FL<br/>Front Left<br/>Ch 0,1,2"]:::legFL
    FR["🟠 FR<br/>Front Right<br/>Ch 3,4,5"]:::legFR

    BODY["🐕 VIGIL-RQ<br/>Top View"]:::body

    RL["🟣 RL<br/>Rear Left<br/>Ch 6,7,8"]:::legRL
    RR["🔴 RR<br/>Rear Right<br/>Ch 9,10,11"]:::legRR

    REAR["⬇ REAR"]:::rear

    FRONT --- FL
    FRONT --- FR
    FL --- BODY
    FR --- BODY
    BODY --- RL
    BODY --- RR
    RL --- REAR
    RR --- REAR

    linkStyle 0,2 stroke:#22c55e,stroke-width:2px
    linkStyle 1,3 stroke:#f97316,stroke-width:2px
    linkStyle 4,6 stroke:#a855f7,stroke-width:2px
    linkStyle 5,7 stroke:#ef4444,stroke-width:2px
```

### Joint Naming Convention (per leg)

Each leg has **3 joints**, numbered from body outward:

| Joint | Position | Range of Motion | Neutral (µs) |
|-------|----------|-----------------|---------------|
| **Hip** | Shoulder pivot (left/right swing) | ±30° | 1500 |
| **Thigh** | Upper leg (forward/back) | ±60° | 1500 |
| **Knee** | Lower leg (bend) | ±90° | 1500 |

### DS3218 PWM Specifications

| Parameter | Value |
|-----------|-------|
| PWM Frequency | 50 Hz (20 ms period) |
| Minimum pulse | 500 µs (full CW) |
| Neutral pulse | 1500 µs (center position) |
| Maximum pulse | 2500 µs (full CCW) |
| Operating voltage | 6.0–7.4V (we use 6.8V) |
| Stall torque @ 6.8V | ~20 kg·cm |
| Signal logic | 5V (via level shifter from 3.3V FPGA) |

---

## All 12 Channels — Overview

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_PWM["🟢 TANG NANO 9K — PWM OUTPUTS"]
        F0["Pin 28<br/>pwm_out 0"]:::fpgaPin
        F1["Pin 29<br/>pwm_out 1"]:::fpgaPin
        F2["Pin 30<br/>pwm_out 2"]:::fpgaPin
        F3["Pin 31<br/>pwm_out 3"]:::fpgaPin
        F4["Pin 32<br/>pwm_out 4"]:::fpgaPin
        F5["Pin 33<br/>pwm_out 5"]:::fpgaPin
        F6["Pin 34<br/>pwm_out 6"]:::fpgaPin
        F7["Pin 35<br/>pwm_out 7"]:::fpgaPin
        F8["Pin 40<br/>pwm_out 8"]:::fpgaPin
        F9["Pin 41<br/>pwm_out 9"]:::fpgaPin
        F10["Pin 42<br/>pwm_out 10"]:::fpgaPin
        F11["Pin 48<br/>pwm_out 11"]:::fpgaPin
        F_3V3["3.3V"]:::vcc
        F_GND["GND"]:::gnd
    end

    subgraph LS1["🔀 LEVEL SHIFTER 1"]
        LS1_LV["LV: 3.3V"]:::lsPin
        LS1_HV["HV: 5V"]:::lsPin
        LS1_GND["GND"]:::gnd
        LS1_A1["LV1 → HV1"]:::lsPin
        LS1_A2["LV2 → HV2"]:::lsPin
        LS1_A3["LV3 → HV3"]:::lsPin
        LS1_A4["LV4 → HV4"]:::lsPin
    end

    subgraph LS2["🔀 LEVEL SHIFTER 2"]
        LS2_LV["LV: 3.3V"]:::lsPin
        LS2_HV["HV: 5V"]:::lsPin
        LS2_GND["GND"]:::gnd
        LS2_A1["LV1 → HV1"]:::lsPin
        LS2_A2["LV2 → HV2"]:::lsPin
        LS2_A3["LV3 → HV3"]:::lsPin
        LS2_A4["LV4 → HV4"]:::lsPin
    end

    subgraph LS3["🔀 LEVEL SHIFTER 3"]
        LS3_LV["LV: 3.3V"]:::lsPin
        LS3_HV["HV: 5V"]:::lsPin
        LS3_GND["GND"]:::gnd
        LS3_A1["LV1 → HV1"]:::lsPin
        LS3_A2["LV2 → HV2"]:::lsPin
        LS3_A3["LV3 → HV3"]:::lsPin
        LS3_A4["LV4 → HV4"]:::lsPin
    end

    subgraph FL_LEG["🦿 FRONT LEFT LEG"]
        FL_H["DS3218 #0<br/>FL Hip · Signal"]:::servoPin
        FL_T["DS3218 #1<br/>FL Thigh · Signal"]:::servoPin
        FL_K["DS3218 #2<br/>FL Knee · Signal"]:::servoPin
    end

    subgraph FR_LEG["🦿 FRONT RIGHT LEG"]
        FR_H["DS3218 #3<br/>FR Hip · Signal"]:::servoPin
        FR_T["DS3218 #4<br/>FR Thigh · Signal"]:::servoPin
        FR_K["DS3218 #5<br/>FR Knee · Signal"]:::servoPin
    end

    subgraph RL_LEG["🦿 REAR LEFT LEG"]
        RL_H["DS3218 #6<br/>RL Hip · Signal"]:::servoPin
        RL_T["DS3218 #7<br/>RL Thigh · Signal"]:::servoPin
        RL_K["DS3218 #8<br/>RL Knee · Signal"]:::servoPin
    end

    subgraph RR_LEG["🦿 REAR RIGHT LEG"]
        RR_H["DS3218 #9<br/>RR Hip · Signal"]:::servoPin
        RR_T["DS3218 #10<br/>RR Thigh · Signal"]:::servoPin
        RR_K["DS3218 #11<br/>RR Knee · Signal"]:::servoPin
    end

    %% FPGA → LS1 Ch 0-3 (links 0-3)
    F0 -->|"Ch0 3.3V"| LS1_A1
    F1 -->|"Ch1 3.3V"| LS1_A2
    F2 -->|"Ch2 3.3V"| LS1_A3
    F3 -->|"Ch3 3.3V"| LS1_A4

    %% FPGA → LS2 Ch 4-7 (links 4-7)
    F4 -->|"Ch4 3.3V"| LS2_A1
    F5 -->|"Ch5 3.3V"| LS2_A2
    F6 -->|"Ch6 3.3V"| LS2_A3
    F7 -->|"Ch7 3.3V"| LS2_A4

    %% FPGA → LS3 Ch 8-11 (links 8-11)
    F8 -->|"Ch8 3.3V"| LS3_A1
    F9 -->|"Ch9 3.3V"| LS3_A2
    F10 -->|"Ch10 3.3V"| LS3_A3
    F11 -->|"Ch11 3.3V"| LS3_A4

    %% LS1 → Servos 5V (links 12-15)
    LS1_A1 ==>|"5V Signal"| FL_H
    LS1_A2 ==>|"5V Signal"| FL_T
    LS1_A3 ==>|"5V Signal"| FL_K
    LS1_A4 ==>|"5V Signal"| FR_H

    %% LS2 → Servos 5V (links 16-19)
    LS2_A1 ==>|"5V Signal"| FR_T
    LS2_A2 ==>|"5V Signal"| FR_K
    LS2_A3 ==>|"5V Signal"| RL_H
    LS2_A4 ==>|"5V Signal"| RL_T

    %% LS3 → Servos 5V (links 20-23)
    LS3_A1 ==>|"5V Signal"| RL_K
    LS3_A2 ==>|"5V Signal"| RR_H
    LS3_A3 ==>|"5V Signal"| RR_T
    LS3_A4 ==>|"5V Signal"| RR_K

    %% Level shifter LV power (links 24-26)
    F_3V3 -.->|"LV Ref"| LS1_LV
    F_3V3 -.->|"LV Ref"| LS2_LV
    F_3V3 -.->|"LV Ref"| LS3_LV

    %% Ground connections (links 27-30)
    F_GND ---|"⚫ GND"| LS1_GND
    F_GND ---|"⚫ GND"| LS2_GND
    F_GND ---|"⚫ GND"| LS3_GND

    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11 stroke:#22c55e,stroke-width:2px
    linkStyle 12,13,14,15,16,17,18,19,20,21,22,23 stroke:#f97316,stroke-width:3px
    linkStyle 24,25,26 stroke:#ef4444,stroke-width:1px
    linkStyle 27,28,29 stroke:#475569,stroke-width:2px

    style FPGA_PWM fill:#14532d,stroke:#22c55e,color:#86efac
    style LS1 fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style LS2 fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style LS3 fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style FL_LEG fill:#7c2d12,stroke:#f97316,color:#fdba74
    style FR_LEG fill:#7c2d12,stroke:#f97316,color:#fdba74
    style RL_LEG fill:#7c2d12,stroke:#f97316,color:#fdba74
    style RR_LEG fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Level Shifter 1 — Channels 0-3 (FL + FR Hip)

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_C03["🟢 FPGA — Channels 0-3"]
        FA0["Pin 28 · pwm 0"]:::fpgaPin
        FA1["Pin 29 · pwm 1"]:::fpgaPin
        FA2["Pin 30 · pwm 2"]:::fpgaPin
        FA3["Pin 31 · pwm 3"]:::fpgaPin
    end

    subgraph LS1_D["🔀 LEVEL SHIFTER 1"]
        LS1D_LV["LV: 3.3V"]:::vcc
        LS1D_HV["HV: 5V"]:::vcc
        LS1D_GND["GND"]:::gnd
        LS1D_A1["LV1 → HV1"]:::lsPin
        LS1D_A2["LV2 → HV2"]:::lsPin
        LS1D_A3["LV3 → HV3"]:::lsPin
        LS1D_A4["LV4 → HV4"]:::lsPin
    end

    subgraph SRV1["🦿 SERVOS"]
        SA0["DS3218 #0 · FL Hip"]:::servoPin
        SA1["DS3218 #1 · FL Thigh"]:::servoPin
        SA2["DS3218 #2 · FL Knee"]:::servoPin
        SA3["DS3218 #3 · FR Hip"]:::servoPin
    end

    FA0 -->|"3.3V PWM"| LS1D_A1
    FA1 -->|"3.3V PWM"| LS1D_A2
    FA2 -->|"3.3V PWM"| LS1D_A3
    FA3 -->|"3.3V PWM"| LS1D_A4

    LS1D_A1 ==>|"5V Signal"| SA0
    LS1D_A2 ==>|"5V Signal"| SA1
    LS1D_A3 ==>|"5V Signal"| SA2
    LS1D_A4 ==>|"5V Signal"| SA3

    linkStyle 0,1,2,3 stroke:#22c55e,stroke-width:2px
    linkStyle 4,5,6,7 stroke:#f97316,stroke-width:3px

    style FPGA_C03 fill:#14532d,stroke:#22c55e,color:#86efac
    style LS1_D fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style SRV1 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Level Shifter 2 — Channels 4-7 (FR Thigh/Knee + RL Hip/Thigh)

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_C47["🟢 FPGA — Channels 4-7"]
        FB4["Pin 32 · pwm 4"]:::fpgaPin
        FB5["Pin 33 · pwm 5"]:::fpgaPin
        FB6["Pin 34 · pwm 6"]:::fpgaPin
        FB7["Pin 35 · pwm 7"]:::fpgaPin
    end

    subgraph LS2_D["🔀 LEVEL SHIFTER 2"]
        LS2D_LV["LV: 3.3V"]:::vcc
        LS2D_HV["HV: 5V"]:::vcc
        LS2D_GND["GND"]:::gnd
        LS2D_A1["LV1 → HV1"]:::lsPin
        LS2D_A2["LV2 → HV2"]:::lsPin
        LS2D_A3["LV3 → HV3"]:::lsPin
        LS2D_A4["LV4 → HV4"]:::lsPin
    end

    subgraph SRV2["🦿 SERVOS"]
        SB4["DS3218 #4 · FR Thigh"]:::servoPin
        SB5["DS3218 #5 · FR Knee"]:::servoPin
        SB6["DS3218 #6 · RL Hip"]:::servoPin
        SB7["DS3218 #7 · RL Thigh"]:::servoPin
    end

    FB4 -->|"3.3V PWM"| LS2D_A1
    FB5 -->|"3.3V PWM"| LS2D_A2
    FB6 -->|"3.3V PWM"| LS2D_A3
    FB7 -->|"3.3V PWM"| LS2D_A4

    LS2D_A1 ==>|"5V Signal"| SB4
    LS2D_A2 ==>|"5V Signal"| SB5
    LS2D_A3 ==>|"5V Signal"| SB6
    LS2D_A4 ==>|"5V Signal"| SB7

    linkStyle 0,1,2,3 stroke:#22c55e,stroke-width:2px
    linkStyle 4,5,6,7 stroke:#f97316,stroke-width:3px

    style FPGA_C47 fill:#14532d,stroke:#22c55e,color:#86efac
    style LS2_D fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style SRV2 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Level Shifter 3 — Channels 8-11 (RL Knee + RR Leg)

```mermaid
graph LR
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef lsPin fill:#5eead4,stroke:#14b8a6,color:#134e4a
    classDef servoPin fill:#fdba74,stroke:#f97316,color:#7c2d12
    classDef vcc fill:#22c55e,stroke:#15803d,color:#fff
    classDef gnd fill:#475569,stroke:#334155,color:#fff

    subgraph FPGA_C811["🟢 FPGA — Channels 8-11"]
        FC8["Pin 40 · pwm 8"]:::fpgaPin
        FC9["Pin 41 · pwm 9"]:::fpgaPin
        FC10["Pin 42 · pwm 10"]:::fpgaPin
        FC11["Pin 48 · pwm 11"]:::fpgaPin
    end

    subgraph LS3_D["🔀 LEVEL SHIFTER 3"]
        LS3D_LV["LV: 3.3V"]:::vcc
        LS3D_HV["HV: 5V"]:::vcc
        LS3D_GND["GND"]:::gnd
        LS3D_A1["LV1 → HV1"]:::lsPin
        LS3D_A2["LV2 → HV2"]:::lsPin
        LS3D_A3["LV3 → HV3"]:::lsPin
        LS3D_A4["LV4 → HV4"]:::lsPin
    end

    subgraph SRV3["🦿 SERVOS"]
        SC8["DS3218 #8 · RL Knee"]:::servoPin
        SC9["DS3218 #9 · RR Hip"]:::servoPin
        SC10["DS3218 #10 · RR Thigh"]:::servoPin
        SC11["DS3218 #11 · RR Knee"]:::servoPin
    end

    FC8 -->|"3.3V PWM"| LS3D_A1
    FC9 -->|"3.3V PWM"| LS3D_A2
    FC10 -->|"3.3V PWM"| LS3D_A3
    FC11 -->|"3.3V PWM"| LS3D_A4

    LS3D_A1 ==>|"5V Signal"| SC8
    LS3D_A2 ==>|"5V Signal"| SC9
    LS3D_A3 ==>|"5V Signal"| SC10
    LS3D_A4 ==>|"5V Signal"| SC11

    linkStyle 0,1,2,3 stroke:#22c55e,stroke-width:2px
    linkStyle 4,5,6,7 stroke:#f97316,stroke-width:3px

    style FPGA_C811 fill:#14532d,stroke:#22c55e,color:#86efac
    style LS3_D fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style SRV3 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Channel-to-Servo Mapping Table

| Channel | FPGA Pin | Level Shifter | LS Channel | Servo | Joint |
|---------|----------|---------------|------------|-------|-------|
| 0 | 28 | LS1 | LV1→HV1 | DS3218 #0 | FL Hip |
| 1 | 29 | LS1 | LV2→HV2 | DS3218 #1 | FL Thigh |
| 2 | 30 | LS1 | LV3→HV3 | DS3218 #2 | FL Knee |
| 3 | 31 | LS1 | LV4→HV4 | DS3218 #3 | FR Hip |
| 4 | 32 | LS2 | LV1→HV1 | DS3218 #4 | FR Thigh |
| 5 | 33 | LS2 | LV2→HV2 | DS3218 #5 | FR Knee |
| 6 | 34 | LS2 | LV3→HV3 | DS3218 #6 | RL Hip |
| 7 | 35 | LS2 | LV4→HV4 | DS3218 #7 | RL Thigh |
| 8 | 40 | LS3 | LV1→HV1 | DS3218 #8 | RL Knee |
| 9 | 41 | LS3 | LV2→HV2 | DS3218 #9 | RR Hip |
| 10 | 42 | LS3 | LV3→HV3 | DS3218 #10 | RR Thigh |
| 11 | 48 | LS3 | LV4→HV4 | DS3218 #11 | RR Knee |

## Level Shifter Power Connections

| Level Shifter | LV Pin | HV Pin | GND |
|---------------|--------|--------|-----|
| LS1 | 3.3V from FPGA | 5V from LM2596 | Common GND |
| LS2 | 3.3V from FPGA | 5V from LM2596 | Common GND |
| LS3 | 3.3V from FPGA | 5V from LM2596 | Common GND |
