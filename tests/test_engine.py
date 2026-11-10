import pytest
from lode.engine.beam import design_beam
from lode.engine.slab import design_one_way_slab
from lode.engine.column import design_short_axially_loaded_column

def test_beam_runs():
    r=design_beam(span_m=4,width_mm=225,overall_depth_mm=450,cover_mm=25,
        link_diameter_mm=8,main_bar_diameter_mm=20,fcu_nmm2=25,fy_nmm2=460,
        dead_load_kn_m=20,imposed_load_kn_m=10)
    assert r["MEd_kNm"]>0 and r["As_required_mm2"]>0

def test_beam_rejects_unsupported_doubly_reinforced_case():
    with pytest.raises(ValueError):
        design_beam(span_m=4,width_mm=150,overall_depth_mm=200,cover_mm=25,
            link_diameter_mm=8,main_bar_diameter_mm=25,fcu_nmm2=20,fy_nmm2=250,
            dead_load_kn_m=200,imposed_load_kn_m=100)

def test_slab_runs():
    r=design_one_way_slab(span_m=3.5,thickness_mm=160,cover_mm=20,
        bar_diameter_mm=10,fcu_nmm2=25,fy_nmm2=460,
        dead_load_kn_m2=4,imposed_load_kn_m2=2)
    assert r["MEd_kNm_per_m"]>0 and r["As_required_mm2"]>0

def test_column_requires_short_column_confirmation():
    with pytest.raises(ValueError):
        design_short_axially_loaded_column(width_mm=300,depth_mm=300,axial_load_kn=800,
            fcu_nmm2=25,fy_nmm2=460,bar_diameter_mm=20,number_of_bars=8)

def test_column_runs_after_confirmation():
    r=design_short_axially_loaded_column(width_mm=300,depth_mm=300,axial_load_kn=800,
        fcu_nmm2=25,fy_nmm2=460,bar_diameter_mm=20,number_of_bars=8,
        confirmed_short_column=True)
    assert r["Nu_capacity_kN"]>0

def test_beam_verifier_recalculates_selected_arithmetic():
    from lode.verification.engine import verify_design_result
    r=design_beam(span_m=4,width_mm=225,overall_depth_mm=450,cover_mm=25,
        link_diameter_mm=8,main_bar_diameter_mm=20,fcu_nmm2=25,fy_nmm2=460,
        dead_load_kn_m=20,imposed_load_kn_m=10)
    v=verify_design_result(r)
    assert v["overall_status"].startswith("PASS")
    assert all(x["status"] == "PASS" for x in v["checks"])
    assert v["not_a_compliance_certificate"] is True

def test_beam_verifier_detects_tampered_moment():
    from lode.verification.engine import verify_design_result
    r=design_beam(span_m=4,width_mm=225,overall_depth_mm=450,cover_mm=25,
        link_diameter_mm=8,main_bar_diameter_mm=20,fcu_nmm2=25,fy_nmm2=460,
        dead_load_kn_m=20,imposed_load_kn_m=10)
    r["MEd_kNm"] += 1
    assert verify_design_result(r)["overall_status"] == "FAIL"

def test_slab_verifier_recalculates_selected_arithmetic():
    from lode.verification.engine import verify_design_result
    r=design_one_way_slab(span_m=3.5,thickness_mm=160,cover_mm=20,
        bar_diameter_mm=10,fcu_nmm2=25,fy_nmm2=460,dead_load_kn_m2=4,imposed_load_kn_m2=2)
    assert verify_design_result(r)["overall_status"].startswith("PASS")

def test_column_verifier_recalculates_axial_expression():
    from lode.verification.engine import verify_design_result
    r=design_short_axially_loaded_column(width_mm=300,depth_mm=300,axial_load_kn=800,
        fcu_nmm2=25,fy_nmm2=460,bar_diameter_mm=20,number_of_bars=8,confirmed_short_column=True)
    assert verify_design_result(r)["overall_status"].startswith("PASS")

def test_beam_rejects_impossible_effective_depth_geometry():
    with pytest.raises(ValueError):
        design_beam(span_m=4,width_mm=225,overall_depth_mm=40,cover_mm=25,
            link_diameter_mm=8,main_bar_diameter_mm=20,fcu_nmm2=25,fy_nmm2=460,
            dead_load_kn_m=20,imposed_load_kn_m=10)
