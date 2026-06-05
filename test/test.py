# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    dut._log.info("Test MDF comparison")

    # uo_out[0]=lt, uo_out[1]=eq, uo_out[2]=gt (from explicit field assignment)
    dut.ui_in.value = 5
    dut.uio_in.value = 3
    await ClockCycles(dut.clk, 2)
    dut._log.info(f"a=5 b=3: uo_out = {dut.uo_out.value}")
    assert dut.uo_out.value == 0b100

    dut.ui_in.value = 3
    dut.uio_in.value = 5
    await ClockCycles(dut.clk, 2)
    dut._log.info(f"a=3 b=5: uo_out = {dut.uo_out.value}")
    assert dut.uo_out.value == 0b001

    dut.ui_in.value = 7
    dut.uio_in.value = 7
    await ClockCycles(dut.clk, 2)
    dut._log.info(f"a=7 b=7: uo_out = {dut.uo_out.value}")
    assert dut.uo_out.value == 0b010

    dut.ui_in.value = 0x0F
    dut.uio_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    dut._log.info(f"a=15 b=0: uo_out = {dut.uo_out.value}")
    assert dut.uo_out.value == 0b100

    dut._log.info("All tests passed!")
