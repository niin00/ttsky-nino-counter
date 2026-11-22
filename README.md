![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# ttsky-nino-counter

My first chip designs on [Tiny Tapeout](https://tinytapeout.com) (SKY130), plus a log of where the template and AI coding tools went wrong.

<!-- TODO: shuttle status -->

The hardware is small. The useful part is [`friction-log.md`](friction-log.md) and [`upstream-draft.md`](upstream-draft.md). The repo was one arm of a two-week experiment looking for recurring tapeout problems that tooling and AI don't resolve.

## What's here

- **`tt_um_nino_counter`** (first design, commit `f919b73`): an 8-bit synchronous up-counter with an enable on `ui_in[0]` and an active-low synchronous reset. It's still in git history.
- **`tt_um_nino_pwm`** (current `info.yaml` and `src/`): an 8-bit PWM generator. A free-running period counter is compared against a duty value latched from `ui_in` on a rising edge of `uio_in[0]`. `duty == 0xFF` is special-cased to exactly 100%. Details are in the [datasheet](docs/info.md).

The repo is still named "counter" because the PWM design replaced the counter in place (commit `5b72d28`). Its testbench checks every cycle against a Python model of the RTL.

## The finding

The template's example `test/test.py` sets inputs, awaits `ClockCycles(...)`, then asserts on outputs immediately. That only works because the placeholder design (`uo_out = ui_in + uio_in`) is combinational. For any sequential design the read returns the previous cycle's value, and the failure (`assert 0 == 1`) looks exactly like an RTL bug. My counter failed this way, and so did the gate-level `gl_test` job.

The mechanism is documented by cocotb, not discovered here: its [timing model](https://docs.cocotb.org/en/stable/timing_model.html) uses the same flip-flop example, and discussions [#3877](https://github.com/cocotb/cocotb/discussions/3877) and [#3282](https://github.com/cocotb/cocotb/discussions/3282) cover it. The gap is that the Tiny Tapeout template ships the unsafe pattern with no pointer to that documentation. I found no existing TT issue, PR or docs page connecting the two (search log in the friction log). I did not file anything upstream; [`upstream-draft.md`](upstream-draft.md) has a minimal reproducer and two fixes (a settle delay after the edge, or `ReadOnly()`).

## What AI got wrong

Before the real cause was found, the AI assistant gave several confident, mechanism-specific root causes that were wrong: a [write-scheduling race](friction-log.md#L40), a [settle delay on the write side](friction-log.md#L42), and a [`timescale` mismatch](friction-log.md#L44) backed by a misread `%0t` print that I [retracted](friction-log.md#L46). The [actual cause](friction-log.md#L47) is the read-after-edge staleness above, and a [correction row](friction-log.md#correction--2026-11-22-final-root-cause-supersedes-earlier-rows) marks the earlier explanations as superseded. Also, rereading cocotb's docs first would have saved most of that time ([row](friction-log.md#L61)).

On the PWM, deliberately mutating the RTL [exposed two real gaps](friction-log.md#L84) in a test suite that looked thorough: edge- vs level-triggered latching was indistinguishable under the original stimulus, and the reset-time seeding of the edge detector was never exercised. Both are now covered.

## Smaller template gaps

- GitHub Pages has to be enabled by hand (Settings → Pages → Source: GitHub Actions), or the `gds` workflow's `viewer` job fails. The template links an FAQ entry but doesn't list it as a setup step.
- `fpga.yaml` ships with `branches: none`, so it never runs on push. It only runs via `workflow_dispatch`.

## Links

- [friction-log.md](friction-log.md): append-only log of what went wrong, with a classification per row
- [upstream-draft.md](upstream-draft.md): unfiled write-up of the template gap
- [docs/info.md](docs/info.md): datasheet for the PWM design
- [GDS viewer / Pages site](https://niin00.github.io/ttsky-nino-counter/)
