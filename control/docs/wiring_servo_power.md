# 🟠 Servo Power — 6.8V Rail to All 12 DS3218

> Part of [VIGIL-RQ Wiring Documentation](wiring_diagram.md)

---

## DS3218 Connector Pinout

Each DS3218 servo has a **3-pin JST connector**. Wire order looking at the plug face:

```mermaid
graph LR
    classDef orange fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef red fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef brown fill:#78716c,stroke:#57534e,color:#fff,font-weight:bold
    classDef plug fill:#1e293b,stroke:#475569,color:#e2e8f0,font-weight:bold

    subgraph PLUG["🔌 DS3218 JST CONNECTOR — Face View"]
        P1["🟠 Pin 1<br/>SIGNAL<br/>Orange wire"]:::orange
        P2["🔴 Pin 2<br/>VCC +6.8V<br/>Red wire"]:::red
        P3["⚫ Pin 3<br/>GND<br/>Brown wire"]:::brown
    end

    P1 -->|"22 AWG"| LS_HV["Level Shifter<br/>HV Output"]
    P2 -->|"18 AWG"| RAIL["XL4015<br/>6.8V Rail"]
    P3 -->|"18 AWG"| GND["Common<br/>GND Bus"]

    linkStyle 0 stroke:#f97316,stroke-width:3px
    linkStyle 1 stroke:#ef4444,stroke-width:3px
    linkStyle 2 stroke:#78716c,stroke-width:3px

    style PLUG fill:#0f172a,stroke:#475569,color:#94a3b8
    style LS_HV fill:#134e4a,stroke:#14b8a6,color:#5eead4
    style RAIL fill:#7f1d1d,stroke:#ef4444,color:#fca5a5
    style GND fill:#1e293b,stroke:#475569,color:#e2e8f0
```

| Wire | Colour | Function | Connects To | Gauge |
|------|--------|----------|-------------|-------|
| 1 (left) | 🟠 Orange | Signal (PWM) | Level shifter HV output | 22 AWG |
| 2 (center) | 🔴 Red | Power (+) | XL4015 6.8V rail | 18 AWG |
| 3 (right) | ⚫ Brown | Ground (-) | Common GND bus | 18 AWG |

> [!CAUTION]
> **Never power servos from the Raspberry Pi 5V pins.** The DS3218 can draw up to 2.5A stall current each. 12 servos × 2.5A = 30A peak. Only the XL4015 buck converter can supply this.

---

## Front Left Leg — DS3218 #0 / #1 / #2

```mermaid
graph TD
    classDef red fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef orange fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef brown fill:#78716c,stroke:#57534e,color:#fff,font-weight:bold
    classDef rail fill:#7f1d1d,stroke:#ef4444,color:#fca5a5,font-weight:bold
    classDef ls fill:#134e4a,stroke:#14b8a6,color:#5eead4,font-weight:bold

    subgraph SOURCES_FL["⚡ POWER SOURCES"]
        RP1["+6.8V Rail"]:::rail
        RG1["GND Bus"]:::brown
        LS1_HV1["LS1 HV1"]:::ls
        LS1_HV2["LS1 HV2"]:::ls
        LS1_HV3["LS1 HV3"]:::ls
    end

    subgraph S0["DS3218 #0 — FL HIP"]
        S0_R["🔴 Red +6.8V"]:::red
        S0_O["🟠 Orange Signal"]:::orange
        S0_B["⚫ Brown GND"]:::brown
    end

    subgraph S1["DS3218 #1 — FL THIGH"]
        S1_R["🔴 Red +6.8V"]:::red
        S1_O["🟠 Orange Signal"]:::orange
        S1_B["⚫ Brown GND"]:::brown
    end

    subgraph S2["DS3218 #2 — FL KNEE"]
        S2_R["🔴 Red +6.8V"]:::red
        S2_O["🟠 Orange Signal"]:::orange
        S2_B["⚫ Brown GND"]:::brown
    end

    RP1 ==>|"18AWG"| S0_R
    RP1 ==>|"18AWG"| S1_R
    RP1 ==>|"18AWG"| S2_R
    LS1_HV1 -->|"22AWG"| S0_O
    LS1_HV2 -->|"22AWG"| S1_O
    LS1_HV3 -->|"22AWG"| S2_O
    RG1 ==>|"18AWG"| S0_B
    RG1 ==>|"18AWG"| S1_B
    RG1 ==>|"18AWG"| S2_B

    linkStyle 0,1,2 stroke:#ef4444,stroke-width:3px
    linkStyle 3,4,5 stroke:#f97316,stroke-width:2px
    linkStyle 6,7,8 stroke:#78716c,stroke-width:3px

    style SOURCES_FL fill:#1e293b,stroke:#475569,color:#e2e8f0
    style S0 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S1 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S2 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Front Right Leg — DS3218 #3 / #4 / #5

```mermaid
graph TD
    classDef red fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef orange fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef brown fill:#78716c,stroke:#57534e,color:#fff,font-weight:bold
    classDef rail fill:#7f1d1d,stroke:#ef4444,color:#fca5a5,font-weight:bold
    classDef ls fill:#134e4a,stroke:#14b8a6,color:#5eead4,font-weight:bold

    subgraph SOURCES_FR["⚡ POWER SOURCES"]
        RP2["+6.8V Rail"]:::rail
        RG2["GND Bus"]:::brown
        LS1_HV4["LS1 HV4"]:::ls
        LS2_HV1["LS2 HV1"]:::ls
        LS2_HV2["LS2 HV2"]:::ls
    end

    subgraph S3["DS3218 #3 — FR HIP"]
        S3_R["🔴 Red +6.8V"]:::red
        S3_O["🟠 Orange Signal"]:::orange
        S3_B["⚫ Brown GND"]:::brown
    end

    subgraph S4["DS3218 #4 — FR THIGH"]
        S4_R["🔴 Red +6.8V"]:::red
        S4_O["🟠 Orange Signal"]:::orange
        S4_B["⚫ Brown GND"]:::brown
    end

    subgraph S5["DS3218 #5 — FR KNEE"]
        S5_R["🔴 Red +6.8V"]:::red
        S5_O["🟠 Orange Signal"]:::orange
        S5_B["⚫ Brown GND"]:::brown
    end

    RP2 ==>|"18AWG"| S3_R
    RP2 ==>|"18AWG"| S4_R
    RP2 ==>|"18AWG"| S5_R
    LS1_HV4 -->|"22AWG"| S3_O
    LS2_HV1 -->|"22AWG"| S4_O
    LS2_HV2 -->|"22AWG"| S5_O
    RG2 ==>|"18AWG"| S3_B
    RG2 ==>|"18AWG"| S4_B
    RG2 ==>|"18AWG"| S5_B

    linkStyle 0,1,2 stroke:#ef4444,stroke-width:3px
    linkStyle 3,4,5 stroke:#f97316,stroke-width:2px
    linkStyle 6,7,8 stroke:#78716c,stroke-width:3px

    style SOURCES_FR fill:#1e293b,stroke:#475569,color:#e2e8f0
    style S3 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S4 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S5 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Rear Left Leg — DS3218 #6 / #7 / #8

```mermaid
graph TD
    classDef red fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef orange fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef brown fill:#78716c,stroke:#57534e,color:#fff,font-weight:bold
    classDef rail fill:#7f1d1d,stroke:#ef4444,color:#fca5a5,font-weight:bold
    classDef ls fill:#134e4a,stroke:#14b8a6,color:#5eead4,font-weight:bold

    subgraph SOURCES_RL["⚡ POWER SOURCES"]
        RP3["+6.8V Rail"]:::rail
        RG3["GND Bus"]:::brown
        LS2_HV3["LS2 HV3"]:::ls
        LS2_HV4["LS2 HV4"]:::ls
        LS3_HV1["LS3 HV1"]:::ls
    end

    subgraph S6["DS3218 #6 — RL HIP"]
        S6_R["🔴 Red +6.8V"]:::red
        S6_O["🟠 Orange Signal"]:::orange
        S6_B["⚫ Brown GND"]:::brown
    end

    subgraph S7["DS3218 #7 — RL THIGH"]
        S7_R["🔴 Red +6.8V"]:::red
        S7_O["🟠 Orange Signal"]:::orange
        S7_B["⚫ Brown GND"]:::brown
    end

    subgraph S8["DS3218 #8 — RL KNEE"]
        S8_R["🔴 Red +6.8V"]:::red
        S8_O["🟠 Orange Signal"]:::orange
        S8_B["⚫ Brown GND"]:::brown
    end

    RP3 ==>|"18AWG"| S6_R
    RP3 ==>|"18AWG"| S7_R
    RP3 ==>|"18AWG"| S8_R
    LS2_HV3 -->|"22AWG"| S6_O
    LS2_HV4 -->|"22AWG"| S7_O
    LS3_HV1 -->|"22AWG"| S8_O
    RG3 ==>|"18AWG"| S6_B
    RG3 ==>|"18AWG"| S7_B
    RG3 ==>|"18AWG"| S8_B

    linkStyle 0,1,2 stroke:#ef4444,stroke-width:3px
    linkStyle 3,4,5 stroke:#f97316,stroke-width:2px
    linkStyle 6,7,8 stroke:#78716c,stroke-width:3px

    style SOURCES_RL fill:#1e293b,stroke:#475569,color:#e2e8f0
    style S6 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S7 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S8 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Rear Right Leg — DS3218 #9 / #10 / #11

```mermaid
graph TD
    classDef red fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef orange fill:#f97316,stroke:#c2410c,color:#fff,font-weight:bold
    classDef brown fill:#78716c,stroke:#57534e,color:#fff,font-weight:bold
    classDef rail fill:#7f1d1d,stroke:#ef4444,color:#fca5a5,font-weight:bold
    classDef ls fill:#134e4a,stroke:#14b8a6,color:#5eead4,font-weight:bold

    subgraph SOURCES_RR["⚡ POWER SOURCES"]
        RP4["+6.8V Rail"]:::rail
        RG4["GND Bus"]:::brown
        LS3_HV2["LS3 HV2"]:::ls
        LS3_HV3["LS3 HV3"]:::ls
        LS3_HV4["LS3 HV4"]:::ls
    end

    subgraph S9["DS3218 #9 — RR HIP"]
        S9_R["🔴 Red +6.8V"]:::red
        S9_O["🟠 Orange Signal"]:::orange
        S9_B["⚫ Brown GND"]:::brown
    end

    subgraph S10["DS3218 #10 — RR THIGH"]
        S10_R["🔴 Red +6.8V"]:::red
        S10_O["🟠 Orange Signal"]:::orange
        S10_B["⚫ Brown GND"]:::brown
    end

    subgraph S11["DS3218 #11 — RR KNEE"]
        S11_R["🔴 Red +6.8V"]:::red
        S11_O["🟠 Orange Signal"]:::orange
        S11_B["⚫ Brown GND"]:::brown
    end

    RP4 ==>|"18AWG"| S9_R
    RP4 ==>|"18AWG"| S10_R
    RP4 ==>|"18AWG"| S11_R
    LS3_HV2 -->|"22AWG"| S9_O
    LS3_HV3 -->|"22AWG"| S10_O
    LS3_HV4 -->|"22AWG"| S11_O
    RG4 ==>|"18AWG"| S9_B
    RG4 ==>|"18AWG"| S10_B
    RG4 ==>|"18AWG"| S11_B

    linkStyle 0,1,2 stroke:#ef4444,stroke-width:3px
    linkStyle 3,4,5 stroke:#f97316,stroke-width:2px
    linkStyle 6,7,8 stroke:#78716c,stroke-width:3px

    style SOURCES_RR fill:#1e293b,stroke:#475569,color:#e2e8f0
    style S9 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S10 fill:#7c2d12,stroke:#f97316,color:#fdba74
    style S11 fill:#7c2d12,stroke:#f97316,color:#fdba74
```

---

## Complete Servo Wiring Summary Table

| Servo # | Joint | 🔴 Red (+6.8V) | 🟠 Orange (Signal) | ⚫ Brown (GND) |
|---------|-------|----------------|---------------------|----------------|
| 0 | FL Hip | XL4015 rail | LS1 HV1 (from FPGA Pin 28) | GND bus |
| 1 | FL Thigh | XL4015 rail | LS1 HV2 (from FPGA Pin 29) | GND bus |
| 2 | FL Knee | XL4015 rail | LS1 HV3 (from FPGA Pin 30) | GND bus |
| 3 | FR Hip | XL4015 rail | LS1 HV4 (from FPGA Pin 31) | GND bus |
| 4 | FR Thigh | XL4015 rail | LS2 HV1 (from FPGA Pin 32) | GND bus |
| 5 | FR Knee | XL4015 rail | LS2 HV2 (from FPGA Pin 33) | GND bus |
| 6 | RL Hip | XL4015 rail | LS2 HV3 (from FPGA Pin 34) | GND bus |
| 7 | RL Thigh | XL4015 rail | LS2 HV4 (from FPGA Pin 35) | GND bus |
| 8 | RL Knee | XL4015 rail | LS3 HV1 (from FPGA Pin 40) | GND bus |
| 9 | RR Hip | XL4015 rail | LS3 HV2 (from FPGA Pin 41) | GND bus |
| 10 | RR Thigh | XL4015 rail | LS3 HV3 (from FPGA Pin 42) | GND bus |
| 11 | RR Knee | XL4015 rail | LS3 HV4 (from FPGA Pin 48) | GND bus |

## Current Budget

| Scenario | Per Servo | 12 Servos Total | Notes |
|----------|-----------|-----------------|-------|
| Idle (holding) | ~150 mA | ~1.8 A | No load, neutral position |
| Walking (typical) | ~500 mA | ~6 A | Normal gait operation |
| Heavy load | ~1.2 A | ~14 A | Climbing / rough terrain |
| Stall (worst case) | ~2.5 A | ~30 A | All servos locked — fuse trips |

> [!WARNING]
> Use **18 AWG wire pairs** from the XL4015 rail to each group of 3 servos (one pair per leg). Using thinner wire will cause voltage drop under load, leading to servo brown-out and twitching.
