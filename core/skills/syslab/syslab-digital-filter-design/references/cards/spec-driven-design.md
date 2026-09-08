# Spec-Driven Design Card

Open this card before using `fdesign_*`, `designmethods`, `designoptions`, or `design`.

## Preferred workflow

```julia
using TyDSPSystem

spec = fdesign_lowpass("Fp,Fst,Ap,Ast", 500, 650, 0.5, 60, 4000)
methods = designmethods(spec, "SystemObject", true)
opts = designoptions(spec, "ellip", "SystemObject", true)
filt = design(spec, "ellip", "MatchExactly", "passband", "SystemObject", true)
```

## When to use

- The user explicitly wants the `fdesign` workflow
- The design family is not fixed yet and you need method discovery
- You need to inspect available methods or options first
- You want a `SystemObject`
- The design is easier to express as passband and stopband specs than as a direct family call

## Rules

- This is a secondary path in this skill, not the default starting point.
- Choose the appropriate `fdesign_*` constructor first.
- Use `designmethods(...)` before committing to a method if the available families are uncertain.
- Use `designoptions(...)` when you need method-specific knobs such as `MatchExactly`, structure, or scaling.
- Prefer `design(..., "SystemObject", true)` for deployable filters and high-order IIR.
- When `Fs` is known, pass it into the `fdesign_*` constructor so the specs are in Hz.
- Do not stop after `design(...)`. Verify numeric behavior with `freqz`, `grpdelay`, or equivalent checks.

## Common methods

- `butter`
- `cheby1`
- `cheby2`
- `ellip`
- `equiripple`
- `ifir`
- `kaiserwin`
- `multistage`

## Quantitative verification pattern

```julia
using TySignalProcessing

fvtool(filt; Analysis = "magnitude", SampleRates = 4000)
```

When hard specs are present, also compute passband ripple and stopband level numerically for the delivered design.
