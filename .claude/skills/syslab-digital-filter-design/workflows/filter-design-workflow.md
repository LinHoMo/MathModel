# Julia Filter Design Workflow

Use this guide when the task is broader than one API call and you need a repeatable workflow.

## Core principles

### Always pin the frequency convention

- If the user gives Hz, require `Fs`.
- If the user omits `Fs`, do not silently switch to Hz-based code.
- For direct-design functions such as `butter`, `cheby1`, `cheby2`, `ellip`, and FIR helpers, convert Hz to normalized frequency with `f / (Fs / 2)` when required by the API.
- For spec-driven design, use `fdesign_*` constructors that accept `Fs` directly.

### Hard-stop on missing design intent

Do not continue to architecture selection if any of these are missing and the answer would change:

- `Fs` for Hz-based requests
- `streaming` versus `offline`
- Phase intent for tasks where zero-phase, linear-phase, or causal IIR behavior matter
- Core edge frequencies, ripple, attenuation, or order limits

### Match workflow to problem shape

- Prefer `TySignalProcessing` direct-design functions for most practical FIR and IIR work.
- Use `butter`, `cheby1`, `cheby2`, `ellip`, `remez`, or `firpm` when the family is known or a direct coefficient design is sufficient.
- Use `fdesign_* -> designmethods -> designoptions -> design` when you need method discovery, spec objects, or `SystemObject` output.
- Use `fvtool`, `freqz`, `grpdelay`, and `zplane` to verify the result instead of stopping at coefficient generation.

### Separate architecture from implementation

- First decide FIR or IIR, phase behavior, and whether the task is offline or streaming.
- Then choose the concrete API and output form.
- Prefer `design(..., "SystemObject", true)` when the result needs to be deployed as a running filter object.

## Standard response structure

Every completed filter-design answer should include:

1. A concise spec recap
2. The chosen architecture and why
3. A Julia script that runs with the Syslab Julia CLI resolved by `syslab-environment`
4. At least one verification call
5. Any important tradeoff such as phase distortion, tap count, or implementation form
6. Numeric acceptance checks when hard specs were given

## Minimal validation workflow

### Direct IIR design

```julia
using TySignalProcessing

fs = 1000.0
b, a = butter(6, 300 / (fs / 2))
h, w = freqz(b, a, 1024, fs)
fvtool(b, a; SampleRates = fs)
```

### FIR minimax design

```julia
using TySignalProcessing

fs = 22050.0
taps = remez(400, [0, 8000, 8100, 0.5 * fs], [1, 0]; fs = fs)
freqz(taps, 1, 1024, fs; plotfig = true)
```

### Spec-driven design when a system object is needed

```julia
using TyDSPSystem
using TySignalProcessing

spec = fdesign_lowpass("Fp,Fst,Ap,Ast", 500, 650, 0.5, 60, 4000)
methods = designmethods(spec, "SystemObject", true)
filt = design(spec, "ellip", "MatchExactly", "passband", "SystemObject", true)
fvtool(filt; SampleRates = 4000)
```

## Quantitative acceptance template

When specs are explicit, report the corresponding numeric checks, not only plots:

- Passband ripple in dB across the accepted passband region
- Maximum stopband level or minimum stopband attenuation in dB
- Group-delay variation when phase or alignment matters
- Any before-versus-after comparison when proposing compensation or efficient alternatives

Typical FIR ripple and stopband check:

```julia
h, w = freqz(taps, 1, 4096, fs)
mag_db = 20 .* log10.(max.(abs.(h), eps()))
pass_idx = findall(w .<= fpass)
stop_idx = findall(w .>= fstop)
pass_ripple_db = maximum(mag_db[pass_idx]) - minimum(mag_db[pass_idx])
stop_max_db = maximum(mag_db[stop_idx])
```

## Decision hints

### Prefer IIR when:

- The user wants a compact implementation
- Phase linearity is not required
- The transition is narrow and efficiency matters

### Prefer FIR when:

- Linear phase matters
- The user explicitly wants equiripple or Remez design
- A long tap vector is acceptable

### Escalate to efficient methods when:

- The transition band is very narrow relative to `Fs`
- FIR length becomes large enough to dominate compute cost
- The user asks for multistage, IFIR, or lower-cost implementations

Then read `../references/efficient-filtering.md`.

## GUI guidance

- `filterDesigner()` can be used as a GUI entry point.
- In this skill, prefer the bundled launcher script `../scripts/launch_filterDesigner_patched.jl`.
- Do not keep retrying the GUI path if it errors. Reproduce the same task through code immediately.
