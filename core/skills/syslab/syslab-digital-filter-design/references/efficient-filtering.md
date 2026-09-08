# Efficient Filtering for Narrow Transitions

Use this guide when a single-stage FIR starts getting expensive or the user asks for a lower-cost implementation.

## When to open this guide

Read this file when any of these are true:

- The transition band is unusually narrow
- The user asks for a more efficient implementation
- `designmethods(...)` exposes `ifir` or `multistage`
- A straightforward FIR design produces a very long filter

## First check

Compute the constraining transition width:

- Lowpass: `delta_f = Fstop - Fpass`
- Highpass: `delta_f = Fpass - Fstop`
- Bandpass: `delta_f = min(Fpass1 - Fstop1, Fstop2 - Fpass2)`
- Bandstop: `delta_f = min(Fstop1 - Fpass1, Fpass2 - Fstop2)`

Then compute:

```text
trans_pct = 100 * delta_f / Fs
```

Use this rule of thumb:

| `trans_pct` | Guidance |
|---|---|
| `> 5%` | Single-stage is usually fine |
| `2%` to `5%` | Mention efficient alternatives if cost matters |
| `< 2%` | Efficient alternatives are worth evaluating |

## Architecture screen

Apply this elimination logic before choosing an implementation:

- If strict linear phase is required, do not default to elliptic or other causal IIR paths.
- If the task is offline and zero phase is acceptable, an IIR plus `filtfilt`-style application strategy may still be viable.
- If streaming is required, prefer causal realizations and report the phase tradeoff explicitly.
- If constant-rate FIR is preferred and `ifir` is supported, compare IFIR against direct FIR rather than assuming one-stage FIR is the only linear-phase option.

## Main options

### Option 1: Single-stage IIR

Best when:

- Phase linearity is not required
- The user wants minimum order
- Offline zero-phase can be achieved by a separate application strategy

Typical Julia path:

```julia
using TyDSPSystem

spec = fdesign_lowpass("Fp,Fst,Ap,Ast", 500, 650, 0.5, 60, 4000)
filt = design(spec, "ellip", "MatchExactly", "passband", "SystemObject", true)
```

### Option 2: IFIR

Best when:

- The transition is narrow
- Constant sample rate is preferred
- `ifir` is available and the user wants an FIR-style efficient solution

Typical Julia path:

```julia
using TyDSPSystem

h, g = ifir(6, "low", [0.12 0.14], [0.01 0.001])
```

### Option 3: Single-stage FIR

Best when:

- Simplicity matters more than compute cost
- Linear phase is required
- The tap count is still manageable

Typical Julia path:

```julia
using TySignalProcessing

fs = 22050.0
taps = remez(400, [0, 8000, 8100, 0.5 * fs], [1, 0]; fs = fs)
```

## Recommended evaluation order

1. Compute `trans_pct`
2. Screen by mode and phase requirements
3. Inspect `designmethods(...)` if spec-driven exploration is justified
4. Compare only the candidate architectures that survive the screen
5. Verify each candidate with `fvtool`, `freqz`, or equivalent numeric checks
6. Explain why the chosen path is cheaper, simpler, or more faithful to the phase requirement

## What to say explicitly

When recommending an efficient path, state:

- Why the straightforward design is costly
- What alternatives were considered and why any were excluded
- What tradeoff is introduced, such as non-linear phase or more design complexity
- Which numeric metric supports the decision, such as tap count, stopband margin, or group-delay variation

## Verification

Do not stop after generating taps or a system object. At minimum:

```julia
using TySignalProcessing

fs = 1000.0
b, a = butter(6, 300 / (fs / 2))
fvtool(b, a; SampleRates = fs)
```
