using TySignalProcessing

fs = 4000.0
numtaps = 121
cutoff = 500.0
stop = 650.0
taps = remez(numtaps, [0, cutoff, stop, 0.5 * fs], [1, 0]; fs=fs)
println("numtaps=", length(taps))
h, w = freqz(taps, 1, 1024, fs)
println("resp_len=", length(h), ", freq_len=", length(w))
fvtool(taps, 1; SampleRates=fs)
