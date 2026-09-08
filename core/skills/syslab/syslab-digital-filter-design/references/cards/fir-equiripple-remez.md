# FIR Equiripple and Remez Card

Open this card before using `remez`, `firpm`, or `firpmord`.

## When to use

- The user explicitly wants FIR equiripple or minimax design
- Linear-phase FIR is preferred
- The design is easier to express with taps, band edges, and desired gains

## Canonical `remez` pattern

```julia
using TySignalProcessing

fs = 22050.0
cutoff = 8000.0
trans_width = 100.0
numtaps = 400
taps = remez(numtaps, [0, cutoff, cutoff + trans_width, 0.5 * fs], [1, 0]; fs = fs)
```

## Rules

- `numtaps` is the tap count, not the filter order.
- `bands` must be monotone and stay within `[0, fs/2]` when `fs` is provided.
- `desired` length must match the number of passband and stopband regions.
- Use `firpm` when the user explicitly asks for that MATLAB-like API.
- Use `firpmord` for order estimation when planning, not as an unquestioned final answer.

## Verification pattern

```julia
freqz(taps, 1, 2000, fs; plotfig = true)
```
