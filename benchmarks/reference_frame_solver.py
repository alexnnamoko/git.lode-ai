"""Independent NumPy reference solver for benchmark cross-checks.

This deliberately separate implementation assembles a 2D Euler-Bernoulli frame
stiffness matrix with NumPy. It is a cross-implementation check, not an independent
commercial-software validation or a proof of physical-model validity.
"""
import numpy as np

def solve(nodes, members, supports, loads):
    ids=[n['id'] for n in nodes]; ix={v:i for i,v in enumerate(ids)}; nd=3*len(nodes)
    K=np.zeros((nd,nd),dtype=float); F=np.zeros(nd,dtype=float); elements=[]
    for m in members:
        i,j=ix[m['i']],ix[m['j']]; ni,nj=nodes[i],nodes[j]
        dx=nj['x_m']-ni['x_m']; dy=nj['y_m']-ni['y_m']; L=float(np.hypot(dx,dy)); c=dx/L; s=dy/L
        E,A,I=m['E_kN_m2'],m['A_m2'],m['I_m4']; EA=E*A/L; EI=E*I
        kl=np.array([[EA,0,0,-EA,0,0],[0,12*EI/L**3,6*EI/L**2,0,-12*EI/L**3,6*EI/L**2],[0,6*EI/L**2,4*EI/L,0,-6*EI/L**2,2*EI/L],[-EA,0,0,EA,0,0],[0,-12*EI/L**3,-6*EI/L**2,0,12*EI/L**3,-6*EI/L**2],[0,6*EI/L**2,2*EI/L,0,-6*EI/L**2,4*EI/L]])
        T=np.zeros((6,6))
        for o in (0,3): T[o,o]=c; T[o,o+1]=s; T[o+1,o]=-s; T[o+1,o+1]=c; T[o+2,o+2]=1
        kg=T.T@kl@T; dofs=[3*i,3*i+1,3*i+2,3*j,3*j+1,3*j+2]
        K[np.ix_(dofs,dofs)]+=kg; elements.append((m,dofs,T,kl,L))
    for nid,vec in loads.items(): F[3*ix[nid]:3*ix[nid]+3]+=np.asarray(vec,dtype=float)
    fixed=[]
    for nid,flags in supports.items(): fixed += [3*ix[nid]+k for k,f in enumerate(flags) if f]
    free=[d for d in range(nd) if d not in set(fixed)]
    u=np.zeros(nd); u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free]); R=K@u-F
    node_out={n['id']:{'ux_mm':u[3*i]*1000,'uy_mm':u[3*i+1]*1000,'rz':u[3*i+2],
        'rx_kN':R[3*i],'ry_kN':R[3*i+1],'rm_kNm':R[3*i+2]} for i,n in enumerate(nodes)}
    member_out={}
    for m,dofs,T,kl,L in elements:
        dl=T@u[dofs]; member_out[m['id']]=(kl@dl).tolist()
    return {'nodes':node_out,'members':member_out}
