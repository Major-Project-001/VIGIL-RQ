# 🩷 GPIO — Buzzer + RGB LED

> Part of [VIGIL-RQ Wiring Documentation](wiring_diagram.md)

---

```mermaid
graph LR
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef alertPin fill:#f9a8d4,stroke:#ec4899,color:#831843
    classDef gnd fill:#475569,stroke:#334155,color:#fff
    classDef resistor fill:#78716c,stroke:#57534e,color:#fff

    subgraph RPI_GPIO["🍓 RASPBERRY PI 4B — GPIO"]
        RPI_GP18["GPIO 18 · Pin 12<br/>PWM0 — Buzzer"]:::rpiPin
        RPI_GP17["GPIO 17 · Pin 11<br/>Red Channel"]:::rpiPin
        RPI_GP27["GPIO 27 · Pin 13<br/>Green Channel"]:::rpiPin
        RPI_GP22["GPIO 22 · Pin 15<br/>Blue Channel"]:::rpiPin
        RPI_GNDG["GND · Pin 14"]:::gnd
    end

    subgraph RESISTORS["🔧 CURRENT LIMITING"]
        R1["220Ω R"]:::resistor
        R2["220Ω G"]:::resistor
        R3["220Ω B"]:::resistor
    end

    subgraph BUZZER_BLOCK["🔊 ACTIVE BUZZER"]
        BUZ_SIG["Signal +"]:::alertPin
        BUZ_GND["GND -"]:::alertPin
    end

    subgraph RGB_BLOCK["💡 RGB LED — Common Cathode"]
        RGB_R["Red Anode"]:::alertPin
        RGB_G["Green Anode"]:::alertPin
        RGB_B["Blue Anode"]:::alertPin
        RGB_GND["Common Cathode"]:::alertPin
    end

    %% Buzzer (links 0-1)
    RPI_GP18 ==>|"🟠 PWM Signal"| BUZ_SIG
    BUZ_GND -->|"⚫ GND"| RPI_GNDG

    %% RGB LED via resistors (links 2-8)
    RPI_GP17 -->|"🔴 PWM"| R1
    R1 -->|" "| RGB_R
    RPI_GP27 -->|"🟢 PWM"| R2
    R2 -->|" "| RGB_G
    RPI_GP22 -->|"🔵 PWM"| R3
    R3 -->|" "| RGB_B
    RGB_GND -->|"⚫ GND"| RPI_GNDG

    linkStyle 0 stroke:#ec4899,stroke-width:3px
    linkStyle 1 stroke:#475569,stroke-width:2px
    linkStyle 2,3 stroke:#ef4444,stroke-width:2px
    linkStyle 4,5 stroke:#22c55e,stroke-width:2px
    linkStyle 6,7 stroke:#3b82f6,stroke-width:2px
    linkStyle 8 stroke:#475569,stroke-width:2px

    style RPI_GPIO fill:#1e3a5f,stroke:#3b82f6,color:#93c5fd
    style BUZZER_BLOCK fill:#831843,stroke:#ec4899,color:#f9a8d4
    style RGB_BLOCK fill:#831843,stroke:#ec4899,color:#f9a8d4
    style RESISTORS fill:#292524,stroke:#78716c,color:#d6d3d1
```

---

## Alert GPIO Pin Mapping

| RPi GPIO | Pin | Function | Component | Wire Colour | Wire Gauge |
|----------|-----|----------|-----------|-------------|------------|
| GPIO 18 | 12 | PWM0 | Buzzer signal (+) | 🟠 Orange | 24 AWG |
| GPIO 17 | 11 | SW PWM | 220Ω → Red anode | 🔴 Red | 24 AWG |
| GPIO 27 | 13 | SW PWM | 220Ω → Green anode | 🟢 Green | 24 AWG |
| GPIO 22 | 15 | SW PWM | 220Ω → Blue anode | 🔵 Blue | 24 AWG |
| GND | 14 | Ground | Buzzer GND + LED cathode | ⚫ Black | 24 AWG |

## RGB LED Colour Codes

| Colour | Red | Green | Blue | Meaning |
|--------|-----|-------|------|---------|
| 🟢 Green | OFF | ON | OFF | System OK, connected |
| 🔵 Blue | OFF | OFF | ON | Starting up / connecting |
| 🟡 Yellow | ON | ON | OFF | Low battery warning |
| 🔴 Red | ON | OFF | OFF | Critical error / E-STOP |
| 🟣 Purple | ON | OFF | ON | IMU error |
| ⬜ White | ON | ON | ON | Watchdog triggered |

> [!NOTE]
> The buzzer uses hardware PWM (GPIO 18 = PWM0) for tone generation. The RGB LED uses software PWM for colour mixing. All 220Ω resistors limit current to ~15mA per channel at 3.3V.
