using TyDSPSystem
using TySignalProcessing

fs = 4000
spec = fdesign_lowpass("Fp,Fst,Ap,Ast", 500, 650, 0.5, 60, fs)
methods = designmethods(spec, "SystemObject", true)
println("methods=", methods)
filt = design(spec, "ellip", "MatchExactly", "passband", "SystemObject", true)
println("filter_type=", typeof(filt))
fvtool(filt; SampleRates=fs)
