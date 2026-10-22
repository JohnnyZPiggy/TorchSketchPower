# M9 compile feasibility: bounded CPU and one T4 probe

Tested source `988a1b170f2b9f56eef3a3e21f71bbdb5b68290e`; starting main `fcf1f9da6ff6692ff065d1f5341d31e7f8306091`; fixed SAE `65338eb1aa67971e110db982a07cf43161c23446`. Issue #22 / Draft PR #23. Independent GPT T2 review pending.

CPU classifications {'SUPPORTED': 4, 'GRAPH_BREAK': 5, 'UNSUPPORTED': 2}; GPU classifications {'SUPPORTED': 4, 'GRAPH_BREAK': 6, 'UNSUPPORTED': 1}. GPU timed calls 73; correctness-fail cases []; unsupported [9]; NOT_RUN [].

Real device/runtime: {'torch': '2.11.0+cu130', 'python': '3.13.15 (main, Aug  6 2026, 11:06:22) [GCC 13.3.0]', 'platform': 'Linux-6.6.122+-x86_64-with-glibc2.39', 'cuda_build': '13.0', 'device': 'cuda', 'threads': 1, 'gpu_name': 'Tesla T4'}. Fresh exact-SHA noneditable package verification PASS; short installed-package M7 CUDA gate {'PASS': 39, 'NOT_RUN': 1}. CPU fresh noneditable install/full suite556PASS/46CUDA SKIP.

Exactly one allocation; cleanup stop+fresh strict AUTHENTICATED_ZERO confirmed at 2026-10-22T18:46:01.112219+00:00. Downloaded artifact 124088 bytes SHA256 7788fd6feb780df1326a5357fbcf59eabf7e12133d48879f0167a4652bdfa377; exact decoded benchmark and CSV/summary hashes verified. No retry or new billing commitment. Controller/account balance redacted; raw credentials/usage not published.

## Scientific interpretation and retained negative evidence

Pure-helper supported means three fixed-sketch matmuls captured, with the original checked subspace/reconstruction subsequently verified. It does NOT mean the entire public algorithm was compiled, fused or accelerated. Public aot_eager includes generator draws and all rank/conditioning checks, but is a debugging backend without optimized codegen. Graph-break observations use explain AFTER measured calls; graph counts describe capture segmentation, not kernels. Fullgraph=True failure is retained as UNSUPPORTED. No ignore-rank policy or graph hacks were used.

CPU public Inductor unsupported because Windows cl is unavailable; helper external-matmul graphs still run. CPU fullgraph=True fails Generator proxy conversion; original source lines/int/float/conditioning checks are unmodified. Full exceptions, worker stderr/stdout, graph reasons, timings and correctness/exception controls remain in CPU/GPU raw JSON, including unsupported and timed-out cases. GPU behavior is independently observed, never inferred from CPU version.

## Derived timing observations (not a speedup claim)

All numbers below are whole-call milliseconds. First compiled call includes compilation+run; wrapper creation is separately in raw data. Warm median/IQR derives from exactly3raw trials, one unmeasured warmup per mode. Helper timing excludes random sketch creation and downstream checks; public timing includes actual draws/checks and same-device generator reset in wrapper. Never compare these scopes as equivalent work. Event intervals include default-stream idle and are not kernel-only; memory is allocator peak/delta, not device-wide allocation.

|case|kind/backend/dtype/steps|mode|first ms|warm median ms|IQR ms|event median ms|
|---|---|---|---|---|---|---|
|0|helper/inductor/float32/1|eager|14.56711000002997|0.17801699993924558|0.01041799998802162|0.12947200238704681|
|0|helper/inductor/float32/1|compiled|7449.67748800002|0.4179890000841624|0.03355200004762082|0.3624959886074066|
|1|helper/aot_eager/float32/1|eager|14.636863999953675|0.14757300004930585|0.08620050004992663|0.10918399691581726|
|1|helper/aot_eager/float32/1|compiled|176.79274599993278|0.2899440000874165|0.03183299997999711|0.23452800512313843|
|2|public/aot_eager/float32/0|eager|204.14054999992004|3.5784140000032494|0.07262700000865152|3.540992021560669|
|2|public/aot_eager/float32/0|compiled|2136.6888180000387|4.864861999976711|0.1356774999976551|4.826848030090332|
|3|public/aot_eager/float32/1|eager|230.6411910000179|4.76624600003106|0.07016950002025624|4.713183879852295|
|3|public/aot_eager/float32/1|compiled|2120.886832999986|8.328602999995383|0.5694519999792647|8.253439903259277|
|4|helper/inductor/float64/1|eager|21.55962599999839|0.8716930000218781|0.005315500004599016|0.8091199994087219|
|4|helper/inductor/float64/1|compiled|4078.2341280000765|1.0098489999563753|0.024463499983085057|0.9511359930038452|
|5|helper/aot_eager/float64/1|eager|17.71112799997354|0.8187459999362545|0.06989399997792134|0.7890880107879639|
|5|helper/aot_eager/float64/1|compiled|179.86638699994728|0.9267869999121103|0.013523000006898656|0.8951359987258911|
|6|public/aot_eager/float64/0|eager|204.70466199992643|12.609448000034718|0.2570700000319448|12.555456161499023|
|6|public/aot_eager/float64/0|compiled|2046.8759520000503|13.37350099993273|0.038258499955645675|13.326944351196289|
|7|public/aot_eager/float64/1|eager|207.76840799999263|14.974337000012383|0.04620749996320228|14.930591583251953|
|7|public/aot_eager/float64/1|compiled|2097.7479369998946|15.984170000024278|0.12421600001744082|15.938240051269531|
|8|public/inductor/float64/1|eager|206.40544499997304|14.901809999969373|0.0744085000405903|14.857983589172363|
|8|public/inductor/float64/1|compiled|8170.585450999965|15.689696999970693|0.15467750000652813|15.642656326293945|

No headline speedup or break-even estimate is accepted. One seed/session and three repeated timings provide no replicated performance result. GPU fixed shape256x128,r3/s6/ell8/d10; CPU32x24. Unsupported/deadline cases have no warm comparisons. Full-grid completion is not implied by report transport.

NOT RUN: full GPU pytest this cycle, complex compile,1024x512/larger compile sweep, amortization break-even, independent seeds/sessions. Initial CPU helper-only codegen probe was an uncommitted private diagnostic; formal CPU/GPU results use exact SHA above. Original M7/M8 directories are untouched, including historical FAIL and 75/80partial evidence.

Next: GPT Chief Architect independently reviews unchanged safety semantics, graph breaks/unsupported paths, raw measurements, source/hash provenance and strict zero cleanup. Keep PR Draft; no merge by Engineer.

## Scoped negative result and warning disclosure

The three actual Inductor paired warm medians were slower than eager on this one T4/shape/seed:

- case0 helper float32: eager 0.178017 ms, compiled 0.417989 ms; compiled first call 7449.677 ms.
- case4 helper float64: eager 0.871693 ms, compiled 1.009849 ms; compiled first call 4078.234 ms.
- case8 public float64: eager 14.901810 ms, compiled 15.689697 ms; compiled first call 8170.585 ms.

This is a scoped negative observation, not universal compiler or algorithm performance. No positive speedup/break-even is inferred. GPU case-wide warning capture includes126 DeprecationWarning records for torch.jit.script_method deprecation; expected IllConditionedWarning controls are captured separately. These are not126 algorithm numerical errors, nor can this capture assign them to individual warm calls. Raw warnings and compiler stderr are retained. run-summary.json has publication-derived M9 counters replacing legacy wrapper fields over nonexistent top-level M8 trials; raw artifact/results/CSV/controller bytes remain unchanged.
