# SPDX-FileCopyrightText: © 2026 Nino
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


async def step_and_settle(dut):
    """Advance one clock cycle, then let the DUT's updates settle before
    reading. cocotb's RisingEdge/ClockCycles resumes at the exact instant of
    the clock edge, with no guarantee it runs after the DUT's own
    posedge-triggered always block (RTL) or standard-cell propagation delays
    (gate-level netlist, built with UNIT_DELAY=#1 per cell) have settled for
    that edge — reading immediately can see a stale, one-cycle-old value. A
    settle delay after the edge (not after driving inputs) forces the read
    into a later time step. 10ns (10% of the 100ns clock period) covers a
    multi-gate propagation chain in gate-level sim while leaving 90ns of
    margin before the next edge."""
    await ClockCycles(dut.clk, 1)
    await Timer(10, unit="ns")


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
    await step_and_settle(dut)

    dut._log.info("Counter is zero after reset")
    assert dut.uo_out.value == 0

    dut._log.info("Counter increments while ui_in[0] is high")
    dut.ui_in.value = 1  # ui_in[0] = 1, all other input bits 0
    expected = 0
    for _ in range(20):
        await step_and_settle(dut)
        expected = (expected + 1) & 0xFF
        assert dut.uo_out.value == expected

    dut._log.info("Counter holds while ui_in[0] is low")
    dut.ui_in.value = 0
    for _ in range(5):
        await step_and_settle(dut)
        assert dut.uo_out.value == expected

    dut._log.info("Counter wraps from 255 to 0")
    dut.ui_in.value = 1
    remaining = 256 - expected
    for _ in range(remaining):
        await step_and_settle(dut)
    assert dut.uo_out.value == 0
