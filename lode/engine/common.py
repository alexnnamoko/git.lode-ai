from math import sqrt, pi

def require_positive(**values):
    bad = [k for k, v in values.items() if v is None or v <= 0]
    if bad:
        raise ValueError("Inputs must be greater than zero: " + ", ".join(bad))

def bar_area(diameter_mm):
    require_positive(diameter_mm=diameter_mm)
    return pi * diameter_mm**2 / 4

def flexural_steel_area(moment_knm, b_mm, d_mm, fcu_nmm2, fy_nmm2):
    """Limited singly-reinforced rectangular-section flexure calculation."""
    require_positive(moment_knm=moment_knm, b_mm=b_mm, d_mm=d_mm,
                     fcu_nmm2=fcu_nmm2, fy_nmm2=fy_nmm2)
    m = moment_knm * 1e6
    k = m / (fcu_nmm2 * b_mm * d_mm**2)
    if k >= 0.156:
        raise ValueError(f"K={k:.4f} exceeds the prototype singly-reinforced range; revise section or use a separately verified doubly-reinforced design.")
    z = min(d_mm * (0.5 + sqrt(0.25 - k/0.9)), 0.95*d_mm)
    return {"M_Nmm": m, "K": k, "z_mm": z,
            "As_required_mm2": m/(0.87*fy_nmm2*z)}
