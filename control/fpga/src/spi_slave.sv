// ============================================================================
// spi_slave.sv — SPI slave receiver for Raspberry Pi → FPGA communication
//
// VIGIL-RQ Quadruped Robot — Tang Nano 9K (GW1NR-9C)
//
// Receives 3-byte SPI frames:
//   Byte 0: channel_id   (0–11, selects which PWM channel to update)
//   Byte 1: pulse_us_hi  (high byte of pulse width in microseconds)
//   Byte 2: pulse_us_lo  (low byte of pulse width in microseconds)
//
// SPI Mode 0: CPOL=0, CPHA=0
//   - Data sampled on rising edge of SCLK
//   - Data shifted on falling edge of SCLK
//   - CS is active-low
//
// Outputs are synchronised to the system clock domain.
// ============================================================================

module spi_slave (
    input  logic        clk,        // 27 MHz system clock
    input  logic        rst_n,      // Active-low reset

    // SPI interface (directly from RPi GPIO)
    input  logic        spi_sclk,   // SPI clock from master
    input  logic        spi_mosi,   // Master Out Slave In
    input  logic        spi_cs_n,   // Chip Select (active low)

    // Decoded output (system clock domain)
    output logic        data_valid, // Pulses HIGH for 1 system clk cycle when new data ready
    output logic [3:0]  channel_id, // Servo channel 0–11
    output logic [15:0] pulse_us    // Pulse width in microseconds (500–2500)
);

    // ── SPI clock domain: shift register ──
    // Synchronise SPI signals into system clock domain (double-flop)
    logic [2:0] sclk_sync;
    logic [2:0] cs_sync;
    logic       mosi_sync1, mosi_sync2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sclk_sync  <= 3'b000;
            cs_sync    <= 3'b111;  // CS idle high
            mosi_sync1 <= 1'b0;
            mosi_sync2 <= 1'b0;
        end else begin
            sclk_sync  <= {sclk_sync[1:0], spi_sclk};
            cs_sync    <= {cs_sync[1:0], spi_cs_n};
            mosi_sync1 <= spi_mosi;
            mosi_sync2 <= mosi_sync1;
        end
    end

    // Edge detection on synchronised SCLK
    wire sclk_rising  = (sclk_sync[2:1] == 2'b01);
    wire sclk_falling = (sclk_sync[2:1] == 2'b10);
    wire cs_active    = ~cs_sync[2];        // CS active (low)
    wire cs_rising    = (cs_sync[2:1] == 2'b01);  // CS deassert (end of frame)

    // ── Shift register: 24 bits (3 bytes) ──
    logic [23:0] shift_reg;
    logic [4:0]  bit_count;  // Counts 0–23

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= '0;
            bit_count <= '0;
        end else if (!cs_active) begin
            // CS inactive: reset for next frame
            shift_reg <= '0;
            bit_count <= '0;
        end else if (sclk_rising && cs_active) begin
            // Sample MOSI on rising SCLK edge (SPI Mode 0)
            shift_reg <= {shift_reg[22:0], mosi_sync2};
            bit_count <= bit_count + 1'b1;
        end
    end

    // ── Frame decode on CS rising edge (end of transaction) ──
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_valid <= 1'b0;
            channel_id <= '0;
            pulse_us   <= 16'd1500;  // Default neutral
        end else begin
            data_valid <= 1'b0;  // Default: no valid data

            if (cs_rising && bit_count == 5'd24) begin
                // Full 24-bit frame received
                // Byte 0 (MSB first): channel_id [23:16]
                // Byte 1: pulse_us high [15:8]
                // Byte 2: pulse_us low [7:0]
                channel_id <= shift_reg[19:16];  // Only need 4 bits (0–11)
                pulse_us   <= shift_reg[15:0];
                data_valid <= 1'b1;
            end
        end
    end

endmodule
