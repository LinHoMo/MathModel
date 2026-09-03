# Multirate and Efficient Design Card

Open this card before using `ifir` or when the user asks for very narrow transitions, efficient implementations, or multistage ideas.

## Indicators

- Transition band is unusually narrow
- FIR tap count is growing too large
- The user asks for lower compute cost
- The user explicitly asks for IFIR or multistage design

## Canonical IFIR pattern

```julia
using TyDSPSystem

h, g = ifir(6, "low", [0.12 0.14], [0.01 0.001])
```

## Rules

- Treat IFIR as a specialized optimization path, not the default first answer.
- Prefer `TySignalProcessing` direct FIR or IIR design first, and move to IFIR or multistage only when those direct functions cannot satisfy the user's efficiency or transition-band requirements.
- Use spec-driven exploration only when you need to confirm whether `ifir` or `multistage` is supported for the given design intent.
- Explain the tradeoff between implementation cost and design complexity.
- Verify the final response with `fvtool` or `freqz`, not only coefficient inspection.
