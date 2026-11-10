import math
from .common import require_positive, flexural_steel_area, bar_area

def design_one_way_slab(*, span_m, thickness_mm, cover_mm, bar_diameter_mm,
                        fcu_nmm2, fy_nmm2, dead_load_kn_m2, imposed_load_kn_m2):
    require_positive(span_m=span_m, thickness_mm=thickness_mm, bar_diameter_mm=bar_diameter_mm,
        fcu_nmm2=fcu_nmm2, fy_nmm2=fy_nmm2)
    if dead_load_kn_m2 < 0 or imposed_load_kn_m2 < 0:
        raise ValueError("Characteristic loads cannot be negative.")
    if cover_mm < 0 or cover_mm + bar_diameter_mm/2 >= thickness_mm:
        raise ValueError("Cover and bar geometry must leave a positive effective depth.")
    d = thickness_mm-cover_mm-bar_diameter_mm/2
    require_positive(effective_depth_mm=d)
    wu = 1.4*dead_load_kn_m2 + 1.6*imposed_load_kn_m2
    m = wu*span_m**2/8  # 1 m strip, simply supported
    flex = flexural_steel_area(m, 1000.0, d, fcu_nmm2, fy_nmm2)
    area = bar_area(bar_diameter_mm)
    n = math.ceil(flex["As_required_mm2"]/area)
    spacing = 1000/n
    ratio = span_m*1000/d
    return {"member":"One-way slab (1 m strip)",
        "basis":"Simply supported one-way slab strip, 1,000 mm wide, UDL",
        "span_m":span_m, "strip_width_mm":1000, "thickness_mm":thickness_mm,
        "d_mm":d, "Gk_kN_m2":dead_load_kn_m2, "Qk_kN_m2":imposed_load_kn_m2,
        "wu_kN_m2":wu, "MEd_kNm_per_m":m, **flex,
        "main_bar_diameter_mm":bar_diameter_mm, "bars_per_m_by_area":n,
        "approx_spacing_mm":spacing, "As_provided_mm2":n*area,
        "fcu_nmm2":fcu_nmm2, "fy_nmm2":fy_nmm2,
        "actual_span_depth_ratio":ratio,
        "basic_ratio_screen":"PASS" if ratio <= 20 else "REVIEW",
        "deflection_note":"Basic span/depth screening only; modification factors and full serviceability checks are not applied.",
        "calculation_scope":"Preliminary simply-supported one-way slab strip under UDL; not a complete BS 8110 slab design."}
