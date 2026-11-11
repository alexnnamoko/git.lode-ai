# Atlas.ai v0.11.1-beta — structural benchmark expansion

## Added
- Cantilever beam analysis for a downward point load at the free end.
- Closed-form central point-load solution for a propped cantilever.
- Reproducible BM001–BM006 benchmark runner.
- Independent NumPy matrix-assembly reference implementation for portal-frame cross-checks.
- Benchmark run output saved as `benchmarks/benchmark_run_results.json`.

## Benchmark scope
- BM001–BM003: closed-form beam statics.
- BM004: closed-form propped-cantilever compatibility solution compared with the 2D frame stiffness solver.
- BM005–BM006: Atlas frame solver compared with a separately implemented NumPy frame stiffness solver.

## Limitations
- Portal-frame comparison is a cross-implementation check, not independent validation against commercial software or experimental results.
- The frame solver remains first-order, linear-elastic, 2D, prismatic Euler-Bernoulli with rigid joints and nodal loads only.
- No distributed member loads, 3D effects, P-Delta, buckling, dynamics, shear deformation, or soil-structure interaction.
- These analysis benchmarks are not BS 8110 RC design verification or construction approval.


## OpenSees comparison preparation (2026-11-11)
- Added independent OpenSees Tcl models for BM005 (vertical portal-frame nodal load) and BM006 (lateral portal-frame nodal load).
- Added run instructions, model assumptions, output guidance, and comparison acceptance criteria under `benchmarks/opensees/`.
- The scripts have **not** been executed in this environment; OpenSeesPy was unavailable and package installation could not reach the package index.
- BM005/BM006 remain pending independent OpenSees execution. Existing Atlas-vs-NumPy results must not be described as OpenSees validation.
