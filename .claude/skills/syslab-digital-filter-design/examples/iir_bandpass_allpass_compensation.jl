using TyDSPSystem
using TySignalProcessing
using TyPlot
using TyMath

# Example goal:
# Design an IIR bandpass filter for 8 GHz sampling, passband 1-2 GHz,
# then cascade an allpass compensator to reduce in-band group-delay variation.
#
# Assumptions added for a complete runnable example:
# - Stopband edges: 0.9 GHz and 2.1 GHz
# - Passband ripple: 1 dB
# - Stopband attenuation: 60 dB

fs = 8.0e9
fst1 = 0.9e9
fp1 = 1.0e9
fp2 = 2.0e9
fst2 = 2.1e9
ap = 1.0
ast1 = 60.0
ast2 = 60.0
npts = 4096

spec = fdesign_bandpass(
    "Fst1,Fp1,Fp2,Fst2,Ast1,Ap,Ast2", fst1, fp1, fp2, fst2, ast1, ap, ast2, fs
)
methods = designmethods(spec, "SystemObject", true)
println("bandpass_methods=", methods)

bp = design(spec, "ellip", "MatchExactly", "passband", "SystemObject", true)
println("bandpass_filter_type=", typeof(bp))

bp_num, bp_den = sos2tf(bp.SOSMatrix, bp.ScaleValues)

# Design the allpass compensator from the passband group-delay profile.
# A higher allpass order improves the in-band variation reduction for this example.
fpass_norm = collect(range(fp1 / (fs / 2), fp2 / (fs / 2); length=401))
gd_bp, = grpdelay(bp_num, bp_den, fpass_norm, 2)
desired_relative_delay = maximum(gd_bp) .- gd_bp

ap_order = 20
weights = ones(length(fpass_norm))
weights[2:end-1] .*= 4
ap_num, ap_den, tau = iirgrpdelay(
    ap_order,
    fpass_norm,
    [fpass_norm[1], fpass_norm[end]],
    desired_relative_delay,
    weights,
    0.999,
)
println("allpass_tau=", tau)
println("allpass_is_allpass=", isallpass(ap_num, ap_den))

# Transfer-function cascade: H_total(z) = H_bp(z) * H_ap(z)
cascade_num = conv(bp_num, ap_num)
cascade_den = conv(bp_den, ap_den)

# Numeric verification
h_bp, f = freqz(bp_num, bp_den, npts, fs)
h_cascade, = freqz(cascade_num, cascade_den, npts, fs)
gd_bp_full, f_gd = grpdelay(bp_num, bp_den, npts, fs)
gd_cascade, = grpdelay(cascade_num, cascade_den, npts, fs)

passband_mask = (f_gd .>= fp1) .& (f_gd .<= fp2)
bp_span = maximum(gd_bp_full[passband_mask]) - minimum(gd_bp_full[passband_mask])
cascade_span = maximum(gd_cascade[passband_mask]) - minimum(gd_cascade[passband_mask])
println("passband_group_delay_span_before=", bp_span)
println("passband_group_delay_span_after=", cascade_span)
println("passband_group_delay_improvement_pct=", 100 * (bp_span - cascade_span) / bp_span)

# Plot frequency response and group-delay comparison.
figure()
plot(f ./ 1e9, 20 .* log10.(abs.(h_bp)), f ./ 1e9, 20 .* log10.(abs.(h_cascade)))
grid("on")
xlabel("Frequency (GHz)")
ylabel("Magnitude (dB)")
legend(["Bandpass only", "Bandpass with allpass compensation"])
title("IIR bandpass magnitude response")

figure()
plot(f_gd ./ 1e9, gd_bp_full, f_gd ./ 1e9, gd_cascade)
grid("on")
xlabel("Frequency (GHz)")
ylabel("Group delay (samples)")
legend(["Bandpass only", "Bandpass with reduced delay variation"])
title("Group delay variation comparison")

# Visual verification in FVTool.
fvtool(bp_num, bp_den, cascade_num, cascade_den; Analysis="freq", SampleRates=fs)
fvtool(bp_num, bp_den, cascade_num, cascade_den; Analysis="grpdelay", SampleRates=fs)
