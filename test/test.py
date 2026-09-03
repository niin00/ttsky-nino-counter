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


def expected_uo_out(period_count, duty):
    """Software model of the RTL: pwm = (period_count < duty) | (duty ==
    0xFF); uo_out = {period_count[7:1], pwm}, i.e. period_count with bit 0
    replaced by pwm."""
    pwm = 1 if (period_count < duty or duty == 0xFF) else 0
    return (period_count & 0xFE) | pwm


async def check(dut, period_count, duty):
    got = int(dut.uo_out.value)
    want = expected_uo_out(period_count, duty)
    assert got == want, (
        f"period_count={period_count} duty={duty}: expected uo_out="
        f"{want:#04x}, got {got:#04x}"
    )


async def reset(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await step_and_settle(dut)  # period_count is free-running: now 1, not 0


async def latch_duty(dut, duty):
    """Set ui_in to `duty` and pulse uio_in[0] low-to-high to latch it on
    the rising edge (detected during the first step below), then back low."""
    dut.ui_in.value = duty
    dut.uio_in.value = 1
    await step_and_settle(dut)
    dut.uio_in.value = 0
    await step_and_settle(dut)


@cocotb.test()
async def test_pwm(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz), matching info.yaml's clock_hz
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    dut._log.info("Reset")
    await reset(dut)
    period_count = 1
    duty = 0
    await check(dut, period_count, duty)

    dut._log.info("Period counter free-runs and reset cleared duty to 0")
    for _ in range(6):
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)

    dut._log.info("0% duty: pwm stays low for a full period")
    await latch_duty(dut, 0)
    duty = 0
    period_count = (period_count + 2) & 0xFF
    await check(dut, period_count, duty)
    for _ in range(256):
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)
        assert (int(dut.uo_out.value) & 1) == 0

    dut._log.info("100% duty: pwm stays high for a full period")
    await latch_duty(dut, 0xFF)
    duty = 0xFF
    period_count = (period_count + 2) & 0xFF
    await check(dut, period_count, duty)
    for _ in range(256):
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)
        assert (int(dut.uo_out.value) & 1) == 1

    dut._log.info("Mid duty (128): verify the high-time count over a full period")
    await latch_duty(dut, 128)
    duty = 128
    period_count = (period_count + 2) & 0xFF
    await check(dut, period_count, duty)
    high_count = 0
    for _ in range(256):
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)
        high_count += int(dut.uo_out.value) & 1
    assert high_count == 128, f"expected 128 high cycles at 50% duty, got {high_count}"

    dut._log.info("Duty change does not take effect until the latch edge")
    dut.ui_in.value = 200  # change ui_in WITHOUT pulsing uio_in[0]
    for _ in range(256):
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)  # still latched at 128

    dut._log.info("Pulsing the latch edge now applies the new duty (200)")
    dut.uio_in.value = 1
    await step_and_settle(dut)
    period_count = (period_count + 1) & 0xFF
    dut.uio_in.value = 0
    await step_and_settle(dut)
    period_count = (period_count + 1) & 0xFF
    duty = 200
    await check(dut, period_count, duty)
    for _ in range(256):
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)

    dut._log.info(
        "Latch is edge-triggered, not level-triggered: holding uio_in[0] "
        "high across multiple cycles while ui_in changes must not re-latch"
    )
    dut.ui_in.value = 10
    dut.uio_in.value = 1
    await step_and_settle(dut)  # rising edge here: duty latches to 10
    period_count = (period_count + 1) & 0xFF
    duty = 10
    await check(dut, period_count, duty)
    for new_val in (50, 90, 3):  # uio_in[0] stays high; a level-triggered
        dut.ui_in.value = new_val  # (buggy) design would re-latch each time
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)  # duty must still be 10
    dut.uio_in.value = 0
    await step_and_settle(dut)
    period_count = (period_count + 1) & 0xFF
    await check(dut, period_count, duty)

    dut._log.info(
        "Reset while uio_in[0] is already high must not cause a spurious "
        "latch of whatever ui_in happens to be at reset release"
    )
    dut.ena.value = 1
    dut.ui_in.value = 77  # must NOT end up latched
    dut.uio_in.value = 1  # already high going into and through reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await step_and_settle(dut)
    period_count = 1
    duty = 0
    await check(dut, period_count, duty)
    for _ in range(3):  # uio_in[0] stays high with no transition: no edge
        await step_and_settle(dut)
        period_count = (period_count + 1) & 0xFF
        await check(dut, period_count, duty)
    dut.uio_in.value = 0
    await step_and_settle(dut)
    period_count = (period_count + 1) & 0xFF
    await check(dut, period_count, duty)

    dut._log.info("Reset clears the period counter and the latched duty")
    await reset(dut)
    period_count = 1
    duty = 0
    await check(dut, period_count, duty)
