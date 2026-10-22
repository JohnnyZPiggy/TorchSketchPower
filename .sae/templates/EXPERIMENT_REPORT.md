# SAE Colab Experiment Report — <run-id>

> Language: **English** | [简体中文](../i18n/zh-CN/templates/EXPERIMENT_REPORT.md)


**Issue:** #<number>  
**Code PR:** #<number>  
**Tested source commit:** `<40-char-sha>`  
**Publication report PR:** <link>  
**Experiment operator:** Codex Engineer  
**Timestamp UTC:** <timestamp>  
**Status:** PASS / FAIL / NOT RUN / BLOCKED

## Three-artifact provenance
**Mathematical Research:** `docs/research/<algorithm>-tensorization.md` / link  
**Engineering Report:** `docs/engineering/<algorithm>-engineering.md` / link  
**Experiment run path:** `reports/gpu/<run-id>/summary.md`  
**Implementation source commit (tested):** `<sha>`  
**Report publication commit (if any):** `<distinct sha or NOT YET PUBLISHED>`  

This file is the **Experimental Report** defined by the [Three-Artifact Handoff](../workflows/THREE_ARTIFACT_HANDOFF.md). It is created from **actual Codex-executed Colab results (no Scientist compute approval required)**, not prefilled as a claimed success.

## Setup
GPU/CPU model, driver/CUDA/PyTorch versions, Colab runtime, dtype, seed, package install source.

## Correctness
Baseline and tolerance, reference comparisons, max error, relative error, failure count, adversarial cases.

## Benchmark
Workload, timing methodology, synchronization, warmups, compile time, repetitions, aggregation, units and accuracy parity.

## Results
Link to manifest.json, correctness.json, benchmark.csv and small figures.

## Interpretation (GPT science/engineering acceptance)
GPT decides the scientific meaning, confidence/limitations and performance bottlenecks from the **actual** measured evidence; no Scientist approval field.

## Next action
GPT Accept / Engineer fix / Re-run / Mentor learning exercise; no human approval queue.
