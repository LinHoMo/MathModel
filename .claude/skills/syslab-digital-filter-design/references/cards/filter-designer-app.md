# Filter Designer App Card

Open this card before using `filterDesigner()`.

## Purpose

`filterDesigner()` opens the GUI application for filter design and analysis.

## Preferred bundled launcher in this skill

```julia
# run: ../../scripts/launch_filterDesigner_patched.jl
```

## Canonical package-level pattern

```julia
using TyFilterDesigner

filterDesigner()
```

## Rules

- Use the app when the user explicitly wants GUI-based exploration, manual tuning, or export workflows.
- Prefer code-based design for reproducible answers, automation, and verification.
- In this skill, prefer the bundled patched launcher over bare `filterDesigner()` because logger initialization may fail in the current environment.
- If the GUI path errors, do not keep retrying. Fall back to `fdesign_*`, `design`, `fvtool`, and other code-based APIs.
- If the user asks for a GUI path, still provide the equivalent Julia code when possible.
- The app is not a substitute for final scripted validation.

## Shared Help Routing

- Shared Julia help root: `<SYSLAB_HOME>/Tools/AIAssets/projects`
- `TySignalProcessing/App/TySignalProcessing/FilterDesigner.md`
- `TySignalProcessing/App/TySignalProcessing/GettingStartedwithFilterDesigner.md`
- `TyDSPSystem/Doc/TyDSPSystem/FilterDesignAndAnalysis/FilterAnalysis/filterDesigner.md`

## Deliverables after app use

- Record the chosen response type, method, and key specs
- Reproduce the final design in Julia code
- Verify with `fvtool`, `freqz`, `grpdelay`, or related analysis APIs
- Report the numeric checks that matter for the stated specs
