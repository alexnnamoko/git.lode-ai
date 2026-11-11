"""Elastic statics for a simply supported beam with full-span UDL and point loads."""
from __future__ import annotations
import math

def analyse_simply_supported_beam(span_m: float, udl_kn_m: float = 0.0, point_loads=None, samples: int = 201):
    if not math.isfinite(span_m) or span_m <= 0: raise ValueError('Span must be a positive finite value.')
    if not math.isfinite(udl_kn_m) or udl_kn_m < 0: raise ValueError('UDL must be finite and non-negative.')
    loads = point_loads or []
    clean=[]
    for i, p in enumerate(loads):
        x=float(p['x_m']); P=float(p['load_kn'])
        if not math.isfinite(x) or not math.isfinite(P) or P < 0: raise ValueError(f'Point load {i+1} must have finite position and non-negative magnitude.')
        if x < 0 or x > span_m: raise ValueError(f'Point load {i+1} must lie between 0 and the span.')
        clean.append({'x_m':x,'load_kn':P})
    total_udl=udl_kn_m*span_m
    total_points=sum(p['load_kn'] for p in clean)
    moment_loads=udl_kn_m*span_m*(span_m/2)+sum(p['load_kn']*p['x_m'] for p in clean)
    rb=moment_loads/span_m; ra=total_udl+total_points-rb
    if samples < 21: samples=21
    xs=[span_m*i/(samples-1) for i in range(samples)]
    # Include exact point-load locations and immediately adjacent sample points for correct jumps.
    for p in clean:
        xs.extend([p['x_m'], max(0,p['x_m']-1e-8), min(span_m,p['x_m']+1e-8)])
    xs=sorted(set(xs)); shear=[]; moment=[]
    for x in xs:
        v=ra-udl_kn_m*x-sum(p['load_kn'] for p in clean if p['x_m'] <= x)
        m=ra*x-udl_kn_m*x*x/2-sum(p['load_kn']*max(0,x-p['x_m']) for p in clean if p['x_m'] <= x)
        shear.append(v); moment.append(m)
    # Check equilibrium independently from calculated reactions.
    vertical_error=abs(ra+rb-total_udl-total_points)
    moment_error=abs(rb*span_m-moment_loads)
    if vertical_error > 1e-7 or moment_error > 1e-7: raise ArithmeticError('Static equilibrium check failed.')
    imax=max(range(len(moment)),key=lambda i:abs(moment[i])); ivmax=max(range(len(shear)),key=lambda i:abs(shear[i]))
    return {'member':'Simply supported beam','span_m':span_m,'udl_kn_m':udl_kn_m,'point_loads':clean,
      'reaction_A_kN':ra,'reaction_B_kN':rb,'total_load_kN':total_udl+total_points,
      'max_abs_shear_kN':abs(shear[ivmax]),'max_shear_location_m':xs[ivmax],
      'max_abs_moment_kNm':abs(moment[imax]),'max_moment_location_m':xs[imax],
      'equilibrium_vertical_error_kN':vertical_error,'equilibrium_moment_error_kNm':moment_error,
      'x_m':xs,'shear_kN':shear,'moment_kNm':moment,
      'sign_convention':'Sagging bending moment positive; positive shear follows the left-face convention used by the equations.'}


def analyse_cantilever_point_load(span_m: float, point_load_kn: float, samples: int = 201):
    """First-order elastic statics for a cantilever with a downward free-end load.

    Returns reactions and the internal shear/moment diagram. Positive load is downward;
    the reported fixed-end reaction moment is counter-clockwise and the internal
    fixed-end bending moment is hogging (negative under the stated convention).
    """
    if not math.isfinite(span_m) or span_m <= 0:
        raise ValueError('Span must be a positive finite value.')
    if not math.isfinite(point_load_kn) or point_load_kn < 0:
        raise ValueError('Point load must be finite and non-negative.')
    samples=max(21, int(samples))
    xs=[span_m*i/(samples-1) for i in range(samples)]
    shear=[-point_load_kn for _ in xs]
    moment=[-point_load_kn*(span_m-x) for x in xs]
    return {
        'member':'Cantilever beam','span_m':span_m,'point_load_kn':point_load_kn,
        'reaction_vertical_kN':point_load_kn,
        'reaction_moment_kNm':point_load_kn*span_m,
        'max_abs_shear_kN':point_load_kn,
        'max_abs_moment_kNm':point_load_kn*span_m,
        'max_moment_location_m':0.0,'x_m':xs,'shear_kN':shear,'moment_kNm':moment,
        'equilibrium_vertical_error_kN':0.0,'equilibrium_moment_error_kNm':0.0,
        'sign_convention':'Downward load; internal hogging moment is negative.'
    }

def analyse_propped_cantilever_central_point_load(span_m: float, point_load_kn: float, samples: int = 201):
    """Closed-form propped cantilever with a central downward point load.

    Fixed at x=0 and vertically propped (roller) at x=L. Linear-elastic Euler-Bernoulli
    solution for a prismatic member. The load is at L/2.
    """
    if not math.isfinite(span_m) or span_m <= 0:
        raise ValueError('Span must be a positive finite value.')
    if not math.isfinite(point_load_kn) or point_load_kn < 0:
        raise ValueError('Point load must be finite and non-negative.')
    P,L=point_load_kn,span_m
    rb=5*P/16; ra=11*P/16; fixed_reaction_moment=3*P*L/16
    a=L/2
    samples=max(21,int(samples))
    xs=sorted(set([L*i/(samples-1) for i in range(samples)]+[a]))
    shear=[]; moment=[]
    for x in xs:
        v=ra-(P if x>=a else 0.0)
        m=-fixed_reaction_moment+ra*x-(P*max(0.0,x-a))
        shear.append(v); moment.append(m)
    # Moment equilibrium about the fixed end and vertical equilibrium.
    verr=abs(ra+rb-P)
    merr=abs(fixed_reaction_moment+rb*L-P*a)
    return {
        'member':'Propped cantilever beam','span_m':L,'point_load_kn':P,'load_position_m':a,
        'reaction_A_vertical_kN':ra,'reaction_B_vertical_kN':rb,
        'reaction_A_moment_kNm':fixed_reaction_moment,
        'max_abs_shear_kN':max(abs(v) for v in shear),
        'max_abs_moment_kNm':max(abs(m) for m in moment),
        'max_moment_location_m':xs[max(range(len(moment)),key=lambda i:abs(moment[i]))],
        'equilibrium_vertical_error_kN':verr,'equilibrium_moment_error_kNm':merr,
        'x_m':xs,'shear_kN':shear,'moment_kNm':moment,
        'sign_convention':'Internal hogging moment at fixed end is negative; sagging is positive.'
    }
