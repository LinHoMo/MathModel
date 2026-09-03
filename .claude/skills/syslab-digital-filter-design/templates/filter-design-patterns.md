# Julia Filter Design Patterns

Use this file for copyable Julia templates that are known to match the current implementation path.

## Direct Butterworth design in Hz

```julia
using TySignalProcessing

fs = 1000.0
fc = 300.0
b, a = butter(6, fc / (fs / 2))
h, w = freqz(b, a, 1024, fs)
fvtool(b, a; SampleRates = fs)
```

## Direct bandpass IIR design in Hz

```julia
using TySignalProcessing

fs = 8.0e9
passband = [1.0e9, 2.0e9]
b, a = ellip(8, 1, 60, passband ./ (fs / 2), "bandpass")
fvtool(b, a; SampleRates = fs)
```

## Direct highpass design with zero-pole-gain output

```julia
using TySignalProcessing

fs = 1000.0
z, p, k = butter(9, 300 / (fs / 2), "highpass"; otype = "zpk")
```

## FIR minimax lowpass with `remez`

```julia
using TySignalProcessing

fs = 22050.0
cutoff = 8000.0
trans_width = 100.0
numtaps = 400
taps = remez(numtaps, [0, cutoff, cutoff + trans_width, 0.5 * fs], [1, 0]; fs = fs)

freqz(taps, 1, 2000, fs; plotfig = true)
```

## Spec-driven lowpass, system-object output

```julia
using TyDSPSystem
using TySignalProcessing

fs = 4000
spec = fdesign_lowpass("Fp,Fst,Ap,Ast", 500, 650, 0.5, 60, fs)
methods = designmethods(spec, "SystemObject", true)
opts = designoptions(spec, "ellip", "SystemObject", true)
filt = design(spec, "ellip", "MatchExactly", "passband", "SystemObject", true)

fvtool(filt; SampleRates = fs)
```

## IFIR for narrow-transition lowpass

```julia
using TyDSPSystem

h, g = ifir(6, "low", [0.12 0.14], [0.01 0.001])
```

## GUI-assisted exploration in this skill

Run the bundled launcher file:

```julia
# run: ../scripts/launch_filterDesigner_patched.jl
```

## Package-level GUI pattern

```julia
using TyFilterDesigner

filterDesigner()
```

Use the GUI pattern only when the user explicitly wants app-based interaction. In this skill, prefer the bundled patched launcher. If initialization fails, fall back to the code patterns above.
