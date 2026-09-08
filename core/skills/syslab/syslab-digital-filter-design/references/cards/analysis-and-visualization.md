# Analysis and Visualization Card

Open this card before using `fvtool`, `freqz`, `grpdelay`, `phasez`, `zplane`, or `zerophase`.

## Rules

- When `Fs` is known, pass it so plots are displayed in physical units rather than only normalized frequency.
- Use `fvtool` for quick comparison and richer filter visualization.
- Use `freqz` for programmable checks and custom numeric verification.
- Use `grpdelay` and `phasez` when phase behavior matters.
- Use `zplane` for pole-zero inspection of IIR designs.
- If the user supplied explicit ripple, attenuation, or delay requirements, report those metrics numerically instead of relying on plots alone.

## Canonical patterns

```julia
using TySignalProcessing

fs = 1000.0
b, a = butter(6, 300 / (fs / 2))
fvtool(b, a; SampleRates = fs)
```

```julia
h, w = freqz(b, a, 1024, fs)
```

```julia
fvtool(b, a; Analysis = "grpdelay", SampleRates = fs)
```

## Numeric verification template

```julia
h, w = freqz(b, a, 4096, fs)
mag_db = 20 .* log10.(max.(abs.(h), eps()))
pass_idx = findall(w .<= fpass)
stop_idx = findall(w .>= fstop)
pass_ripple_db = maximum(mag_db[pass_idx]) - minimum(mag_db[pass_idx])
stop_max_db = maximum(mag_db[stop_idx])
```

```julia
gd, f_gd = grpdelay(b, a, 4096, fs)
passband_mask = (f_gd .>= fp1) .& (f_gd .<= fp2)
gd_span = maximum(gd[passband_mask]) - minimum(gd[passband_mask])
```

## Common analysis values

- `Analysis = "magnitude"`
- `Analysis = "phase"`
- `Analysis = "freq"`
- `Analysis = "grpdelay"`
- `Analysis = "phasedelay"`
- `Analysis = "impulse"`
- `Analysis = "step"`
- `Analysis = "polezero"`
