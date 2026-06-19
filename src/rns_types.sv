`ifndef RNS_TYPES_SV
`define RNS_TYPES_SV

typedef struct packed {
  logic lt;
  logic eq;
  logic gt;
} out_t;

typedef struct packed {
  logic [3:0] first;
  logic [3:0] second;
  logic [4:0] third;
  logic [4:0] fourth;
  logic [4:0] fifth;
  logic [15:0] sixth;
} rns_t;

`endif
