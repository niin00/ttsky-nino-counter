/*
 * Copyright (c) 2026 Nino
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_nino_pwm (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  reg [7:0] period_count;  // free-running PWM period counter
  reg [7:0] duty;          // latched duty cycle
  reg       uio_in0_prev;  // previous uio_in[0], for rising-edge detection

  wire uio_in0_rise = uio_in[0] & ~uio_in0_prev;

  always @(posedge clk) begin
    if (!rst_n) begin
      period_count <= 8'd0;
      duty         <= 8'd0;
      // Seed with the current input level rather than a fixed 0, so a level
      // that's already high when reset releases isn't mistaken for a rising
      // edge on the very next cycle.
      uio_in0_prev <= uio_in[0];
    end else begin
      period_count <= period_count + 8'd1;
      uio_in0_prev <= uio_in[0];
      if (uio_in0_rise)
        duty <= ui_in;
    end
  end

  // count < duty gives an exact 0% at duty==0. An 8-bit duty compared
  // against an 8-bit counter can't reach exact 100% this way (255/256 at
  // best), so duty==8'hFF is special-cased to a constant-high output.
  wire pwm = (period_count < duty) | (&duty);

  assign uo_out  = {period_count[7:1], pwm};
  assign uio_out = 8'd0;
  assign uio_oe  = 8'd0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in[7:1], 1'b0};

endmodule
