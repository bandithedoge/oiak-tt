{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  buildInputs = with pkgs; [
    yosys
    iverilog
    gnumake
    python3
    python3Packages.cocotb
    python3Packages.pytest
  ];
}
