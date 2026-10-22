# TorchSketchPower

[English](README.md) | [简体中文](README.zh-CN.md)

**Randomized low-rank matrix approximation in native PyTorch.**

TorchSketchPower implements sketch-power iterations using randomized matrix sketches, QR-stabilized subspace refinement, checked least-squares recovery, and truncated SVD. The repository brings together mathematical derivations, CPU/CUDA numerical experiments, PyTorch benchmarking, and reproducible research artifacts.

![MIT](https://img.shields.io/badge/license-MIT-0f766e) ![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab) ![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-ee4c2c) ![Research](https://img.shields.io/badge/status-research_software-334155)

**Explore:** [Mathematics](docs/math.md) · [Experimental results](docs/RESEARCH_CLOSEOUT.md) · [CPU studies](docs/cpu-results.md) · [GPU benchmarks](reports/m8_gpu/m8-ref-t4-20261022-195451/review.md) · [Documentation](docs/README.md)

## Highlights

- **Native PyTorch:** matrix-based random sketches, QR, least squares and SVD on CPU and CUDA.
- **Numerical stability:** rank checks, conditioning diagnostics and complex conjugate-transpose support.
- **Sketch-power refinement:** subspace iterations reuse an auxiliary sketch.
- **Reproducible research:** source-pinned CPU/T4 experiments, raw benchmark records and numerical counterexamples.
- **Independent scientific engineering:** documented algorithm choices, correctness tests and performance investigations.

## Algorithm architecture

![Sketch-Power tensor pipeline](docs/assets/sketch-power-architecture.svg)

The pipeline constructs two right sketches and one corange sketch from the input matrix. A QR-stabilized sketch-power iteration extracts a subspace; a small least-squares problem and truncated SVD recover the low-rank factors.

For a dense matrix \(A\in\mathbb{F}^{m\times n}\), sketch dimensions \(s,\ell,d\) and target rank \(r\):

\[
Y=A\Omega,\quad Z=A\Phi,\quad W=\Psi A,\qquad
Q_0=\operatorname{orth}(Y).
\]

\[
Q_{t+1}=\operatorname{orth}\bigl(Z\,\operatorname{orth}(Z^H Q_t)\bigr),\qquad
B=\underset{B}{\operatorname{argmin}}\,\|(\Psi Q_t)B-W\|_F.
\]

The output is the rank-\(r\) truncated factorization \(\widehat A_r=U_r\Sigma_r V_r^H\). The current implementation processes resident matrices; the power updates reuse \(Z\). See [the mathematical formulation](docs/math.md) for derivations and numerical conventions.

## Installation and quick start

Install from a checkout (Python >=3.10; PyTorch >=2.2):

```bash
git clone https://github.com/JohnnyZPiggy/TorchSketchPower.git
cd TorchSketchPower
python -m pip install .
```

```python
import torch
from torchsketchpower import sketch_power_low_rank

matrix_rng = torch.Generator().manual_seed(7)
A = torch.randn(120, 80, generator=matrix_rng, dtype=torch.float64)

U, sigma, Vh = sketch_power_low_rank(
    A, r=8, s=12, ell=24, d=24, steps=1,
    generator=torch.Generator().manual_seed(42),
)

A_hat = (U * sigma) @ Vh
relative_error = torch.linalg.matrix_norm(A - A_hat) / torch.linalg.matrix_norm(A)
print(f"Relative Frobenius error: {relative_error:.4f}")
```

Pass a device-resident input and matching random generator for the Gaussian CUDA path. The API also exposes sketch constructors, the subspace kernel, corange reconstruction and numerical diagnostics.

## Performance and research findings

The archive includes real NVIDIA Tesla T4 measurements and CPU numerical studies. This is an accuracy- and evidence-oriented numerical project: comparisons are reported with their measurement scope.

| Study | Result | Evidence |
|---|---|---|
| **CPU accuracy and error analysis** | Synthetic spectral experiments and exact error-decomposition checks | [M4–M5](docs/cpu-results.md) |
| **CUDA correctness** | **171 passing numerical-oracle cases** on a real T4 | [M7](reports/m7_cuda/m7-t4-20261022-185647/m7-cuda-report.json) |
| **Native PyTorch comparison** | **75/80** configurations fully timed in the second study; `torch.svd_lowrank` was faster on the measured paired cases | [M8](reports/m8_gpu/m8-ref-t4-20261022-195451/review.md) |
| **`torch.compile`** | Partial graph capture and graph-break analysis; three measured T4 Inductor pairs were slower than eager | [M9](reports/m9_compile/m9-t4-20261022-204314/review.md) |
| **Optimization research** | FLOP/memory cost model and a reproducible rank-threshold counterexample for concatenated GEMMs | [M10](experiments/m10_cost/README.md) · [M11](reports/m11_concat/m11-20261022-214747/review.md) |

The [research evidence index](docs/RESEARCH_CLOSEOUT.md) links tested source commits, raw output and complete numerical findings.

## Applications and research directions

| Area | Potential use |
|---|---|
| Low-rank approximation | Explore compressed representations of dense matrices |
| Subspace estimation | Study leading singular subspaces using randomized sketches |
| Scientific computing | Compare sketch accuracy across spectra and memory budgets |
| GPU numerical methods | Examine QR/SVD/least-squares costs and PyTorch execution behavior |

## Repository layout

```text
src/torchsketchpower/   Core PyTorch implementation
tests/                 Numerical and regression tests
experiments/           Research and benchmark runners
reports/               Raw measurements and reproducibility evidence
docs/                  Mathematical derivations and research documentation
.sae/                  Scientist–Architect–Engineer workflow snapshot
```

Run the CPU test suite:

```bash
python -m pip install pytest
python -m pytest -q
```

## References

Inspired by **Chao Chang and Yuning Yang**, *Improving Sketching Algorithms for Low-Rank Matrix Approximation via Sketch-Power Iterations*, *SIAM Journal on Matrix Analysis and Applications* (2026). [DOI: 10.1137/25M1760143](https://doi.org/10.1137/25M1760143).

Developed using the [SAE (Scientist–Architect–Engineer) framework](https://github.com/JohnnyZPiggy/SAE-Framework).

## License

[MIT License](LICENSE) · Copyright © 2026 Ru Zhang.
