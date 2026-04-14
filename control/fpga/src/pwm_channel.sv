// ============================================================================
// pwm_channel.sv — Single-channel PWM generator for DS3218 servos
//
// VIGIL-RQ Quadruped Robot — Tang Nano 9K (GW1NR-9C)
//
// Generates a 50 Hz PWM signal with configurable pulse width (500–2500 µs).
// At 27 MHz clock: period = 540,000 cycles, resolution ≈ 0.037 µs/tick.
//
// Inputs:
//   clk          — 27 MHz system clock
//   rst_n        — Active-low reset
//   pulse_width  — Desired pulse width in clock ticks (13,500 – 67,500)
//
// Outputs:
//   pwm_out      — PWM signal output
// ============================================================================

module pwm_channel (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [16:0] pulse_width,   // Width in clock ticks (17 bits for max 67,500)
    output logic        pwm_out
);

    // ── Parameters ──
    // 27 MHz / 50 Hz = 540,000 ticks per period
    localparam int unsigned PWM_PERIOD  = 540_000;

    // Pulse width limits in clock ticks
    // 500 µs  × 27 = 13,500 ticks (min)
    // 2500 µs × 27 = 67,500 ticks (max)
    localparam int unsigned PW_MIN = 13_500;
    localparam int unsigned PW_MAX = 67_500;

    // ── Counter ──
    logic [19:0] counter;  // 20 bits covers 540,000

    // ── Clamped pulse width ──
    logic [16:0] pw_clamped;

    // Clamp pulse width to valid range
    always_comb begin
        if (pulse_width < PW_MIN[16:0])
            pw_clamped = PW_MIN[16:0];
        else if (pulse_width > PW_MAX[16:0])
            pw_clamped = PW_MAX[16:0];
        else
            pw_clamped = pulse_width;
    end

    // ── PWM counter ──
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= '0;
        end else begin
            if (counter >= PWM_PERIOD - 1)
                counter <= '0;
            else
                counter <= counter + 1'b1;
        end
    end

    // ── PWM output: HIGH when counter < pulse_width ──
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_out <= 1'b0;
        end else begin
            pwm_out <= (counter < {3'b0, pw_clamped}) ? 1'b1 : 1'b0;
        end
    end

endmodule
