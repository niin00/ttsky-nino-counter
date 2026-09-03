<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

An 8-bit synchronous up counter. On each rising edge of `clk`, if `rst_n` is low the counter
resets to 0; otherwise, if `ui_in[0]` is high the counter increments by 1 (wrapping from 255
back to 0), and if `ui_in[0]` is low the counter holds its current value. The count is driven
out continuously on `uo_out`. All other input bits and the bidirectional IOs are unused.

## How to test

Hold `rst_n` low for a few clock cycles to reset the counter to 0, then release it. Drive
`ui_in[0]` high to count up on every clock cycle, or low to pause the counter. Observe the
count on `uo_out`.

## External hardware

None.
