"""Linear-elastic 2D Euler-Bernoulli frame analysis by the direct stiffness method.

Research implementation: prismatic members, small displacements, first-order elastic
analysis, rigid joints, no releases, no member distributed loads or second-order effects.
"""
from __future__ import annotations
import math


def analyse_frame_2d(nodes, members, supports, nodal_loads):
    """Solve a 2D frame. Units: m, kN, kN/m² (E), m² (A), m⁴ (I).

    Node dict: {id, x_m, y_m}; member: {id, i, j, E_kN_m2, A_m2, I_m4};
    supports: {node_id: [ux_fixed, uy_fixed, rz_fixed]};
    nodal_loads: {node_id: [Fx_kN, Fy_kN, Mz_kNm]}.
    """
    if len(nodes) < 2 or not members:
        raise ValueError("The model needs at least two nodes and one member.")
    ids = [n["id"] for n in nodes]
    if len(set(ids)) != len(ids):
        raise ValueError("Node identifiers must be unique.")
    index = {nid: i for i, nid in enumerate(ids)}
    ndof = 3 * len(nodes)
    K = [[0.0] * ndof for _ in range(ndof)]
    F = [0.0] * ndof
    element_data = []

    for m in members:
        if m["i"] not in index or m["j"] not in index:
            raise ValueError(f"Member {m.get('id')} refers to an unknown node.")
        ni, nj = nodes[index[m["i"]]], nodes[index[m["j"]]]
        dx, dy = nj["x_m"] - ni["x_m"], nj["y_m"] - ni["y_m"]
        L = math.hypot(dx, dy)
        E, A, I = m["E_kN_m2"], m["A_m2"], m["I_m4"]
        if L <= 1e-9 or min(E, A, I) <= 0:
            raise ValueError(f"Member {m.get('id')} has invalid length or section/material properties.")
        c, s = dx / L, dy / L
        EA_L, EI = E * A / L, E * I
        k = [[0.0]*6 for _ in range(6)]
        vals = [
            [ EA_L,0,0,-EA_L,0,0],
            [0,12*EI/L**3,6*EI/L**2,0,-12*EI/L**3,6*EI/L**2],
            [0,6*EI/L**2,4*EI/L,0,-6*EI/L**2,2*EI/L],
            [-EA_L,0,0,EA_L,0,0],
            [0,-12*EI/L**3,-6*EI/L**2,0,12*EI/L**3,-6*EI/L**2],
            [0,6*EI/L**2,2*EI/L,0,-6*EI/L**2,4*EI/L],
        ]
        k = vals
        # d_local = T d_global; each node block rotates translations only.
        T = [[0.0]*6 for _ in range(6)]
        for off in (0,3):
            T[off][off]=c; T[off][off+1]=s
            T[off+1][off]=-s; T[off+1][off+1]=c
            T[off+2][off+2]=1.0
        kg = [[sum(T[p][a]*k[p][q]*T[q][b] for p in range(6) for q in range(6)) for b in range(6)] for a in range(6)]
        dofs = [3*index[m["i"]],3*index[m["i"]]+1,3*index[m["i"]]+2,3*index[m["j"]],3*index[m["j"]]+1,3*index[m["j"]]+2]
        for a in range(6):
            for b in range(6): K[dofs[a]][dofs[b]] += kg[a][b]
        element_data.append((m, dofs, T, k, L, c, s))

    for nid, load in nodal_loads.items():
        if nid not in index or len(load) != 3:
            raise ValueError("Nodal loads must reference an existing node and contain Fx, Fy and Mz.")
        for j in range(3): F[3*index[nid]+j] += float(load[j])

    fixed = set()
    for nid, flags in supports.items():
        if nid not in index or len(flags) != 3:
            raise ValueError("Support definitions must reference an existing node and contain three restraint flags.")
        for j, flag in enumerate(flags):
            if flag: fixed.add(3*index[nid]+j)
    free = [i for i in range(ndof) if i not in fixed]
    if not fixed:
        raise ValueError("At least one restrained degree of freedom is required.")
    if not free:
        raise ValueError("The model has no free degrees of freedom.")
    # Gaussian elimination with partial pivoting.
    Ared = [[K[i][j] for j in free] for i in free]
    bred = [F[i] for i in free]
    n = len(free)
    for col in range(n):
        pivot = max(range(col,n), key=lambda r: abs(Ared[r][col]))
        if abs(Ared[pivot][col]) < 1e-10:
            raise ValueError("The frame stiffness matrix is singular. Check supports, connectivity and member properties.")
        Ared[col], Ared[pivot] = Ared[pivot], Ared[col]
        bred[col], bred[pivot] = bred[pivot], bred[col]
        p = Ared[col][col]
        for j in range(col,n): Ared[col][j] /= p
        bred[col] /= p
        for r in range(n):
            if r == col: continue
            factor = Ared[r][col]
            if factor:
                for j in range(col,n): Ared[r][j] -= factor*Ared[col][j]
                bred[r] -= factor*bred[col]
    disp = [0.0]*ndof
    for i, dof in enumerate(free): disp[dof] = bred[i]
    reactions = [sum(K[i][j]*disp[j] for j in range(ndof))-F[i] for i in range(ndof)]
    member_results = []
    for m, dofs, T, kl, L, c, s in element_data:
        dg = [disp[d] for d in dofs]
        dl = [sum(T[a][b]*dg[b] for b in range(6)) for a in range(6)]
        end = [sum(kl[a][b]*dl[b] for b in range(6)) for a in range(6)]
        member_results.append({"member_id":m["id"],"length_m":L,"local_end_actions_kN_kNm":end})
    node_results = []
    for i,nod in enumerate(nodes):
        node_results.append({"node_id":nod["id"],"ux_mm":disp[3*i]*1000,"uy_mm":disp[3*i+1]*1000,"rotation_rad":disp[3*i+2],"reaction_Fx_kN":reactions[3*i],"reaction_Fy_kN":reactions[3*i+1],"reaction_Mz_kNm":reactions[3*i+2]})
    return {"method":"2D linear-elastic direct stiffness method","nodes":node_results,"members":member_results,"free_dof_count":len(free),"restrained_dof_count":len(fixed),"limitations":["Planar 2D frame only.","Linear elastic, first-order, small-displacement analysis.","Prismatic Euler-Bernoulli members with rigid joints; no end releases.","Only applied nodal forces and moments are supported; member distributed loads are not yet implemented.","No 3D effects, torsion, shear deformation, P-Delta, buckling, dynamic or foundation-soil analysis.","Results are analysis actions, not BS 8110 design or approval."]}
