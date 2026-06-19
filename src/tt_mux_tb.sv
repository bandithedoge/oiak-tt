`include "rns_types.sv"

module tt_mux_tb;

  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

  tt_um_mdf_demo dut (
    .ui_in   (ui_in),
    .uo_out  (uo_out),
    .uio_in  (uio_in),
    .uio_out (uio_out),
    .uio_oe  (uio_oe),
    .ena     (ena),
    .clk     (clk),
    .rst_n   (rst_n)
  );

  integer errors;
  integer tests;

  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  initial begin
    errors = 0;
    tests = 0;

    rst_n = 0;
    ena = 1;
    ui_in = 0;
    uio_in = 0;

    repeat (10) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    // --- Test 1: MDF equality (algo_select=0) ---
    $display("[Test 1] MDF equality (algo_select=0)");

    ui_in = 8'b0000_0000 | (0 << 7);  // a=0
    uio_in = 8'b0000_0000;             // b=0
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: MDF 0==0: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b0101_0011 | (0 << 7);  // a=1 (first=1,second=1,third=1)
    uio_in = 8'b0101_0011;             // b=1
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: MDF 1==1: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b1010_0101 | (0 << 7);  // a=5 (first=1,second=2,third=5)
    uio_in = 8'b1010_0101;             // b=5
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: MDF 5==5: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    // --- Test 2: Phase-sum equality (algo_select=1) ---
    $display("[Test 2] Phase-sum equality (algo_select=1)");

    ui_in = 8'b0000_0000 | (1 << 7);  // a=0
    uio_in = 8'b0000_0000;             // b=0
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: phase_sum 0==0: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b0101_0011 | (1 << 7);  // a=1
    uio_in = 8'b0101_0011;             // b=1
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: phase_sum 1==1: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b1010_0101 | (1 << 7);  // a=5
    uio_in = 8'b1010_0101;             // b=5
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: phase_sum 5==5: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    // --- Test 3: Phase-sum ordering (algo_select=1) ---
    $display("[Test 3] Phase-sum ordering (algo_select=1)");

    ui_in = 8'b0000_0000 | (1 << 7);  // a=0
    uio_in = 8'b0101_0011;             // b=1
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b001) begin
      $display("  FAIL: phase_sum 0<1: got %b, expected 001", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b0101_0011 | (1 << 7);  // a=1
    uio_in = 8'b0000_0000;             // b=0
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b100) begin
      $display("  FAIL: phase_sum 1>0: got %b, expected 100", uo_out[2:0]);
      errors = errors + 1;
    end

    // --- Test 4: MUX switching — same inputs, both algorithms ---
    $display("[Test 4] MUX switching (same inputs, different algorithm)");

    ui_in = 8'b0000_0000 | (0 << 7);  // a=0, mdf
    uio_in = 8'b0101_0011;             // b=1
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b001) begin
      $display("  FAIL: MUX mdf 0<1: got %b, expected 001", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b0000_0000 | (1 << 7);  // a=0, phase_sum
    uio_in = 8'b0101_0011;             // b=1
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b001) begin
      $display("  FAIL: MUX phase_sum 0<1: got %b, expected 001", uo_out[2:0]);
      errors = errors + 1;
    end

    // --- Test 5: MUX toggle — flip select, same data ---
    $display("[Test 5] MUX toggle (flip select, same data)");

    ui_in = 8'b1010_0101 | (0 << 7);  // a=5, mdf
    uio_in = 8'b1010_0101;             // b=5
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: toggle mdf 5==5: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    ui_in = 8'b1010_0101 | (1 << 7);  // a=5, phase_sum
    uio_in = 8'b1010_0101;             // b=5
    @(posedge clk); #1;
    tests = tests + 1;
    if (uo_out[2:0] !== 3'b010) begin
      $display("  FAIL: toggle phase_sum 5==5: got %b, expected 010", uo_out[2:0]);
      errors = errors + 1;
    end

    // --- Test 6: Output pins unaffected by select ---
    $display("[Test 6] Unused outputs are zero");
    ui_in = 8'b0101_0011 | (1 << 7);
    uio_in = 8'b0000_0000;
    @(posedge clk); #1;

    tests = tests + 1;
    if (uo_out[7:3] !== 5'b0) begin
      $display("  FAIL: uo_out[7:3] = %b, expected 0", uo_out[7:3]);
      errors = errors + 1;
    end
    tests = tests + 1;
    if (uio_out !== 8'b0) begin
      $display("  FAIL: uio_out = %b, expected 0", uio_out);
      errors = errors + 1;
    end
    tests = tests + 1;
    if (uio_oe !== 8'b0) begin
      $display("  FAIL: uio_oe = %b, expected 0", uio_oe);
      errors = errors + 1;
    end

    $display("SUMMARY: %0d tests, %0d errors", tests, errors);
    if (errors == 0) $display("ALL PASSED");
    else begin
      $display("FAILURES DETECTED");
      $finish(1);
    end
    $finish;
  end

endmodule
