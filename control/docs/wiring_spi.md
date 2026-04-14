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

---

## SPI Timing — Mode 0 (CPOL=0, CPHA=0)

```
         ┌─ CS asserted                                           CS released ─┐
         │                                                                      │
CS    ───┐                                                                      ┌───
         └──────────────────────────────────────────────────────────────────────┘
              │◄──────── Byte 0 ────────►│◄──────── Byte 1 ────────►│◄──── Byte 2 ────►│
              │       Channel ID         │      Pulse µs [15:8]     │   Pulse µs [7:0]  │
              │                          │                          │                    │
SCLK  ────────┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌─────
              └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘
              1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
                                                                            clock edges
MOSI  ───┬────╫────╫────╫────╫────╫────╫────╫────╫─┬──╫────╫────╫────╫────╫────╫────╫──┬───
         │  MSB                              LSB  │MSB                            LSB │
         │  D7   D6   D5   D4   D3   D2   D1  D0 │D7   D6   D5   D4   D3   D2  D1 D0│
         │           Channel ID (0-11)            │        Pulse Width High            │
         └────────────────────────────────────────┴────────────────────────────────────┘
              ↑ Data sampled on rising edge of SCLK (Mode 0)
```

**Example: Channel 0 → 1500 µs (neutral)**

```
Byte 0 = 0x00 = Channel 0    → MOSI: 00000000
Byte 1 = 0x05 = 1500 >> 8    → MOSI: 00000101
Byte 2 = 0xDC = 1500 & 0xFF  → MOSI: 11011100
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| Clock speed | 1 MHz | RPi `spidev` max_speed_hz |
| Clock polarity (CPOL) | 0 | Idle low |
| Clock phase (CPHA) | 0 | Sample on rising edge |
| Bit order | MSB first | Default for both RPi and FPGA |
| CS active | Low | RPi drives CE0 low during transfer |
| Transfer time | ~24 µs per command | 3 bytes × 8 bits / 1 MHz |
| Update rate | 50 Hz (20 ms) | One full sweep of 12 servos per cycle |

### Full Update Cycle

At 50 Hz, the RPi sends 12 commands per cycle:

```
Total SPI time = 12 channels × 24 µs = 288 µs per cycle
Available time = 20,000 µs (50 Hz period)
SPI utilisation = 1.4%  ← plenty of headroom
```

---

## Wiring Best Practices

1. **Keep wires short** — SPI is high-speed digital; wires >15cm act as antennas
2. **Twist SCLK+GND together** — reduces electromagnetic interference
3. **Route SPI away from servo power wires** — switching 6.8V/2A servos creates noise
4. **Use consistent wire colours** — Blue=SCLK, Green=MOSI, Yellow=CS, Black=GND
5. **Solder connections preferred** — DuPont jumpers can work loose under vibration
6. **Add a GND wire** — even though ground is shared via power, a dedicated SPI GND wire reduces noise

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No SPI activity (FPGA LED[1] never lights) | CS not connected or wrong pin | Check GPIO 8 → FPGA Pin 27 |
| Servos jitter randomly | Ground loop or missing GND wire | Add dedicated SPI GND wire |
| Servos don't respond at all | SPI clock too fast or CPOL wrong | Verify 1 MHz, Mode 0 in Python |
| Intermittent channel glitches | Loose DuPont connection | Solder SPI wires |
| All servos go to neutral after 500ms | FPGA watchdog tripping | SPI commands not arriving — check `spidev` |

### Quick SPI Test (Python)

```python
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, CE0
spi.max_speed_hz = 1_000_000
spi.mode = 0b00

# Send channel 0 to neutral (1500 µs = 0x05DC)
spi.xfer2([0x00, 0x05, 0xDC])
print("Sent: Ch0 → 1500 µs")
```

