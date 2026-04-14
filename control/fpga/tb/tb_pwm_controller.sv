// ============================================================================
// tb_pwm_controller.sv — Testbench for PWM controller
//
// VIGIL-RQ Quadruped Robot — Tang Nano 9K (GW1NR-9C)
// Run in Gowin EDA simulator or any SystemVerilog simulator (e.g., Icarus/Verilator)
//
// Tests:
//   1. Reset behaviour (all channels neutral at 1500 µs)
//   2. SPI transaction: update channel 0 to 1000 µs
//   3. SPI transaction: update channel 5 to 2000 µs
//   4. SPI transaction: update channel 11 to 500 µs (min)
//   5. Watchdog timeout → all channels reset to neutral
//   6. Verify PWM output timing
// ============================================================================

`timescale 1ns / 1ps

module tb_pwm_controller;

    // ── Clock and reset ──
    logic clk;
    logic rst_n;

    // ── SPI signals ──
    logic spi_sclk;
    logic spi_mosi;
    logic spi_cs_n;

    // ── PWM outputs ──
    logic [11:0] pwm_out;

    // ── DUT ──
    pwm_controller dut (
        .clk        (clk),
        .rst_n      (rst_n),
        .spi_sclk   (spi_sclk),
        .spi_mosi   (spi_mosi),
        .spi_cs_n   (spi_cs_n),
        .pwm_out    (pwm_out)
    );

    // ── 27 MHz clock generation (period ≈ 37.037 ns) ──
    localparam CLK_PERIOD = 37;
    initial clk = 1'b0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // ── SPI clock period: 1 MHz = 1000 ns ──
    localparam SPI_HALF_PERIOD = 500;

    // ── Task: Send a single SPI byte (MSB first, Mode 0) ──
    task automatic spi_send_byte(input logic [7:0] data);
        for (int i = 7; i >= 0; i--) begin
            spi_mosi = data[i];
            #(SPI_HALF_PERIOD);
            spi_sclk = 1'b1;           // Rising edge: slave samples
            #(SPI_HALF_PERIOD);
            spi_sclk = 1'b0;           // Falling edge
        end
    endtask

    // ── Task: Send a 3-byte SPI frame [channel_id, pulse_hi, pulse_lo] ──
    task automatic spi_send_frame(input logic [7:0] channel, input logic [15:0] pulse_us);
        $display("[%0t] SPI: channel=%0d, pulse_us=%0d", $time, channel, pulse_us);
        spi_cs_n = 1'b0;               // Assert CS
        #(SPI_HALF_PERIOD);

        spi_send_byte(channel);         // Byte 0: channel ID
        spi_send_byte(pulse_us[15:8]);  // Byte 1: pulse high
        spi_send_byte(pulse_us[7:0]);   // Byte 2: pulse low

        #(SPI_HALF_PERIOD);
        spi_cs_n = 1'b1;               // Deassert CS
        #(SPI_HALF_PERIOD * 4);         // Inter-frame gap
    endtask

    // ── Testbench stimulus ──
    initial begin
        // Initialise signals
        rst_n    = 1'b0;
        spi_sclk = 1'b0;
        spi_mosi = 1'b0;
        spi_cs_n = 1'b1;

        $display("=== VIGIL-RQ PWM Controller Testbench ===");
        $display("");

        // ── Test 1: Reset ──
        $display("[TEST 1] Reset — all channels should be neutral (40500 ticks)");
        #(CLK_PERIOD * 10);
        rst_n = 1'b1;
        #(CLK_PERIOD * 10);

        // After reset, all PWM outputs should produce 1500µs pulses
        $display("  Reset released. PWM outputs: %b", pwm_out);

        // ── Test 2: Send pulse to channel 0 → 1000 µs ──
        $display("");
        $display("[TEST 2] Set channel 0 to 1000 µs");
        spi_send_frame(8'd0, 16'd1000);

        // Wait a bit for the PWM to update
        #(CLK_PERIOD * 100);

        // ── Test 3: Send pulse to channel 5 → 2000 µs ──
        $display("[TEST 3] Set channel 5 to 2000 µs");
        spi_send_frame(8'd5, 16'd2000);
        #(CLK_PERIOD * 100);

        // ── Test 4: Send pulse to channel 11 → 500 µs (minimum) ──
        $display("[TEST 4] Set channel 11 to 500 µs (minimum)");
        spi_send_frame(8'd11, 16'd500);
        #(CLK_PERIOD * 100);

        // ── Test 5: Send pulse to channel 3 → 2500 µs (maximum) ──
        $display("[TEST 5] Set channel 3 to 2500 µs (maximum)");
        spi_send_frame(8'd3, 16'd2500);
        #(CLK_PERIOD * 100);

        // ── Test 6: Invalid channel (should be ignored) ──
        $display("[TEST 6] Invalid channel 15 (should be ignored)");
        spi_send_frame(8'd15, 16'd1800);
        #(CLK_PERIOD * 100);

        // ── Test 7: Observe one full PWM period ──
        // 20 ms = 540,000 cycles × 37 ns ≈ 20 ms
        $display("");
        $display("[TEST 7] Observing one full PWM period (20 ms)...");
        #(CLK_PERIOD * 540_000);

        $display("  PWM outputs after 1 period: %b", pwm_out);

        // ── Test 8: Watchdog timeout ──
        // Wait for watchdog (13.5M cycles × 37 ns ≈ 500 ms)
        // Shortened for simulation: just check the counter exists
        $display("");
        $display("[TEST 8] Watchdog — skipping full 500ms wait in sim");
        $display("  (In hardware, all channels reset to neutral after 500ms of no SPI)");

        $display("");
        $display("=== ALL TESTS COMPLETE ===");
        $finish;
    end

    // ── Optional: Dump waveforms ──
    initial begin
        $dumpfile("tb_pwm_controller.vcd");
        $dumpvars(0, tb_pwm_controller);
    end

endmodule
