# 🔵 SPI Bus — Raspberry Pi ↔ Tang Nano 9K

> Part of [VIGIL-RQ Wiring Documentation](wiring_diagram.md)

---

```mermaid
graph LR
    classDef rpiPin fill:#93c5fd,stroke:#3b82f6,color:#1e3a5f
    classDef fpgaPin fill:#86efac,stroke:#22c55e,color:#14532d
    classDef gnd fill:#475569,stroke:#334155,color:#fff
    classDef vcc fill:#fbbf24,stroke:#d97706,color:#78350f

    subgraph RPI_SPI["🍓 RASPBERRY PI 4B — SPI0"]
        RPI_SCLK["GPIO 11 · Pin 23<br/>SPI0_SCLK"]:::rpiPin
        RPI_MOSI["GPIO 10 · Pin 19<br/>SPI0_MOSI"]:::rpiPin
        RPI_MISO["GPIO 9 · Pin 21<br/>SPI0_MISO — NC"]:::rpiPin
        RPI_CE0["GPIO 8 · Pin 24<br/>SPI0_CE0"]:::rpiPin
        RPI_GND_SPI["GND · Pin 25"]:::gnd
        RPI_3V3_SPI["3.3V · Pin 17"]:::vcc
    end

    subgraph FPGA_SPI["🟢 TANG NANO 9K — SPI SLAVE"]
        FPGA_SCLK["Pin 25<br/>spi_sclk"]:::fpgaPin
        FPGA_MOSI["Pin 26<br/>spi_mosi"]:::fpgaPin
        FPGA_CS["Pin 27<br/>spi_cs_n"]:::fpgaPin
        FPGA_GND_SPI["GND<br/>Header GND"]:::gnd
    end

    subgraph NOTES_SPI["📝 SPI CONFIGURATION"]
        N1["Mode 0: CPOL=0 CPHA=0"]
        N2["Clock: 1 MHz"]
        N3["Both 3.3V logic — NO level shifter"]
        N4["Frame: 3 bytes per servo command"]
    end

    %% SPI Signal connections (links 0-3)
    RPI_SCLK ==>|"🔵 SCLK · 22AWG"| FPGA_SCLK
    RPI_MOSI ==>|"🟢 MOSI · 22AWG"| FPGA_MOSI
    RPI_CE0 ==>|"🟡 CS · 22AWG"| FPGA_CS
    RPI_GND_SPI ---|"⚫ GND · 22AWG"| FPGA_GND_SPI

    linkStyle 0 stroke:#3b82f6,stroke-width:3px
    linkStyle 1 stroke:#22c55e,stroke-width:3px
    linkStyle 2 stroke:#eab308,stroke-width:3px
    linkStyle 3 stroke:#475569,stroke-width:3px

    style RPI_SPI fill:#1e3a5f,stroke:#3b82f6,color:#93c5fd
    style FPGA_SPI fill:#14532d,stroke:#22c55e,color:#86efac
    style NOTES_SPI fill:#1e293b,stroke:#475569,color:#94a3b8
```

---

## SPI Pin Mapping

| RPi GPIO | RPi Pin | Signal | FPGA Pin | Wire Colour | Notes |
|----------|---------|--------|----------|-------------|-------|
| GPIO 11 | 23 | SCLK | 25 | 🔵 Blue | Clock, 1 MHz |
| GPIO 10 | 19 | MOSI | 26 | 🟢 Green | Data RPi→FPGA |
| GPIO 9 | 21 | MISO | — | — | Reserved, not connected |
| GPIO 8 | 24 | CE0 (CS) | 27 | 🟡 Yellow | Active low chip select |
| GND | 25 | Ground | GND | ⚫ Black | Shared ground |

## SPI Frame Format

Each servo command is **3 bytes**:

| Byte | Content | Range |
|------|---------|-------|
| 0 | Channel ID | 0–11 |
| 1 | Pulse width MSB | High 8 bits of µs value |
| 2 | Pulse width LSB | Low 8 bits of µs value |

> [!IMPORTANT]
> Both RPi 4B SPI0 and Tang Nano 9K GPIO run at **3.3V** — **no level shifter needed** on the SPI bus. Keep SPI wires **short** (<15cm) to avoid noise. SPI MISO is reserved but not connected since the FPGA is receive-only.

> [!NOTE]
> The **Notes** box in the diagram is intentionally disconnected — it's a reference info panel, not a wired component.
