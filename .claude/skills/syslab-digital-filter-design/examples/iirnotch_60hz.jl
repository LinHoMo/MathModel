using TyDSPSystem
using TySignalProcessing

fs = 300.0
f0 = 60.0
q = 35.0
w0 = f0 / (fs / 2)
bw = w0 / q
b, a = iirnotch(w0, bw)
println("b_len=", length(b), ", a_len=", length(a))
h, w = freqz(b, a, 1024, fs)
println("resp_len=", length(h), ", freq_len=", length(w))
fvtool(b, a; SampleRates=fs)
