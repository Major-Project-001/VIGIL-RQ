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
    classDef posBlock fill:#fbbf24,stroke:#d97706,color:#7c2d12,font-weight:bold
    classDef gndBlock fill:#64748b,stroke:#475569,color:#fff,font-weight:bold
    classDef bmsNote fill:#a78bfa,stroke:#7c3aed,color:#fff,font-weight:bold
    classDef diode fill:#f472b6,stroke:#db2777,color:#fff,font-weight:bold

    subgraph BATTERY["🔋 3× Dragon 3S PACKS — PARALLEL — 11.1V / 9000mAh"]
        BAT_NOTE["🛡 Internal BMS per pack"]:::bmsNote
        BAT_POS["+ Positive (joined)"]:::powerPin
        BAT_NEG["- Negative (joined)"]:::powerPin
    end

    subgraph FUSE_BLOCK["⚡ 15A INLINE FUSE"]
        FUSE_IN["Fuse In"]:::powerPin
        FUSE_OUT["Fuse Out"]:::powerPin
    end

    subgraph POS_TERMINAL["🔴 +V TERMINAL BLOCK (6-pin)"]
        PT1["1: +V IN"]:::posBlock
        PT2["2: → XL4015 VIN"]:::posBlock
        PT3["3: → LM2596 diode"]:::posBlock
        PT4["4: spare"]:::posBlock
        PT5["5: spare"]:::posBlock
        PT6["6: spare"]:::posBlock
    end

    subgraph GND_TERMINAL["⚫ GND TERMINAL BLOCK (6-pin)"]
        GT1["1: GND IN"]:::gndBlock
        GT2["2: → XL4015 GND"]:::gndBlock
        GT3["3: → LM2596 GND"]:::gndBlock
        GT4["4: → RPi USB-C GND"]:::gndBlock
        GT5["5: → FPGA USB-C GND"]:::gndBlock
        GT6["6: → buck GND returns"]:::gndBlock
    end

    subgraph DIODE_BLOCK["🔒 1N5822 SCHOTTKY DIODE"]
        D1_A["Anode ←"]:::diode
        D1_K["→ Cathode"]:::diode
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

    subgraph LOADS["📤 POWER OUTPUTS"]
        RPI_5V["RPi 4B — USB-C 5V"]:::rpiPin
        FPGA_5V["Tang Nano 9K — USB-C 5V"]:::rpiPin
        LS_HV["Level Shifters — HV 5V"]:::lsPin
        SERVO_PWR["12× Servos — 6.8V Rail"]:::servoPin
    end

    %% Battery → Fuse / GND terminal (no external BMS — internal per pack)
    BAT_POS -->|"🔴 16AWG"| FUSE_IN
    BAT_NEG -->|"⚫ 16AWG"| GT1

    %% Fuse → +V terminal
    FUSE_OUT -->|"🔴 16AWG"| PT1

    %% +V terminal → XL4015 (direct — no diode, 15A too high for 1N5822)
    PT2 -->|"🔴 16AWG"| BS_VIN

    %% +V terminal → diode → LM2596 (reverse polarity protection)
    PT3 -->|"🔴"| D1_A
    D1_K -->|"🔴"| BL_VIN

    %% GND terminal → bucks
    GT2 -->|"⚫ 16AWG"| BS_GND
    GT3 -->|"⚫ 16AWG"| BL_GND

    %% Buck GND returns → GND terminal
    BS_GNDO -->|"⚫"| GT6
    BL_GNDO -->|"⚫"| GT6

    %% Buck outputs → loads
    BS_VOUT ==>|"🔴 16AWG"| SERVO_PWR
    BL_VOUT -->|"🔴 USB-C"| RPI_5V
    BL_VOUT -->|"🔴 USB-C"| FPGA_5V
    BL_VOUT -->|"🔴 22AWG"| LS_HV

    %% Bus bars (bare copper wire through all 6 positions)
    PT1 ---|"bus bar"| PT2
    PT2 ---|"bus bar"| PT3
    PT3 ---|"bus bar"| PT4
    PT4 ---|"bus bar"| PT5
    PT5 ---|"bus bar"| PT6
    GT1 ---|"bus bar"| GT2
    GT2 ---|"bus bar"| GT3
    GT3 ---|"bus bar"| GT4
    GT4 ---|"bus bar"| GT5
    GT5 ---|"bus bar"| GT6

    linkStyle 0 stroke:#ef4444,stroke-width:3px
    linkStyle 1 stroke:#475569,stroke-width:3px
    linkStyle 2 stroke:#ef4444,stroke-width:3px
    linkStyle 3 stroke:#ef4444,stroke-width:2px
    linkStyle 4,5 stroke:#f472b6,stroke-width:2px
    linkStyle 6,7 stroke:#475569,stroke-width:2px
    linkStyle 8,9 stroke:#475569,stroke-width:2px
    linkStyle 10 stroke:#ef4444,stroke-width:3px
    linkStyle 11,12,13 stroke:#ef4444,stroke-width:2px
    linkStyle 14,15,16,17,18 stroke:#fbbf24,stroke-width:2px,stroke-dasharray:5
    linkStyle 19,20,21,22,23 stroke:#64748b,stroke-width:2px,stroke-dasharray:5
```

---

## Screw Terminal Block Wiring (2× 6-pin)

Use two separate 6-pin terminal blocks — one for **+V distribution**, one for **GND distribution**.

### How to Make a Bus Bar

Each position on a screw terminal is **electrically isolated by default**. To make all positions share the same voltage, create a **bus bar**:

1. Cut a ~10 cm piece of **16 AWG wire**
2. Strip the **entire insulation** off — you want bare copper
3. Bend it so it runs under all 6 screw positions
4. Tighten each screw down onto the bare wire
5. Now all 6 positions are connected — you can add/remove wires from any position freely

Do this for **both** terminal blocks.

### +V Block Layout

```mermaid
graph TD
    classDef pos fill:#fbbf24,stroke:#d97706,color:#7c2d12,font-weight:bold
    classDef busbar fill:#ef4444,stroke:#b91c1c,color:#fff,font-weight:bold
    classDef wire fill:#fca5a5,stroke:#ef4444,color:#7f1d1d

    BUS["🔴 16AWG BARE COPPER BUS BAR"]:::busbar

    P1["Pos 1: +V IN\n← from fuse"]:::pos
    P2["Pos 2: +V OUT\n→ XL4015 VIN"]:::pos
    P3["Pos 3: +V OUT\n→ LM2596 VIN"]:::pos
    P4["Pos 4: spare"]:::pos
    P5["Pos 5: spare"]:::pos
    P6["Pos 6: spare"]:::pos

    BUS --- P1
    BUS --- P2
    BUS --- P3
    BUS --- P4
    BUS --- P5
    BUS --- P6

    linkStyle 0,1,2,3,4,5 stroke:#ef4444,stroke-width:3px
```

### GND Block Layout

```mermaid
graph TD
    classDef gndpos fill:#64748b,stroke:#475569,color:#fff,font-weight:bold
    classDef busbar fill:#475569,stroke:#334155,color:#fff,font-weight:bold

    BUS["⚫ 16AWG BARE COPPER BUS BAR"]:::busbar

    G1["Pos 1: GND IN\n← from battery GND"]:::gndpos
    G2["Pos 2: GND OUT\n→ XL4015 GND"]:::gndpos
    G3["Pos 3: GND OUT\n→ LM2596 GND"]:::gndpos
    G4["Pos 4: GND OUT\n→ RPi USB-C black"]:::gndpos
    G5["Pos 5: GND OUT\n→ FPGA USB-C black"]:::gndpos
    G6["Pos 6: GND OUT\n→ buck GND returns"]:::gndpos

    BUS --- G1
    BUS --- G2
    BUS --- G3
    BUS --- G4
    BUS --- G5
    BUS --- G6

    linkStyle 0,1,2,3,4,5 stroke:#475569,stroke-width:3px
```

> [!TIP]
> Two wires fit in one terminal position. If a position needs two connections (e.g. GND pos 6 gets both buck converter GND returns), insert both stripped wire ends side-by-side and tighten. Tug-test both wires after.

---

## Power Rail Summary

| Rail | Source | Voltage | Current | Wire Gauge | Feeds |
|------|--------|---------|---------|------------|-------|
| Servo | XL4015 | 6.8V | ~15A peak | 16 AWG | 12× DS3218 servos |
| Logic | LM2596 | 5.0V | ~2A | USB-C | RPi 4B, Tang Nano 9K |
| LV Ref | FPGA 3.3V | 3.3V | <50mA | 22 AWG | 3× level shifters (LV side) |
| I2C | RPi 3.3V | 3.3V | <20mA | 22 AWG | IMU, INA219 |

> [!WARNING]
> **Always adjust buck converter trimpots with a multimeter BEFORE connecting any load.** Set XL4015 to 6.8V and LM2596 to 5.0V. Incorrect voltage will destroy the RPi or servos.

---

## 18650 Battery Pack Specifications

Using **3× Dragon 3S 3000mAh packs wired in parallel**. Each pack has an **internal BMS** — no external BMS board needed.

| Parameter | Value |
|-----------|-------|
| Chemistry | Li-ion (18650 cells) |
| Configuration per pack | 3S1P (3 cells in series) |
| Internal BMS per pack | ✅ Over-discharge, over-charge, short circuit |
| Packs in parallel | 3 |
| Effective configuration | 3S3P |
| Nominal voltage | 11.1V (3.7V × 3) |
| Fully charged | 12.6V (4.2V × 3) |
| Low cutoff | 9.0V (3.0V × 3) — internal BMS disconnects |
| Combined capacity | 9000mAh (3 × 3000mAh) |
| Max continuous discharge | ~15A (3 × ~5A per pack) |

> [!CAUTION]
> **Before connecting packs in parallel:** Charge all 3 packs fully and verify they are within **0.1V** of each other using a multimeter. Connecting packs at different voltages causes a dangerous current surge between them.

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

## Making USB-C Power Cables (LM2596 → RPi & FPGA)

The LM2596's 5V output powers the RPi and Tang Nano 9K via USB-C. You'll make two simple cables by cutting cheap USB-C charging cables.

### What You Need

| Item | Qty | Notes |
|------|-----|-------|
| USB-C charging cable | 2 | Cheap ones are fine — you only need the power wires |
| Wire strippers | 1 | For exposing the internal wires |
| Soldering iron + solder | 1 | For secure connections |
| Heat shrink tubing | — | To insulate exposed joints |
| Multimeter | 1 | To verify voltage before plugging in |

### Step-by-Step

1. **Cut the cable** — keep the **USB-C end** (the end that plugs into the Pi / FPGA), discard the other end
2. **Strip the outer jacket** — expose ~3 cm of the internal wires
3. **Identify the power wires:**

   | Wire Color | Purpose | Connect To |
   |-----------|---------|------------|
   | 🔴 **Red** | +5V | LM2596 **VOUT** |
   | ⚫ **Black** | GND | Common **GND bus** |
   | 🟢 Green / 🔵 Blue / ⚪ White | Data (D+, D-) | **Cut short & insulate** — not needed |

4. **Solder or crimp** the red and black wires:
   - Both cables' **red wires** → LM2596 **VOUT** terminal
   - Both cables' **black wires** → **common GND bus**
5. **Heat shrink** all exposed joints
6. **Verify before plugging in:**
   - Set multimeter to DC voltage
   - Touch probes to the USB-C connector's power pins (or just the red/black wires)
   - Confirm **5.0V ± 0.05V**
7. **Plug in** — USB-C into RPi, second USB-C into Tang Nano 9K

### Final Wiring

```
LM2596 VOUT (+5V) ──┬── 🔴 red wire ── USB-C ──→ 🍓 RPi 4B
                     └── 🔴 red wire ── USB-C ──→ 🟢 Tang Nano 9K

LM2596 GND OUT ─────┬── ⚫ black wire ─── (from RPi cable)    ──→ ⏚ Common GND
                     └── ⚫ black wire ─── (from FPGA cable)   ──→ ⏚ Common GND
```

> [!TIP]
> **Why USB-C instead of GPIO header pins?** Powering via USB-C uses the Pi's built-in protection circuitry (polyfuse + ESD diode). Feeding 5V directly to GPIO pins 2/4 works but bypasses this protection — a wiring mistake could fry the Pi.

> [!WARNING]
> Some ultra-cheap USB-C cables have non-standard wire colors. If in doubt, use a multimeter in continuity mode: touch one probe to the **metal shell** of the USB-C plug (that's GND) and check which internal wire beeps.

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

