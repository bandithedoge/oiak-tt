`include "rns_types.sv"

module phase_sum (
    output out_t out,
    input  rns_t a,
    input  rns_t b
);
  localparam [32:0] first = 33'd4294967296;
  localparam [31:0] second = 32'd2863311530;
  localparam [29:0] third = 780903144;
  localparam [28:0] fourth = 373475417;
  localparam [28:0] fifth = 277094664;
  localparam [17:0] sixth = 182543;

  logic [35:0] p0a, p1a, p2a, p3a, p4a, p5a;
  logic [35:0] p0b, p1b, p2b, p3b, p4b, p5b;
  logic [36:0] sa_l, sa_m, sa_h;
  logic [36:0] sb_l, sb_m, sb_h;

  assign p0a = {32'b0, a.first} * first;
  assign p1a = {31'b0, a.second} * {1'b0, second};
  assign p2a = {29'b0, a.third} * {3'b0, third};
  assign p3a = {28'b0, a.fourth} * {4'b0, fourth};
  assign p4a = {28'b0, a.fifth} * {4'b0, fifth};
  assign p5a = {17'b0, a.sixth} * {15'b0, sixth};

  assign p0b = {32'b0, b.first} * first;
  assign p1b = {31'b0, b.second} * {1'b0, second};
  assign p2b = {29'b0, b.third} * {3'b0, third};
  assign p3b = {28'b0, b.fourth} * {4'b0, fourth};
  assign p4b = {28'b0, b.fifth} * {4'b0, fifth};
  assign p5b = {17'b0, b.sixth} * {15'b0, sixth};

  assign sa_l = p0a + p1a;
  assign sa_m = p2a + p3a;
  assign sa_h = p4a + p5a;

  assign sb_l = p0b + p1b;
  assign sb_m = p2b + p3b;
  assign sb_h = p4b + p5b;

  assign out.lt = (sa_l + sa_m + sa_h) < (sb_l + sb_m + sb_h);
  assign out.eq = (sa_l + sa_m + sa_h) == (sb_l + sb_m + sb_h);
  assign out.gt = (sa_l + sa_m + sa_h) > (sb_l + sb_m + sb_h);

endmodule
