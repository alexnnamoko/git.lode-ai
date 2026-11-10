"""Independent arithmetic checks; not a code-compliance or design-approval engine."""
from math import pi, sqrt, isclose
TOL = 1e-6

def _check(name, actual, expected, unit=""):
    ok = isclose(float(actual), float(expected), rel_tol=TOL, abs_tol=TOL)
    return {"check": name, "status": "PASS" if ok else "FAIL", "actual": float(actual),
            "independently_recalculated": float(expected), "unit": unit}

def verify_design_result(result):
    member = str(result.get("member", "")).lower(); checks = []
    if "beam" in member:
        span=float(result["span_m"]); wu=float(result["wu_kN_m"])
        checks += [_check("Ultimate UDL",wu,1.4*float(result["Gk_kN_m"])+1.6*float(result["Qk_kN_m"]),"kN/m"),
                   _check("Maximum moment",result["MEd_kNm"],wu*span**2/8,"kN·m"),
                   _check("Support shear",result["VEd_kN"],wu*span/2,"kN")]
        fcu=float(result.get("fcu_nmm2",0)); fy=float(result.get("fy_nmm2",0)); b=float(result["b_mm"]); d=float(result["d_mm"])
        if fcu>0 and fy>0:
            m=float(result["MEd_kNm"])*1e6; k=m/(fcu*b*d*d)
            if k<0.156:
                z=min(d*(0.5+sqrt(0.25-k/0.9)),0.95*d); as_req=m/(0.87*fy*z)
                checks += [_check("Flexural K",result["K"],k),_check("Lever arm",result["z_mm"],z,"mm"),
                           _check("Required tensile steel",result["As_required_mm2"],as_req,"mm²")]
            else: checks.append({"check":"Flexural range","status":"NOT CHECKED","note":"K outside supported singly reinforced range."})
        dia=float(result["main_bar_diameter_mm"]); n=int(result["main_bars_by_area"])
        checks.append(_check("Provided main steel area",result["As_provided_mm2"],n*pi*dia**2/4,"mm²"))
        scope="Selected simply-supported UDL beam arithmetic only; not full shear, deflection, crack, torsion, anchorage or code compliance verification."
    elif "slab" in member:
        span=float(result["span_m"]); wu=float(result["wu_kN_m2"])
        checks += [_check("Ultimate slab load",wu,1.4*float(result["Gk_kN_m2"])+1.6*float(result["Qk_kN_m2"]),"kN/m²"),
                   _check("One-metre strip moment",result["MEd_kNm_per_m"],wu*span**2/8,"kN·m/m")]
        dia=float(result["main_bar_diameter_mm"]); n=int(result["bars_per_m_by_area"])
        checks.append(_check("Provided main steel area",result["As_provided_mm2"],n*pi*dia**2/4,"mm²"))
        scope="Selected one-way slab arithmetic only; not full two-way, punching, crack or code compliance verification."
    elif "column" in member:
        ag=float(result["Ag_mm2"]); ass=float(result["As_provided_mm2"]); ac=float(result["Ac_mm2"])
        checks += [_check("Gross area",ag,float(result["b_mm"])*float(result["h_mm"]),"mm²"),
                   _check("Concrete area",ac,ag-ass,"mm²")]
        capacity=(0.4*float(result["fcu_nmm2"])*ac+0.75*float(result["fy_nmm2"])*ass)/1000
        checks.append(_check("Axial capacity expression",result["Nu_capacity_kN"],capacity,"kN"))
        scope="Selected axial-capacity arithmetic only; not eccentricity, moments, slenderness, biaxial or code compliance verification."
    else:
        return {"overall_status":"NOT CHECKED","checks":[],"scope":"No verifier registered for this result type."}
    statuses={c["status"] for c in checks}
    overall="FAIL" if "FAIL" in statuses else ("PASS — LIMITED ARITHMETIC CHECKS" if statuses=={"PASS"} else "PARTIAL")
    return {"overall_status":overall,"checks":checks,"scope":scope,"not_a_compliance_certificate":True,
            "required_review":"Qualified structural engineer review remains mandatory."}
