fs = 8.0e9;
fst1 = 0.9e9;
fp1 = 1.0e9;
fp2 = 2.0e9;
fst2 = 2.1e9;
Ap = 1.0;
Ast1 = 60.0;
Ast2 = 60.0;
npts = 4096;

% Design the IIR bandpass filter from explicit specs.
spec = fdesign.bandpass('Fst1,Fp1,Fp2,Fst2,Ast1,Ap,Ast2', fst1, fp1, fp2, fst2, Ast1, Ap, Ast2, fs);
methods = designmethods(spec, 'SystemObject', true);
disp('bandpass_methods=');
disp(methods);

bp = design(spec, 'ellip', 'MatchExactly', 'passband', 'SystemObject', true);
disp(class(bp));

[bpNum, bpDen] = tf(bp);

% Design an allpass compensator from the in-band group-delay profile.
fpassNorm = linspace(fp1 / (fs / 2), fp2 / (fs / 2), 401);
gdBp = grpdelay(bpNum, bpDen, fpassNorm, 2);
desiredRelativeDelay = max(gdBp) - gdBp;

apOrder = 10;
[apNum, apDen, tau] = iirgrpdelay(apOrder, fpassNorm, [fpassNorm(1) fpassNorm(end)], desiredRelativeDelay);
fprintf('allpass_tau=%g\n', tau);
fprintf('allpass_is_allpass=%d\n', isallpass(apNum, apDen));

% Cascade in transfer-function form.
cascadeNum = conv(bpNum, apNum);
cascadeDen = conv(bpDen, apDen);

% Numeric verification.
[~, f] = freqz(bpNum, bpDen, npts, fs);
gdBpFull = grpdelay(bpNum, bpDen, npts, fs);
gdCascade = grpdelay(cascadeNum, cascadeDen, npts, fs);

passbandMask = (f >= fp1) & (f <= fp2);
bpSpan = max(gdBpFull(passbandMask)) - min(gdBpFull(passbandMask));
cascadeSpan = max(gdCascade(passbandMask)) - min(gdCascade(passbandMask));
fprintf('passband_group_delay_span_before=%g\n', bpSpan);
fprintf('passband_group_delay_span_after=%g\n', cascadeSpan);

% Plot magnitude comparison.
[hBp, fMag] = freqz(bpNum, bpDen, npts, fs);
hCascade = freqz(cascadeNum, cascadeDen, npts, fs);
figure;
plot(fMag / 1e9, 20 * log10(abs(hBp)), fMag / 1e9, 20 * log10(abs(hCascade)));
grid on;
xlabel('Frequency (GHz)');
ylabel('Magnitude (dB)');
legend('Bandpass only', 'Bandpass cascaded with allpass', 'Location', 'best');
title('IIR bandpass magnitude response');

% Plot group delay comparison.
figure;
plot(f / 1e9, gdBpFull, f / 1e9, gdCascade);
grid on;
xlabel('Frequency (GHz)');
ylabel('Group delay (samples)');
legend('Bandpass only', 'Bandpass cascaded with allpass', 'Location', 'best');
title('Group delay comparison');

% Visual verification in FVTool.
fvtool(bpNum, bpDen, cascadeNum, cascadeDen, 'Analysis', 'freq', 'Fs', fs);
fvtool(bpNum, bpDen, cascadeNum, cascadeDen, 'Analysis', 'grpdelay', 'Fs', fs);
