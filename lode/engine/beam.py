import math
from .common import require_positive, flexural_steel_area, bar_area

def design_beam(*, span_m, width_mm, overall_depth_mm, cover_mm, link_diameter_mm,
                main_bar_diameter_mm, fcu_nmm2, fy_nmm2, dead_load_kn_m,
                imposed_load_kn_m, shear_concrete_capacity_n_mm2=None,
                link_steel_fy_nmm2=None):
    require_positive(span_m=span_m, width_mm=width_mm, overall_depth_mm=overall_depth_mm,
        link_diameter_mm=link_diameter_mm, main_bar_diameter_mm=main_bar_diameter_mm,
        fcu_nmm2=fcu_nmm2, fy_nmm2=fy_nmm2)
    if dead_load_kn_m < 0 or imposed_load_kn_m < 0:
        raise ValueError("Characteristic loads cannot be negative.")
    if cover_mm < 0:
        raise ValueError("Cover cannot be negative.")
    if cover_mm + link_diameter_mm + main_bar_diameter_mm/2 >= overall_depth_mm:
        raise ValueError("Cover, link and bar geometry leave no positive effective depth.")
    d = overall_depth_mm-cover_mm-link_diameter_mm-main_bar_diameter_mm/2
    require_positive(effective_depth_mm=d)
    wu = 1.4*dead_load_kn_m + 1.6*imposed_load_kn_m
    m = wu*span_m**2/8
    v = wu*span_m/2
    flex = flexural_steel_area(m, width_mm, d, fcu_nmm2, fy_nmm2)
    n_bars = max(2, math.ceil(flex["As_required_mm2"]/bar_area(main_bar_diameter_mm)))
    result = {"member":"Beam", "basis":"Simply supported rectangular beam under UDL",
        "span_m":span_m, "b_mm":width_mm, "h_mm":overall_depth_mm, "d_mm":d,
        "fcu_nmm2":fcu_nmm2, "fy_nmm2":fy_nmm2,
        "Gk_kN_m":dead_load_kn_m, "Qk_kN_m":imposed_load_kn_m, "wu_kN_m":wu,
        "MEd_kNm":m, "VEd_kN":v, **flex,
        "main_bar_diameter_mm":main_bar_diameter_mm, "main_bars_by_area":n_bars,
        "As_provided_mm2":n_bars*bar_area(main_bar_diameter_mm),
        "shear_assessment":"NOT CHECKED: enter a verified BS 8110 vc table value to enable preliminary link screening.",
        "calculation_scope":"Preliminary simply-supported rectangular beam under full-span UDL; not a complete BS 8110 design."}
    if shear_concrete_capacity_n_mm2 is not None:
        vc = shear_concrete_capacity_n_mm2
        require_positive(shear_concrete_capacity_n_mm2=vc)
        fyv = link_steel_fy_nmm2 or fy_nmm2
        stress = v*1000/(width_mm*d)
        av = 2*bar_area(link_diameter_mm)
        asv_s = (0.4*width_mm/(0.87*fyv)) if stress <= vc else ((stress-vc)*width_mm/(0.87*fyv))
        spacing_strength = av/asv_s
        spacing_limit = min(0.75*d, 300.0)
        spacing = min(spacing_strength, spacing_limit)
        result.update({"ved_N_mm2":stress, "vc_entered_N_mm2":vc,
            "two_leg_link_area_mm2":av, "link_spacing_strength_mm":spacing_strength,
            "link_spacing_limit_mm":spacing_limit,
            "recommended_link_spacing_mm":max(25, int(spacing//5*5)),
            "shear_assessment":"Preliminary link screening using the user-entered concrete shear capacity. Verify table selection and detailing."})
    return result
