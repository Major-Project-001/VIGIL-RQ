// ============================================================================
// pwm_controller.sv — 12-channel PWM controller with SPI slave interface
//
// VIGIL-RQ Quadruped Robot — Tang Nano 9K (GW1NR-9C)
//
// Integrates:
//   - 1× spi_slave   (receives servo commands from RPi)
//   - 12× pwm_channel (generates independent PWM outputs)
//
// SPI frame: [channel_id (8-bit)] [pulse_width_us (16-bit big-endian)]
// Converts µs → clock ticks internally (multiply by 27 for 27 MHz clock).
//
// Includes a watchdog timer: if no SPI command is received within
// WATCHDOG_TIMEOUT clock cycles, all channels reset to neutral (1500 µs).
// ============================================================================

module pwm_controller (
    input  logic        clk,        // 27 MHz system clock
    input  logic        rst_n,      // Active-low reset

    // SPI interface
    input  logic        spi_sclk,
    input  logic        spi_mosi,
    input  logic        spi_cs_n,

    // 12× PWM outputs
    output logic [11:0] pwm_out
);

    // ── Constants ──
    localparam int unsigned NUM_CHANNELS = 12;

    // Neutral pulse width: 1500 µs × 27 ticks/µs = 40,500 ticks
    localparam int unsigned NEUTRAL_TICKS = 40_500;

    // Watchdog timeout: 500 ms at 27 MHz = 13,500,000 cycles
    localparam int unsigned WATCHDOG_TIMEOUT = 13_500_000;

    // ── SPI slave output signals ──
    logic        spi_data_valid;
    logic [3:0]  spi_channel_id;
    logic [15:0] spi_pulse_us;

    // ── Per-channel pulse width registers (in clock ticks) ──
    logic [16:0] pulse_ticks [NUM_CHANNELS];

    // ── Watchdog counter ──
    logic [23:0] watchdog_counter;
    logic        watchdog_expired;

    // ── SPI Slave instance ──
    spi_slave u_spi_slave (
        .clk        (clk),
        .rst_n      (rst_n),
        .spi_sclk   (spi_sclk),
        .spi_mosi   (spi_mosi),
        .spi_cs_n   (spi_cs_n),
        .data_valid  (spi_data_valid),
        .channel_id  (spi_channel_id),
        .pulse_us    (spi_pulse_us)
    );

    // ── Microseconds → clock ticks conversion ──
    // pulse_ticks = pulse_us × 27
    // Max: 2500 × 27 = 67,500 (fits in 17 bits)
    //
    // Multiply by 27: x*27 = x*32 - x*4 - x = (x << 5) - (x << 2) - x
    // This avoids a hardware multiplier.
    function automatic logic [16:0] us_to_ticks(input logic [15:0] us);
        logic [20:0] x32, x4, x1;
        x32 = {us, 5'b0};       // us << 5 = us * 32
        x4  = {5'b0, us, 2'b0}; // us << 2 = us * 4
        x1  = {5'b0, us};       // us * 1
        return (x32 - x4 - x1);
    endfunction

    // ── Channel register update logic ──
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all channels to neutral
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                pulse_ticks[i] <= NEUTRAL_TICKS[16:0];
            end
            watchdog_counter <= '0;
            watchdog_expired <= 1'b0;
        end else begin
            // Watchdog counter
            if (spi_data_valid) begin
                watchdog_counter <= '0;
                watchdog_expired <= 1'b0;
            end else if (watchdog_counter >= WATCHDOG_TIMEOUT[23:0]) begin
                watchdog_expired <= 1'b1;
            end else begin
                watchdog_counter <= watchdog_counter + 1'b1;
            end

            // Update channel or reset on watchdog
            if (watchdog_expired) begin
                // Safety: reset all to neutral
                for (int i = 0; i < NUM_CHANNELS; i++) begin
                    pulse_ticks[i] <= NEUTRAL_TICKS[16:0];
                end
            end else if (spi_data_valid && spi_channel_id < NUM_CHANNELS[3:0]) begin
                // Valid channel update
                pulse_ticks[spi_channel_id] <= us_to_ticks(spi_pulse_us);
            end
        end
    end

    // ── PWM channel instances ──
    genvar g;
    generate
        for (g = 0; g < NUM_CHANNELS; g++) begin : gen_pwm
            pwm_channel u_pwm (
                .clk         (clk),
                .rst_n       (rst_n),
                .pulse_width (pulse_ticks[g]),
                .pwm_out     (pwm_out[g])
            );
        end
    endgenerate

endmodule
