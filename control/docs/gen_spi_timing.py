"""
Generate SPI Mode 0 timing diagram for VIGIL-RQ wiring documentation.
Output: spi_timing.png in control/docs/
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Colours (matching our wiring doc palette) ──
BG       = '#0f172a'
GRID     = '#1e293b'
CS_CLR   = '#eab308'   # yellow
SCLK_CLR = '#3b82f6'   # blue
MOSI_CLR = '#22c55e'   # green
LABEL    = '#e2e8f0'
DIM      = '#64748b'
BYTE_COLORS = ['#ef4444', '#f97316', '#a855f7']  # red, orange, purple for bytes

fig, axes = plt.subplots(3, 1, figsize=(16, 7), sharex=True,
                         gridspec_kw={'height_ratios': [1, 1, 1.3], 'hspace': 0.05})
fig.patch.set_facecolor(BG)
for ax in axes:
    ax.set_facecolor(BG)
    ax.tick_params(colors=LABEL, labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_yticks([])

# ── Time axis: 1 µs per clock cycle, 24 clocks for 3 bytes ──
# Add padding before and after
t_pad = 3
t_total = t_pad + 24 + t_pad  # 30 total units

# ── CS (active low) ──
ax = axes[0]
cs_t = [0, t_pad-0.5, t_pad-0.5, t_pad+24+0.5, t_pad+24+0.5, t_total]
cs_v = [1, 1, 0, 0, 1, 1]
ax.plot(cs_t, cs_v, color=CS_CLR, linewidth=2.5, solid_capstyle='round')
ax.fill_between(cs_t, cs_v, 0, alpha=0.08, color=CS_CLR)
ax.set_ylim(-0.3, 1.6)
ax.set_ylabel('CS', color=CS_CLR, fontsize=13, fontweight='bold', rotation=0, labelpad=35, va='center')
# Annotations
ax.annotate('CS asserted (LOW)', xy=(t_pad, 0), xytext=(t_pad+3, 1.3),
            color=CS_CLR, fontsize=9, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=CS_CLR, lw=1.2))
ax.annotate('CS released (HIGH)', xy=(t_pad+24+0.5, 1), xytext=(t_pad+19, 1.3),
            color=CS_CLR, fontsize=9, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=CS_CLR, lw=1.2))

# ── SCLK (idle low, pulses during transfer) ──
ax = axes[1]
sclk_t = [0]
sclk_v = [0]
for i in range(24):
    t_start = t_pad + i
    # Rising edge
    sclk_t.extend([t_start, t_start])
    sclk_v.extend([0, 1])
    # Falling edge
    sclk_t.extend([t_start + 0.5, t_start + 0.5])
    sclk_v.extend([1, 0])
sclk_t.append(t_total)
sclk_v.append(0)
ax.plot(sclk_t, sclk_v, color=SCLK_CLR, linewidth=2, solid_capstyle='round')
ax.fill_between(sclk_t, sclk_v, 0, alpha=0.06, color=SCLK_CLR)
ax.set_ylim(-0.3, 1.6)
ax.set_ylabel('SCLK', color=SCLK_CLR, fontsize=13, fontweight='bold', rotation=0, labelpad=35, va='center')

# Rising edge sample markers (every rising edge)
for i in range(24):
    t_rise = t_pad + i
    ax.plot(t_rise, 1, 'v', color='#fbbf24', markersize=4, alpha=0.6)

ax.text(t_pad + 12, 1.35, '↑ Data sampled on rising edges', color='#fbbf24',
        fontsize=8, ha='center', fontstyle='italic')

# ── MOSI (data, changes on falling edge) ──
ax = axes[2]

# Example data: Channel 0 (0x00), Pulse 1500µs (0x05, 0xDC)
byte_vals = [0x00, 0x05, 0xDC]
byte_names = ['Channel ID', 'Pulse µs [15:8]', 'Pulse µs [7:0]']
all_bits = []
for bv in byte_vals:
    for bit in range(7, -1, -1):
        all_bits.append((bv >> bit) & 1)

# Draw MOSI waveform
mosi_t = [0, t_pad - 0.2]
mosi_v = [0, 0]  # idle before CS

for i, bit in enumerate(all_bits):
    t_start = t_pad + i
    # Data changes on falling edge (previous), stable before rising
    if i == 0:
        mosi_t.extend([t_pad - 0.2, t_pad - 0.2])
        mosi_v.extend([0, bit])
    else:
        prev_t = t_pad + i - 0.5  # at previous falling edge
        mosi_t.extend([prev_t, prev_t])
        mosi_v.extend([all_bits[i-1], bit])
    
    mosi_t.append(t_start + 0.5)  # hold through rising edge
    mosi_v.append(bit)

# End
mosi_t.extend([t_pad + 24, t_pad + 24, t_total])
mosi_v.extend([all_bits[-1], 0, 0])

ax.plot(mosi_t, mosi_v, color=MOSI_CLR, linewidth=2, solid_capstyle='round')
ax.fill_between(mosi_t, mosi_v, 0, alpha=0.06, color=MOSI_CLR)
ax.set_ylim(-1.2, 2.0)
ax.set_ylabel('MOSI', color=MOSI_CLR, fontsize=13, fontweight='bold', rotation=0, labelpad=35, va='center')

# Byte boundary boxes and labels
for byte_idx in range(3):
    t_start = t_pad + byte_idx * 8
    t_end = t_start + 8
    clr = BYTE_COLORS[byte_idx]
    
    # Background highlight
    ax.axvspan(t_start - 0.2, t_end - 0.2, alpha=0.07, color=clr)
    
    # Byte label on top
    ax.text((t_start + t_end) / 2 - 0.2, 1.65, f'Byte {byte_idx}',
            color=clr, fontsize=10, fontweight='bold', ha='center')
    ax.text((t_start + t_end) / 2 - 0.2, 1.35,
            f'{byte_names[byte_idx]}',
            color=clr, fontsize=8, ha='center', fontstyle='italic')
    ax.text((t_start + t_end) / 2 - 0.2, -0.55,
            f'0x{byte_vals[byte_idx]:02X}',
            color=clr, fontsize=10, fontweight='bold', ha='center',
            family='monospace')

    # Bit labels
    for bit_idx in range(8):
        t_bit = t_start + bit_idx
        bit_val = all_bits[byte_idx * 8 + bit_idx]
        ax.text(t_bit + 0.15, -0.85, str(bit_val),
                color=DIM, fontsize=7, ha='center', family='monospace')
    
    # Byte boundaries (dashed vertical lines)
    ax.axvline(t_start - 0.2, color=clr, linewidth=0.8, linestyle='--', alpha=0.4)

ax.axvline(t_pad + 24 - 0.2, color=BYTE_COLORS[2], linewidth=0.8, linestyle='--', alpha=0.4)

# Bit position labels (MSB/LSB)
for byte_idx in range(3):
    t_start = t_pad + byte_idx * 8
    ax.text(t_start + 0.15, -1.05, 'MSB', color=DIM, fontsize=6, ha='center')
    ax.text(t_start + 7.15, -1.05, 'LSB', color=DIM, fontsize=6, ha='center')

# ── X-axis labels ──
ax.set_xlim(0, t_total)
ax.set_xlabel('Clock Cycles (1 µs each @ 1 MHz)', color=DIM, fontsize=9)

# Clock cycle numbers
for i in range(24):
    axes[1].text(t_pad + i + 0.25, -0.2, str(i+1), color=DIM, fontsize=6, ha='center')

# ── Title ──
fig.suptitle('SPI Mode 0 Timing — VIGIL-RQ Servo Command (3-byte frame)',
             color=LABEL, fontsize=15, fontweight='bold', y=0.97)

# ── Legend ──
legend_elements = [
    mpatches.Patch(facecolor=CS_CLR, alpha=0.5, label='CS (Chip Select) — Active LOW'),
    mpatches.Patch(facecolor=SCLK_CLR, alpha=0.5, label='SCLK — 1 MHz, idle LOW'),
    mpatches.Patch(facecolor=MOSI_CLR, alpha=0.5, label='MOSI — Data RPi→FPGA, MSB first'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3,
           facecolor=BG, edgecolor=DIM, labelcolor=LABEL, fontsize=9,
           bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0.06, 0.06, 1, 0.95])
plt.savefig('d:/Desktop/kutta/control/docs/spi_timing.png',
            dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
print("Saved: d:/Desktop/kutta/control/docs/spi_timing.png")
plt.close()
