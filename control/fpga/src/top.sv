// ============================================================================
// top.sv — Top-level module for VIGIL-RQ PWM controller
//
// Tang Nano 9K (GW1NR-9C) — Gowin EDA
//
// Maps:
//   - On-board 27 MHz oscillator → system clock
//   - SPI signals from RPi 4B (SCLK, MOSI, CS)
//   - 12× PWM outputs to GPIO header pins (active after level shifting)
//   - On-board LED[0] as heartbeat indicator
//
// Pin assignments are defined in tangnano9k.cst
// ============================================================================

module top (
    input  logic        clk_27m,     // 27 MHz on-board crystal oscillator

    // On-board user button (active low) used as reset
    input  logic        btn_rst_n,   // S1 button on Tang Nano 9K

    // SPI interface from Raspberry Pi 4B
    input  logic        spi_sclk,
    input  logic        spi_mosi,
    input  logic        spi_cs_n,

    // 12× PWM outputs to servo level shifters
    output logic [11:0] pwm_out,

    // On-board LED (active low on Tang Nano 9K)
    output logic [5:0]  led           // 6 on-board LEDs
);

    // ── Reset synchroniser ──
    // Synchronise the async button reset into the clock domain
    logic rst_n_sync1, rst_n_sync2;

    always_ff @(posedge clk_27m or negedge btn_rst_n) begin
        if (!btn_rst_n) begin
            rst_n_sync1 <= 1'b0;
            rst_n_sync2 <= 1'b0;
        end else begin
            rst_n_sync1 <= 1'b1;
            rst_n_sync2 <= rst_n_sync1;
        end
    end

    wire rst_n = rst_n_sync2;

    // ── Heartbeat LED ──
    // Blinks LED[0] at ~1 Hz to indicate FPGA is alive
    logic [24:0] heartbeat_counter;
    always_ff @(posedge clk_27m or negedge rst_n) begin
        if (!rst_n)
            heartbeat_counter <= '0;
        else
            heartbeat_counter <= heartbeat_counter + 1'b1;
    end

    // LEDs are active-low on Tang Nano 9K
    // LED[0] = heartbeat (blinks ~1 Hz, 27M / 2^24 ≈ 1.6 Hz)
    // LED[1] = SPI CS active indicator (lit when CS is low = data transfer)
    // LED[2:5] = off
    assign led[0] = ~heartbeat_counter[24];
    assign led[1] = spi_cs_n;       // Active-low: lit during SPI transfer
    assign led[2] = 1'b1;           // Off
    assign led[3] = 1'b1;           // Off
    assign led[4] = 1'b1;           // Off
    assign led[5] = 1'b1;           // Off

    // ── PWM Controller instantiation ──
    pwm_controller u_pwm_controller (
        .clk        (clk_27m),
        .rst_n      (rst_n),
        .spi_sclk   (spi_sclk),
        .spi_mosi   (spi_mosi),
        .spi_cs_n   (spi_cs_n),
        .pwm_out    (pwm_out)
    );

endmodule
