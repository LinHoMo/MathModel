# Direct IIR Design Card

Open this card before using `butter`, `cheby1`, `cheby2`, or `ellip`.

## Canonical pattern

```julia
using TySignalProcessing

fs = 1000.0
b, a = butter(6, 300 / (fs / 2))
```

## Rules

- This is the default path for most IIR design tasks in this skill.
- These functions work naturally when the order and family are already chosen, or when direct coefficient output is acceptable.
- For digital filters, normalized cutoff values are in `(0, 1)`, where `1` corresponds to Nyquist.
- If the user gives frequencies in Hz, convert with `Wn = f / (Fs / 2)` or the band equivalent.
- For bandpass and bandstop, pass a two-element vector.
- Prefer `zpk` output or a spec-driven system-object workflow for higher-order IIR when numeric robustness or deployment matters.

## Variants

```julia
z, p, k = butter(9, 300 / 500, "highpass"; otype = "zpk")
```

```julia
b, a = cheby1(6, 1, 300 / 500)
```

```julia
b, a = ellip(8, 1, 60, [0.25, 0.5], "bandpass")
```

## Verification pattern

```julia
fvtool(b, a; SampleRates = fs)
```
