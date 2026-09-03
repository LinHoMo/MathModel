using TyDSPSystem
using TySignalProcessing

fs = 4000
spec = fdesign_bandstop(
    "Fp1,Fst1,Fst2,Fp2,Ap1,Ast,Ap2", 500, 700, 900, 1100, 0.5, 60, 0.5, fs
)
methods = designmethods(spec, "SystemObject", true)
println("methods=", methods)
filt = design(spec, "ellip", "SystemObject", true)
println("filter_type=", typeof(filt))
fvtool(filt; SampleRates=fs)
