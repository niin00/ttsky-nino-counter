<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

An 8-bit PWM generator. A free-running 8-bit period counter increments every clock cycle
regardless of any input. The duty cycle is set by `ui_in[7:0]` and is latched into an internal
register on a rising edge of `uio_in[0]`; changing `ui_in` has no effect until the next rising
edge of `uio_in[0]`. The PWM output is high whenever the period counter is less than the
latched duty value, giving an exact 0% duty at `duty == 0`; since an 8-bit duty compared
against an 8-bit counter can reach at most 255/256 high cycles, `duty == 0xFF` is special-cased
to a constant-high output for an exact 100% duty. `uo_out[0]` carries the PWM output, and
`uo_out[7:1]` mirrors the period counter's upper 7 bits so the waveform is directly observable
on the demo board's LEDs. Reset is active-low and synchronous; it clears the period counter and
the latched duty to 0. The bidirectional IOs are configured as inputs, with only `uio_in[0]`
used (as the duty-latch trigger).

## How to test

Hold `rst_n` low for a few clock cycles to reset, then release it. Set `ui_in` to the desired
duty cycle (0-255) and pulse `uio_in[0]` from low to high to latch it in — the PWM output on
`uo_out[0]` and the period counter's MSBs on `uo_out[7:1]` will reflect the new duty starting
from the next period. Changing `ui_in` without pulsing `uio_in[0]` has no effect on the output.

## External hardware

None.
