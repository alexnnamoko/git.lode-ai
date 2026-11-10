from .common import require_positive, bar_area

def design_short_axially_loaded_column(*, width_mm, depth_mm, axial_load_kn,
    fcu_nmm2, fy_nmm2, bar_diameter_mm, number_of_bars,
    confirmed_short_column=False):
    require_positive(width_mm=width_mm, depth_mm=depth_mm, axial_load_kn=axial_load_kn,
        fcu_nmm2=fcu_nmm2, fy_nmm2=fy_nmm2, bar_diameter_mm=bar_diameter_mm)
    if number_of_bars < 4:
        raise ValueError("At least four longitudinal bars are required in this rectangular tied-column prototype.")
    if not confirmed_short_column:
        raise ValueError("Independently confirm short-column classification before using this axial-only calculation.")
    ag = width_mm*depth_mm
    ass = number_of_bars*bar_area(bar_diameter_mm)
    ac = ag-ass
    if ac <= 0:
        raise ValueError("Provided reinforcement area is invalid for this section.")
    # Simplified axial capacity expression for a short braced column.
    capacity_kn = (0.4*fcu_nmm2*ac + 0.75*fy_nmm2*ass)/1000
    pct = 100*ass/ag
    return {"member":"Short tied rectangular column",
        "basis":"Concentric axial compression only; short-column classification separately confirmed",
        "b_mm":width_mm, "h_mm":depth_mm, "Ag_mm2":ag, "Ac_mm2":ac,
        "NEd_kN":axial_load_kn, "As_provided_mm2":ass, "steel_percentage":pct,
        "fcu_nmm2":fcu_nmm2, "fy_nmm2":fy_nmm2, "bar_diameter_mm":bar_diameter_mm,
        "number_of_bars":number_of_bars,
        "Nu_capacity_kN":capacity_kn, "axial_capacity_check":capacity_kn >= axial_load_kn,
        "reinforcement_ratio_screen":"PASS" if 0.4 <= pct <= 6.0 else "REVIEW",
        "warning":"No column moments, biaxial bending, eccentricity, slenderness or second-order effects are included.",
        "calculation_scope":"Preliminary concentric axial-only short tied column calculation; not a complete BS 8110 column design."}
