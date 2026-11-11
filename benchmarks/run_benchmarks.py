"""Run Atlas structural analysis benchmarks BM001-BM006."""
from __future__ import annotations
import json, math
from pathlib import Path
from lode.analysis.beam_analysis import (analyse_simply_supported_beam, analyse_cantilever_point_load, analyse_propped_cantilever_central_point_load)
from lode.analysis.frame2d import analyse_frame_2d
from benchmarks.reference_frame_solver import solve as reference_solve

E=200_000_000.0  # kN/m² (200 GPa)
A=0.02           # m²
I=8.0e-5         # m⁴
def member(mid,i,j): return {'id':mid,'i':i,'j':j,'E_kN_m2':E,'A_m2':A,'I_m4':I}
def frame_model():
    nodes=[{'id':'BL','x_m':0,'y_m':0},{'id':'BR','x_m':6,'y_m':0},
           {'id':'TL','x_m':0,'y_m':3},{'id':'TM','x_m':3,'y_m':3},{'id':'TR','x_m':6,'y_m':3}]
    members=[member('CL','BL','TL'),member('CR','BR','TR'),member('B1','TL','TM'),member('B2','TM','TR')]
    supports={'BL':[True,True,True],'BR':[True,True,True]}
    return nodes,members,supports
def close(a,b,tol=1e-7): return abs(a-b)<=tol*max(1.0,abs(a),abs(b))
def run():
    results=[]
    # BM001 / BM002: exact analytical references and actual Atlas function calls.
    for bid,L,udl,loads,refvals in [
      ('BM001',6,0,[{'x_m':3,'load_kn':20}],{'reaction_A_kN':10,'reaction_B_kN':10,'max_abs_shear_kN':10,'max_abs_moment_kNm':30,'max_moment_location_m':3}),
      ('BM002',6,10,[],{'reaction_A_kN':30,'reaction_B_kN':30,'max_abs_shear_kN':30,'max_abs_moment_kNm':45,'max_moment_location_m':3})]:
        r=analyse_simply_supported_beam(L,udl,loads); vals={k:r[k] for k in refvals}
        results.append({'id':bid,'status':'PASS' if all(close(vals[k],v) for k,v in refvals.items()) else 'FAIL','reference':refvals,'atlas':vals,'method':'Closed-form beam statics','checks':{'vertical_equilibrium_error_kN':r['equilibrium_vertical_error_kN'],'moment_equilibrium_error_kNm':r['equilibrium_moment_error_kNm']}})
    # BM003: analytical closed-form and actual new Atlas cantilever function.
    ref={'reaction_vertical_kN':10,'reaction_moment_kNm':30,'max_abs_shear_kN':10,'max_abs_moment_kNm':30}
    r=analyse_cantilever_point_load(3,10); vals={k:r[k] for k in ref}
    results.append({'id':'BM003','status':'PASS' if all(close(vals[k],v) for k,v in ref.items()) else 'FAIL','reference':ref,'atlas':vals,'method':'Closed-form cantilever statics','checks':{'vertical_equilibrium_error_kN':r['equilibrium_vertical_error_kN'],'moment_equilibrium_error_kNm':r['equilibrium_moment_error_kNm']}})
    # BM004: solve the same propped cantilever with frame stiffness method; compare to closed form.
    nodes=[{'id':'A','x_m':0,'y_m':0},{'id':'M','x_m':3,'y_m':0},{'id':'B','x_m':6,'y_m':0}]
    mem=[member('AM','A','M'),member('MB','M','B')]; supports={'A':[True,True,True],'B':[False,True,False]}; loads={'M':[0,-20,0]}
    ra=analyse_frame_2d(nodes,mem,supports,loads); refp=analyse_propped_cantilever_central_point_load(6,20)
    n={x['node_id']:x for x in ra['nodes']}; ma={x['member_id']:x['local_end_actions_kN_kNm'] for x in ra['members']}
    atlas={'reaction_A_vertical_kN':n['A']['reaction_Fy_kN'],'reaction_B_vertical_kN':n['B']['reaction_Fy_kN'],'reaction_A_moment_kNm':n['A']['reaction_Mz_kNm'],'mid_joint_uy_mm':n['M']['uy_mm']}
    ref4={'reaction_A_vertical_kN':refp['reaction_A_vertical_kN'],'reaction_B_vertical_kN':refp['reaction_B_vertical_kN'],'reaction_A_moment_kNm':refp['reaction_A_moment_kNm']}
    ok=all(close(atlas[k],ref4[k]) for k in ref4)
    results.append({'id':'BM004','status':'PASS' if ok else 'FAIL','reference':ref4,'atlas':atlas,'method':'Closed-form compatibility solution vs Atlas 2D frame stiffness solver','checks':{'vertical_equilibrium_error_kN':abs(atlas['reaction_A_vertical_kN']+atlas['reaction_B_vertical_kN']-20),'reference_moment_equilibrium_error_kNm':refp['equilibrium_moment_error_kNm']},'member_end_actions':ma})
    # BM005/006: independent NumPy reference assembly vs Atlas 2D frame solver.
    for bid,loads in [('BM005',{'TM':[0,-20,0]}),('BM006',{'TL':[20,0,0]})]:
        nodes,mem,supports=frame_model(); atlas_r=analyse_frame_2d(nodes,mem,supports,loads); ref_r=reference_solve(nodes,mem,supports,loads)
        an={x['node_id']:x for x in atlas_r['nodes']}
        diffs=[]; compare=[]
        for nid,rv in ref_r['nodes'].items():
            av=an[nid]
            for key,ak,rk in [('ux_mm','ux_mm','ux_mm'),('uy_mm','uy_mm','uy_mm')]:
                diffs.append(abs(av[ak]-rv[rk])); compare.append({'node':nid,'output':key,'reference':rv[rk],'atlas':av[ak],'abs_error':abs(av[ak]-rv[rk])})
            if nid in supports:
                for key,ak,rk in [('reaction_Fx_kN','reaction_Fx_kN','rx_kN'),('reaction_Fy_kN','reaction_Fy_kN','ry_kN'),('reaction_Mz_kNm','reaction_Mz_kNm','rm_kNm')]:
                    diffs.append(abs(av[ak]-rv[rk])); compare.append({'node':nid,'output':key,'reference':rv[rk],'atlas':av[ak],'abs_error':abs(av[ak]-rv[rk])})
        member_diffs=[]
        atlas_member={x['member_id']:x['local_end_actions_kN_kNm'] for x in atlas_r['members']}
        for mid,rv in ref_r['members'].items():
            for idx,rvv in enumerate(rv):
                err=abs(atlas_member[mid][idx]-rvv); member_diffs.append(err)
                compare.append({'member':mid,'end_action_index':idx,'reference':rvv,'atlas':atlas_member[mid][idx],'abs_error':err})
        diffs.extend(member_diffs)
        maxdiff=max(diffs or [0.0]); ok=maxdiff<1e-6
        # global force equilibrium for externally applied nodal loads and support reactions
        sum_fx=sum(x['reaction_Fx_kN'] for x in atlas_r['nodes'])+sum(v[0] for v in loads.values())
        sum_fy=sum(x['reaction_Fy_kN'] for x in atlas_r['nodes'])+sum(v[1] for v in loads.values())
        results.append({'id':bid,'status':'PASS' if ok and abs(sum_fx)<1e-6 and abs(sum_fy)<1e-6 else 'FAIL','reference_method':'Independent NumPy matrix assembly (separate implementation)','atlas_method':atlas_r['method'],'max_abs_difference':maxdiff,'compared_outputs':compare,'equilibrium':{'sum_fx_kN':sum_fx,'sum_fy_kN':sum_fy},'reference_member_end_actions':ref_r['members'],'atlas_member_end_actions':{x['member_id']:x['local_end_actions_kN_kNm'] for x in atlas_r['members']}})
    return {'benchmark_suite':'Atlas.ai Structural Analysis Benchmark v1.1','units':'kN, m, kN/m², m², m⁴; displacements reported in mm','frame_properties':{'E_kN_m2':E,'A_m2':A,'I_m4':I},'results':results,'interpretation':'BM001-BM004 compare to closed-form analytical solutions. BM005-BM006 compare Atlas to a separately implemented NumPy stiffness solver using the same linear-elastic Euler-Bernoulli theory; this is a cross-implementation check, not external commercial-software validation.'}
if __name__=='__main__':
    data=run(); out=Path(__file__).with_name('benchmark_run_results.json'); out.write_text(json.dumps(data,indent=2)); print(json.dumps(data,indent=2))
