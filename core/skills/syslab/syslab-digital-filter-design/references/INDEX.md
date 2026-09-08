# Reference Index

Read the mapped card before using the corresponding Julia API or workflow.

Use the paired shared help page when you need exact syntax, parameters, return values, app steps, or supported options.
All help-page paths below are relative to `<SYSLAB_HOME>/Tools/AIAssets/projects`.

## Function-level routing

| Function or pattern | Read first |
|---|---|
| `filterDesigner()` | `cards/filter-designer-app.md` |
| `fvtool(...)` | `cards/analysis-and-visualization.md` |
| `freqz`, `grpdelay`, `phasez`, `zplane`, `zerophase` | `cards/analysis-and-visualization.md` |
| `butter`, `cheby1`, `cheby2`, `ellip` | `cards/direct-iir-design.md` |
| `remez`, `firpm`, `firpmord` | `cards/fir-equiripple-remez.md` |
| `fdesign_*` plus `design(...)` | `cards/spec-driven-design.md` |
| `designmethods(...)`, `designoptions(...)` | `cards/spec-driven-design.md` |
| `ifir`, narrow-transition lowpass or highpass | `cards/multirate-and-efficient-design.md` |

## Shared Help Routing

| Topic | Read under the shared help root |
|---|---|
| GUI startup and Filter Designer behavior | `TySignalProcessing/App/TySignalProcessing/FilterDesigner.md`, `TySignalProcessing/App/TySignalProcessing/GettingStartedwithFilterDesigner.md` |
| `filterDesigner` API details | `TyDSPSystem/Doc/TyDSPSystem/FilterDesignAndAnalysis/FilterAnalysis/filterDesigner.md` |
| `fvtool` usage | `TySignalProcessing/Doc/TySignalProcessing/DigitalAndAnalogFilters/DigitalFilterAnalysis/fvtool.md`, `TyDSPSystem/Doc/TyDSPSystem/FilterDesignAndAnalysis/FilterDesign/fvtool.md` |
| Direct IIR design | `TySignalProcessing/Doc/TySignalProcessing/DigitalAndAnalogFilters/DigitalFilterDesign/` |
| `fdesign_*`, `design`, `designmethods`, `designoptions` | `TyDSPSystem/Doc/TyDSPSystem/FilterDesignAndAnalysis/FilterDesign/` |
| `freqz`, `grpdelay`, `phasez`, `zplane`, `zerophase` | `TySignalProcessing/Doc/TySignalProcessing/DigitalAndAnalogFilters/DigitalFilterAnalysis/`, `TyDSPSystem/Doc/TyDSPSystem/FilterDesignAndAnalysis/FilterAnalysis/` |
| Multirate operations such as `upfirdn`, `resample`, `interp`, `decimate` | `TySignalProcessing/Doc/TySignalProcessing/DigitalAndAnalogFilters/MultirateSignalProcessing/` |

## Task-level routing

| Trigger or task | Read first |
|---|---|
| User wants app-based exploration or export from GUI | `cards/filter-designer-app.md` |
| User asks for Butterworth, Chebyshev, elliptic, IIR, or direct coefficient design | `cards/direct-iir-design.md` |
| User asks for equiripple, minimax, Parks-McClellan, Remez, or `firpm` | `cards/fir-equiripple-remez.md` |
| User has ripple and attenuation specs and wants method discovery or a `SystemObject` | `cards/spec-driven-design.md` |
| User wants verification, comparison, or plots | `cards/analysis-and-visualization.md` |
| User wants methodology, validation discipline, or end-to-end workflow | `../workflows/filter-design-workflow.md` |
| User wants copyable templates for common tasks | `../templates/filter-design-patterns.md` |
| Transition band is very narrow or user asks for multistage or IFIR efficiency | `cards/multirate-and-efficient-design.md`, then `efficient-filtering.md` |

## Suggested defaults

- Prefer direct FIR/IIR design functions from `TySignalProcessing` for most practical design tasks.
- Prefer `design(..., "SystemObject", true)` only when IIR deployment, streaming use, or method exploration makes system objects the better fit.
- Prefer `fvtool(...; SampleRates=Fs)` or `freqz(..., Fs)` style verification when `Fs` is known.
- Prefer `fdesign_*` only when the spec-object workflow adds real value.
- If `filterDesigner()` fails during GUI startup, switch immediately to the code-driven path.
