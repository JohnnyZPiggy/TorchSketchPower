# TorchSketchPower

Experimental portable PyTorch sketch-power subspace kernel inspired by Chang and Yang (2026), DOI: 10.1137/25M1760143.

## Status

**EXPLORE / unmerged prototype.** The kernel computes an orthonormal basis for repeated auxiliary-sketch power operations; it is **not** yet the complete paper algorithm or a verified single-pass low-rank reconstruction.

```bash
python -m pip install -e '.[test]'
pytest -q
```

If `(Z Z^H)^q Y` has numerical rank below `k`, the trailing output columns are arbitrary; `sketch_power_subspace` emits a `RankDeficiencyWarning` in that case (disable with `check_rank=False`).

CPU evidence for each revision is recorded in the PR conversation (PR #2). GPU: NOT RUN.

See [research rationale](docs/research/spi-tensorization.md) and [Issue #1](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/1).

Upstream MATLAB: https://github.com/Mitchell-Cxyk/SketchPowerIteration @ `752be34fbd26595f8d608a25e7dcdea586a6e0ca`. No root LICENSE found: no code copied.

SAE V3.3 source commit: `65338eb1aa67971e110db982a07cf43161c23446`. Full `.sae/` snapshot adoption remains **BLOCKED / INCOMPLETE**; do not assume this project has a complete pinned framework snapshot.
