# CPU-only float64 dense-SVD audit

Tested source `a3cba95d1c1c0df66ef5fccc3e0745ae84debc7a`, Issue #20 / Draft PR #21. **CPU diagnostic complete; historical GPU INCONCLUSIVE; previous configured FAIL remains FAIL.**

CPU `(2048,1024), geometric,float64,seed123,r8`: residual 6.9655678949048578; values-only SVD tail 6.9655678949048561; full-SVD tail 6.9655678949048623; independent total-minus-leading-energy tail 6.9655678949048792. Signed residual-reference gap 1.7763568394002505e-15, relative 2.2204460492503131e-16. CPU original500eps check PASS, not a reproduction of GPU FAIL.

Full backward residual 4.3125523489744603e-14, relative 5.7609924016161734e-15; observed U/V Gram Frobenius defects 1.6765738238562302e-13/1.3926560818898742e-13. Direct residual squared norm 48.519136098529295; math.fsum squared residual 48.519136098529373. Full raw spectra and error scales are in diagnostic.json.

Independent standard-arithmetic/dimension/norm/backward-residual model yields uncertainty 5.4370586328455709e-09 (7.2631822030899255e-10 relative to A); conditional status CONSISTENT_WITH_ROUNDOFF. This is conservative, not a formal interval certificate or scientific PASS. Proposed policy/model derivation is experiments/m8_gpu/FLOAT64_AUDIT.md. Existing M8 runner remains unchanged; no replacement500eps constant. Gross zero-candidate FAIL; inflated reference INCONCLUSIVE; compensated nonorthogonal-factor regression FAIL.

CPU serialized tensor SHA256 d77e73d6541b6be9e633f102efb91d6fe8b34bdb88c02c8e4fa325f5b4a481de; roundtrip equality verified. GPU serialized SHA256 f5b892c32d0d7259f9578f0fd1ef36172d794cdec3419d5f24084018b3d76996 differs. CPU storage bytes SHA256 2a37be205a00f1ea6adb49f345dd08a3f3ea7d2f579aa9b2c256c76504a331b4. Exact cross-runtime input reproduction is NOT established; no GPU factors were archived. The tiny GPU mismatch is plausibly finite precision but cannot be bounded from archived summaries using this new a-posteriori audit. GPU retrospective diagnosis stays INCONCLUSIVE, never PASS.

Fresh clean-clone, exact-SHA, noneditable offline installation using existing system CPU dependencies: 548 PASS /46CUDA SKIP. Tests cover dimension-based gamma, both sides of dense error, unbounded/overlarge uncertainty => INCONCLUSIVE, gross invalid/zero candidate, nonfinite and compensated nonorthogonal factors. First isolated diagnostic invocation had an import failure at earlier cd5a584; previous-cpu-attempt.json and complete error log retained. Final isolated CLI and all tests passed. No GPU or Colab CLI invoked; no new cleanup state claimed.

Reproduce on a clean checkout of a3cba95d1c1c0df66ef5fccc3e0745ae84debc7a: install existing dependencies then `python -I -m pip install --no-deps --no-build-isolation .`; `python -I -m pytest -q -rs -p no:cacheprovider`; `python -I experiments/m8_gpu/diagnose_float64.py --source-sha a3cba95d1c1c0df66ef5fccc3e0745ae84debc7a --out NEW_DIRECTORY`.

Merge-scope proposal only: accept 75 complete configs as partial exploratory evidence while retaining both immutable GPU run directories, all raw timing/error/memory data, fixed tested SHAs, unresolved last-case FAIL and20missingwarm calls. One matrix/sketch seed and three replayed repeats; native niter and SPI steps are distinct work; no general speedup claim. Keep Draft for GPT Chief Architect independent review. No merge performed.

Changed scope: one CPU diagnostic/proposed-policy module, mathematical note, focused tests, and this CPU evidence directory. Production src, SAE/pin, CLI/controller/driver, existing M8 runner/methods/tiers/timing, both historical run directories unchanged. Raw test logs retain exact bytes; source whitespace check separately passes.
