# Friction log — Tiny Tapeout SKY130 arm

Repo: https://github.com/niin00/ttsky-nino-counter
Started: 2026-09-03

Format: | what happened | AI handled it / AI got it subtly wrong / needed human judgment | would another newcomer hit this? |

| what happened | classification | newcomer-prone? |
|---|---|---|
| Local env has no `iverilog` or `cocotb`. Per instructions, did not install; will rely on CI test.yaml for the actual functional run, and note install steps for the user. | needed human judgment (explicit instruction to defer, not a design decision) | Yes — template's own devcontainer exists precisely because host-machine setup for iverilog+cocotb+riscv toolchain is nontrivial; anyone not using the devcontainer/Codespace hits this immediately. |
| Repo name, author field, and description tone were not specified in the task and were genuine guesses (not derivable from repo/docs) — stopped and asked before creating anything, per instruction to ask rather than guess. | needed human judgment | Yes, but this is workflow-shape friction (task ambiguity), not template/CI friction — still worth recording since a newcomer would face the identical "what do I name this / who am I" blank-slate moment. |
| `gh repo create --template ... --public --clone` worked first try, no auth prompts (gh was already authenticated with repo+workflow scopes). | AI handled it | Only if they've already run `gh auth login` with the right scopes — a first-time gh user would hit an auth wall here. |

| `.github/workflows/fpga.yaml` ships with `branches: none` under its `push:` trigger — i.e. it deliberately does NOT run on push, only on manual `workflow_dispatch`. Comment in the file even says "Comment out (or remove) the following line to run the FPGA workflow on every push." Since the task asked for all four workflows green after push but also said not to silently work around failures or add unrequested scaffolding, treating "doesn't run" as a config choice rather than a bug: will push normally, then manually dispatch fpga via `gh workflow run`, leaving the file as shipped. | needed human judgment (documented in-file, not a bug, but easy to miss) | Yes, very much — a newcomer who watches `gh run watch` after pushing will see only 3 of the 4 workflows appear and reasonably think something is broken. This is a real doc/template gap: the top-level README does not mention this at all. |
| Template's own placeholder `src/project.v` already demonstrates the exact idiom SKY130 CI expects for tying off unused inputs: `wire _unused = &{sig_a, sig_b, ..., 1'b0};`. Reused this pattern rather than inventing one. | AI handled it | No — this is discoverable by reading the template file, which anyone following the instructions would do. |

| RTL design decision: when both `rst_n` (active-low) is asserted and `ui_in[0]` (count-enable) is high simultaneously, reset takes priority (checked first in the if/else chain). Spec text ("increments... when ui_in[0] is high" + "active-low synchronous reset") didn't explicitly state precedence. | needed human judgment — flagged explicitly to user before push rather than silently picking a convention | Yes — this is exactly the kind of ordering ambiguity that's easy to encode differently (enable-over-reset) without noticing, and CI/tests would pass either way if the test author makes the same assumption as the RTL author (test-matches-bug scenario). |
| Testbench clock period changed from template default (10 us / 100 kHz) to 100 ns / 10 MHz to match `clock_hz: 10000000` declared in info.yaml. Functionally irrelevant for a purely synchronous design (cocotb simulated time, not real timing), but noted as a deviation since asked to flag changes. | AI handled it, flagged for transparency | No — cosmetic, unlikely to trip anyone up, but worth naming so the reviewer isn't surprised by an unexplained diff. |

## Notes on docs / guesses (running)

(populated as encountered)
