# Draft: TT's example `test.py` idiom is silently unsafe for sequential designs

**Status: draft only. Not filed. Left for the repo owner to review and decide where (if anywhere) to send it.**

## Summary

Tiny Tapeout's Verilog templates (checked `ttsky-verilog-template` and
`ttihp-verilog-template`) ship an example `test/test.py` that drives inputs and
checks outputs immediately after `await ClockCycles(dut.clk, 1)`. This pattern
gives correct results for the templates' own placeholder design (a purely
combinational `uo_out = ui_in + uio_in`), but silently returns a *stale,
one-cycle-old* value for any design with registered/clocked outputs — which is
effectively every real ASIC submission. New users who follow the template
literally and write a sequential design will see assertion failures that look
exactly like a broken design ("my counter doesn't count"), when the actual
defect is in the inherited test scaffolding, not their RTL.

**Important context found before writing this**: the underlying simulation
mechanism is not novel and is not undocumented in general — it's cocotb's own
documented behavior (see "Prior art," below), explained clearly on cocotb's
own docs site with the exact same illustrative example (a flip-flop read via
`RisingEdge`) used here. What appears to be missing is any connection between
that documentation and Tiny Tapeout's own templates/tutorials, which ship the
unsafe pattern with no cross-reference or warning.

## Prior art (checked before drafting this)

- **cocotb's official "Timing Model" docs**
  (`docs.cocotb.org/en/stable/timing_model.html`) state, verbatim: *"After
  returning, an edge trigger returns at the point where the signal or
  variable given to the trigger will have changed value, but no HDL that
  reacts to that value change will have executed... Using a flip-flop for
  example, after an `await RisingEdge(dut.clk)`, `dut.clk` will be `1`, but
  the output of the flip-flop will remain the previous value."* This is the
  exact mechanism below, already documented by the tool's own authors.
- **cocotb GitHub Discussion #3877** ("COCOTB + Verilator reads stale signal
  values when on clock posedge") — a maintainer (ktbarrett) explains the same
  mechanism for a real user-reported case, with the same fix (`ReadOnly()`).
- **cocotb GitHub Discussion #3282** ("Should I be using FallingEdge to set
  and assert values?") — discusses a third approach (asserting on
  `FallingEdge` instead of `RisingEdge`), with an important caveat: a
  `FallingEdge`-only assertion scheme was shown to pass for a design with a
  *combinational* bug (`assign q = d` instead of a real flip-flop), because
  the values happened to coincide at that sampling phase. Not a safe
  substitute on its own.
- **Not found anywhere**: any Tiny Tapeout issue, PR, discussion, or docs page
  (checked `tinytapeout.com/hdl/testing/`, the `ttsky-verilog-template` and
  `ttihp-verilog-template` repos, and searched TinyTapeout's GitHub org)
  connecting this to TT's own templates. TT's testing guide mentions "a delay
  is also inserted in-between setting the input, and checking the output,"
  but this refers to the one-cycle `ClockCycles` wait itself, not a
  settle-margin fix for registered outputs — consistent with the fact that
  the design it's demonstrated on is combinational and never needed one.

So: report the mechanism as already well-documented (by cocotb, not by us),
but the gap connecting it to Tiny Tapeout's templates as real and, as far as
we could find, unreported.

## Minimal reproducer

The smallest sequential circuit that exhibits this — a single toggle
flip-flop, no inputs beyond clock and reset:

```verilog
// toggle.v
`default_nettype none
module toggle (
    input  wire clk,
    input  wire rst_n,
    output reg  q
);
  always @(posedge clk) begin
    if (!rst_n)
      q <= 1'b0;
    else
      q <= ~q;
  end
endmodule
```

```verilog
// tb.v
`timescale 1ns/1ps
module tb ();
  reg clk;
  reg rst_n;
  wire q;
  toggle dut (.clk(clk), .rst_n(rst_n), .q(q));
endmodule
```

```python
# test_naive.py — the TT-template-style pattern, applied to a sequential design
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_toggle_naive(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    # q should have toggled from 0 to 1 on this edge:
    assert dut.q.value == 1, f"expected q=1, got {int(dut.q.value)}"
```

Run with Icarus Verilog 13.0 + cocotb 2.0.1: **fails**, `expected q=1, got 0`,
even though the RTL is correct and `q` genuinely does toggle on that edge (a
`$display` inside the `always` block confirms this independently of cocotb).
Verified locally before writing this draft — this is not a claim taken on
faith.

## The mechanism, with actual confidence levels

We got this wrong twice before landing on the right explanation. Recording
that honestly, because it's informative about how misleading the symptom is:

1. **First guess (wrong, falsified by direct evidence): a cocotb write-scheduling
   race.** Theory: a `.value =` write issued right after resuming from
   `ClockCycles` gets deferred to a time step that coincides with the *next*
   edge, racing the flip-flop's own sample. Falsified by inserting a settle
   delay between the write and the next `ClockCycles` call and observing
   **zero change** in the failure — identical timestamps before and after,
   proving the delay was absorbed into existing slack before an
   already-distant edge rather than resolving any race at an edge boundary.

2. **Second guess (wrong, actively misleading): a `` `timescale `` mismatch.**
   Adding a `$display` with a raw `%0t` inside the design showed timestamps
   1000x larger than cocotb's reported nanosecond values, which looked like
   compelling evidence of a picosecond/nanosecond unit mismatch between
   compiled files. This was a red herring: a bare `%0t` prints the *design's
   single global time precision* (here, picoseconds, since the testbench
   declares `` `timescale 1ns/1ps ``); cocotb's own logger separately
   reformats the identical instant into human-readable nanoseconds. Two
   different presentations of the same value, not a mismatch. Confirmed
   wrong by testing the fix (adding a matching `` `timescale `` directive to
   the design file) locally and observing no change in behavior.

3. **Third explanation (high confidence — confirmed by direct experiment,
   and now additionally corroborated by cocotb's own documentation cited
   above): `RisingEdge`/`ClockCycles` resumes at the exact simulation instant
   the clock edge is detected, with no guarantee that other processes also
   sensitive to that same edge — including the DUT's own
   `always @(posedge clk)` block — have executed and applied their
   non-blocking assignments yet.** Confirmed by adding a `$display` inside
   the RTL's own always-block: the internal register updates correctly on
   *every single cycle* with zero missed increments (ground truth, from the
   simulator's perspective), while a Python-side read one line after the
   corresponding `ClockCycles` call is consistently one edge behind. This is
   standard, intentional Verilog delta-cycle simulation semantics — cocotb's
   docs confirm it isn't a bug, using literally the same flip-flop example
   independently arrived at here.

## Proposed fix: two options, with tradeoffs

### Option A — settle delay (`Timer` after the edge, before the read)

```python
async def step_and_settle(dut):
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")  # margin AFTER the edge, not after driving inputs
```

- **Pro**: simple, one line, no phase restrictions — you can freely drive new
  stimulus immediately afterward.
- **Con**: it's a heuristic wall-clock margin, not a simulator guarantee. The
  correct value is design/simulation-dependent (see gate-level note below),
  and picking one that's "obviously enough" without understanding why is easy
  to get wrong — we did, initially, by placing the delay in the wrong
  position (after the write instead of after the edge), which had no effect
  and cost real debugging time before we noticed the timestamps hadn't moved.

### Option B — `await ReadOnly()`

```python
from cocotb.triggers import ClockCycles, ReadOnly

await ClockCycles(dut.clk, 1)
await ReadOnly()
value = dut.q.value  # guaranteed to reflect this edge's settled state
```

- **Pro**: this is the simulator-guaranteed synchronization point (per
  cocotb's own docs: entered "when the current timestep no longer has any
  further delta steps... all signal values are stable"). Not a magic number;
  works identically regardless of RTL vs. gate-level timing.
- **Con**: `ReadOnly()` is a strict phase — cocotb raises
  `RuntimeError: Attempting settings a value during the ReadOnly phase.` if
  you try to write a `.value` immediately afterward, before a new time step
  begins. Test code that interleaves driving new stimulus and checking
  outputs every cycle (a common pattern) has to be restructured so writes
  never happen while still inside a `ReadOnly()`-synchronized point from the
  previous iteration — usually by only calling `ReadOnly()` right before a
  read that has no immediately-following same-timestep write, or by using
  `NextTimeStep()` to explicitly move past it when a write is needed next.

Both options were verified against the minimal reproducer above before
writing this section.

## RTL vs. gate-level: the margin isn't one-size-fits-all

Using Option A (settle delay) specifically: a margin that works for RTL
simulation does not necessarily work for gate-level (post-synthesis) sign-off
against the same test. TT's own template `test/Makefile` builds the
gate-level netlist with `COMPILE_ARGS += -DUNIT_DELAY=\#1`, meaning every
standard cell in the synthesized netlist carries a real `#1` propagation
delay; a multi-gate path (flip-flop plus buffering) can need more simulated
time to settle than the zero-delay RTL case ever does. In our case, a 1ns
margin worked for RTL but reproduced the identical stale-read failure
(shifted by exactly the added 1ns) against the gate-level netlist; widening
to 10ns (10% of our 100ns clock period) fixed it.

**That 10ns number is an unverified guess, and should be labeled as such if
this is ever turned into a real recommendation.** It was chosen by reasoning
about the `UNIT_DELAY` directive, not by measuring the actual propagation
depth of any specific synthesized netlist (no local PDK was available to
reproduce `GATES=yes` outside CI), and confirmed only by a single passing CI
run, not by understanding the true worst-case gate chain length. Option B
(`ReadOnly()`) sidesteps this entire class of problem, since it isn't a
margin at all — that's a real argument in its favor for anyone hardening this
into template guidance, despite its write-ordering awkwardness.

## Suggested next step (not taken here)

If this gets filed anywhere, the most useful and least presumptuous form is
probably a documentation addition to the templates' `test/test.py` comments
and/or `tinytapeout.com/hdl/testing/`, pointing at cocotb's existing Timing
Model docs and showing the settle-delay or `ReadOnly()` pattern next to the
current combinational example — rather than a claim of a new bug, since
there isn't one in cocotb itself.
