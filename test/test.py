# SPDX-FileCopyrightText: © 2026 Nino
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz), matching info.yaml's clock_hz
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("Counter is zero after reset")
    assert dut.uo_out.value == 0

    dut._log.info("Counter increments while ui_in[0] is high")
    dut.ui_in.value = 1  # ui_in[0] = 1, all other input bits 0
    expected = 0
    for _ in range(20):
        await ClockCycles(dut.clk, 1)
        expected = (expected + 1) & 0xFF
        assert dut.uo_out.value == expected

    dut._log.info("Counter holds while ui_in[0] is low")
    dut.ui_in.value = 0
    for _ in range(5):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == expected

    dut._log.info("Counter wraps from 255 to 0")
    dut.ui_in.value = 1
    remaining = 256 - expected
    await ClockCycles(dut.clk, remaining)
    assert dut.uo_out.value == 0
