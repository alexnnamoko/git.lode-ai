# Atlas.ai v0.11.0-beta — Structural modelling and 2D frame analysis

## Added
- Regular multi-bay, multi-storey planar frame model generation from user-entered geometry.
- Beam and column placement with explicit node-to-member connectivity.
- Separate beam and column rectangular gross section properties and user-specified elastic modulus.
- Fixed-base support idealisation and model preview/member schedule.
- Linear-elastic 2D Euler-Bernoulli frame analysis using the direct stiffness method.
- Nodal horizontal and vertical loading; joint displacement, support reaction and member local end-action tables.
- JSON model export and CSV member-action export.

## Important limits
- Manual regular-frame generation only; drawing interpretation does not populate or verify the model.
- Planar 2D, prismatic members, rigid joints, gross section properties, small displacements and first-order linear elasticity.
- Nodal loads only. Distributed member loads, end releases, 3D, shear deformation, P-Delta, buckling, dynamic analysis and soil/foundation interaction are not included.
- Member end actions are not automatically passed into BS 8110 design modules in this release.
- This solver has not been independently benchmarked for professional engineering use. Outputs are research results requiring independent verification.

## Preserved
- Existing dashboard cleanup, drawing workflows, OCR/vision integration, knowledge retrieval, beam/slab/column preliminary design modules, verification and reports.
- Existing simply supported beam statics remains available as a separate Beam Statics workspace.
