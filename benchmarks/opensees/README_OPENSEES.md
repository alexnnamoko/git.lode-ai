# OpenSees independent comparison — BM005 and BM006

## Status

**Prepared, not yet executed against OpenSees.** OpenSeesPy was not installed in the preparation environment and package installation was unavailable. These Tcl models are ready for execution in a local OpenSees installation. Do not report an OpenSees PASS until the generated CSV files have been reviewed and compared with Atlas outputs.

## What is being compared

Both scripts use the same 2D, one-storey, one-bay rigid portal frame:

- Bay width: 6.0 m; storey height: 3.0 m.
- Nodes: BL (0,0), BR (6,0), TL (0,3), TM (3,3), TR (6,3), coordinates in metres.
- Members: left column BL–TL, right column BR–TR, left beam TL–TM, right beam TM–TR.
- All members: E = 200,000,000 kN/m²; A = 0.020 m²; I = 0.000080 m⁴.
- Both column bases fully fixed (ux, uy, rz); all beam-column joints rigid; no end releases.
- Linear elastic, first-order static analysis; small displacements; Euler-Bernoulli elements; no self-weight; no geometric nonlinearity.
- BM005: 20 kN downward at TM.
- BM006: 20 kN to the right at TL.

## Run on Windows

1. Install a compatible OpenSees executable from the official OpenSees distribution and confirm the executable runs from Command Prompt. The executable is commonly named `OpenSees.exe`.
2. Copy `BM005_portal_vertical.tcl` and `BM006_portal_lateral.tcl` into a working folder.
3. Open Command Prompt in that folder.
4. Run the vertical case:

   ```bat
   OpenSees.exe BM005_portal_vertical.tcl
   ```

5. Run the lateral case:

   ```bat
   OpenSees.exe BM006_portal_lateral.tcl
   ```

6. Each successful run should create a CSV file in the current working directory:
   - `BM005_opensees_results.csv`
   - `BM006_opensees_results.csv`
7. Keep the Tcl files, CSV outputs, OpenSees version, run date, and any console errors together as evidence.

If Windows cannot find `OpenSees.exe`, use its full path in the command, for example:

```bat
"C:\Path\To\OpenSees.exe" BM005_portal_vertical.tcl
```

## Outputs

The CSV files contain node displacements and support reactions. They also include the element `localForce` response as returned by OpenSees. Compare node displacement and support reaction values first. Member local-force sign conventions and the response vector ordering must be confirmed against the OpenSees documentation before comparing them; do not compare absolute values without checking the sign convention.

## Acceptance criteria

- First confirm that both analyses complete successfully and that global force equilibrium is satisfied.
- Compare the same output quantity, unit, node, and sign convention.
- Calculate absolute and percentage error for each non-zero reference value. For values near zero, use an absolute tolerance rather than percentage error.
- Use a pre-declared tolerance (suggested initial screening: 0.1% for non-zero displacements/reactions, plus an absolute tolerance of 1e-8 in the corresponding unit for near-zero values). If the solvers differ because of formulation, constraints, or output conventions, investigate rather than loosening tolerance automatically.
- A comparison only validates these two specified linear-elastic frame models. It does not validate 3D analysis, P-Delta, distributed member loads, reinforced-concrete design, BS 8110 compliance, or building-wide analysis.

## Atlas side

The source implementation being compared is `lode/analysis/frame2d.py`, called by `benchmarks/run_benchmarks.py`. Re-run the Atlas benchmark suite from the project root:

```bat
python benchmarks\run_benchmarks.py
python -m pytest -q
```

Retain `benchmarks/benchmark_run_results.json` with the OpenSees CSVs. The current Atlas runner also compares BM005/BM006 with a separately written NumPy reference solver; that is a cross-implementation check, not an OpenSees comparison.
