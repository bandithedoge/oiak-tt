# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Pin mapping (from project.v):
    #   ui_in[0]     = a.first  (1 bit)
    #   ui_in[2:1]   = a.second (2 bits)
    #   ui_in[6:3]   = a.third  (4 bits)
    #   ui_in[7]     = algo_select (0=mdf, 1=phase_sum)
    #   uio_in[0]    = b.first  (1 bit)
    #   uio_in[2:1]  = b.second (2 bits)
    #   uio_in[6:3]  = b.third  (4 bits)
    #
    # Only first 3 residues are pin-accessible. fourth/fifth/sixth = 0.
    # MDF requires all 6 residues for correct comparison; only equality
    # is reliable through the wrapper. Phase-sum is more robust with
    # partial data.

    def pack_operand(first, second, third):
        return (first & 0x1) | ((second & 0x3) << 1) | ((third & 0xF) << 3)

    async def set_and_read(ui_val, uio_val):
        dut.ui_in.value = ui_val
        dut.uio_in.value = uio_val
        await ClockCycles(dut.clk, 1)
        return int(dut.uo_out.value) & 0x7

    async def check_eq(a_first, a_second, a_third,
                       b_first, b_second, b_third,
                       algo_name, algo_bit, label):
        """Check that equal encodings produce eq=1."""
        ui_val = pack_operand(a_first, a_second, a_third) | (algo_bit << 7)
        uio_val = pack_operand(b_first, b_second, b_third)
        result = await set_and_read(ui_val, uio_val)
        lt = (result >> 0) & 1
        eq = (result >> 1) & 1
        gt = (result >> 2) & 1
        dut._log.info(f"  {algo_name} {label}: lt={lt} eq={eq} gt={gt}")
        assert eq == 1, f"{algo_name} {label}: expected eq, got lt={lt} eq={eq} gt={gt}"

    async def check_phase_sum(a_first, a_second, a_third,
                              b_first, b_second, b_third,
                              expected, label):
        """Check phase-sum comparison (more robust with partial residues)."""
        ui_val = pack_operand(a_first, a_second, a_third) | (1 << 7)
        uio_val = pack_operand(b_first, b_second, b_third)
        result = await set_and_read(ui_val, uio_val)
        lt = (result >> 0) & 1
        eq = (result >> 1) & 1
        gt = (result >> 2) & 1
        dut._log.info(f"  phase_sum {label}: lt={lt} eq={eq} gt={gt} (expected {expected})")
        assert (lt, eq, gt) == expected, \
            f"phase_sum {label}: got ({lt},{eq},{gt}), expected {expected}"

    # --- MDF equality tests ---
    dut._log.info("Testing MDF equality (select=0)")
    await check_eq(0, 0, 0, 0, 0, 0, "MDF", 0, "0==0")
    await check_eq(1, 1, 1, 1, 1, 1, "MDF", 0, "1==1")
    await check_eq(1, 2, 5, 1, 2, 5, "MDF", 0, "5==5")
    await check_eq(0, 1, 10, 0, 1, 10, "MDF", 0, "10==10")

    # --- Phase-sum equality tests ---
    dut._log.info("Testing phase-sum equality (select=1)")
    await check_eq(0, 0, 0, 0, 0, 0, "phase_sum", 1, "0==0")
    await check_eq(1, 1, 1, 1, 1, 1, "phase_sum", 1, "1==1")
    await check_eq(1, 2, 5, 1, 2, 5, "phase_sum", 1, "5==5")
    await check_eq(0, 1, 10, 0, 1, 10, "phase_sum", 1, "10==10")

    # --- Phase-sum comparison tests (more reliable with partial residues) ---
    dut._log.info("Testing phase-sum comparisons (select=1)")
    # a=0, b=1 (lt)
    await check_phase_sum(0, 0, 0, 1, 1, 1, (1, 0, 0), "0<1")
    # a=1, b=0 (gt)
    await check_phase_sum(1, 1, 1, 0, 0, 0, (0, 0, 1), "1>0")

    dut._log.info("All tests passed!")
