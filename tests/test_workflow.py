import pytest
from lode.analysis.beam_analysis import analyse_simply_supported_beam
from lode.drawing.extract import candidate_dimensions
from lode.detailing.schedule import bar_area, choose_bars, beam_schedule
from lode.knowledge.retrieval import search_knowledge, readable_record

def test_udl_beam_reactions_and_diagrams():
    r=analyse_simply_supported_beam(4,10,[])
    assert r['reaction_A_kN']==pytest.approx(20)
    assert r['reaction_B_kN']==pytest.approx(20)
    assert r['max_abs_moment_kNm']==pytest.approx(20)
    assert r['max_abs_shear_kN']==pytest.approx(20)
    assert r['equilibrium_vertical_error_kN']<1e-9

def test_central_point_load():
    r=analyse_simply_supported_beam(6,0,[{'x_m':3,'load_kn':30}])
    assert r['reaction_A_kN']==pytest.approx(15)
    assert r['reaction_B_kN']==pytest.approx(15)
    assert r['max_abs_moment_kNm']==pytest.approx(45)

def test_multiple_point_loads_and_udl_equilibrium():
    r=analyse_simply_supported_beam(8,5,[{'x_m':2,'load_kn':10},{'x_m':6,'load_kn':20}])
    assert r['reaction_A_kN']+r['reaction_B_kN']==pytest.approx(70)
    assert r['equilibrium_moment_error_kNm']<1e-9

def test_reject_load_outside_span():
    with pytest.raises(ValueError): analyse_simply_supported_beam(4,0,[{'x_m':5,'load_kn':10}])

def test_units_and_bar_selection():
    assert bar_area(20)==pytest.approx(314.159265,rel=1e-5)
    r=choose_bars(600)
    assert r['provided_area_mm2']>=600

def test_beam_schedule_marks_incomplete_details():
    r=beam_schedule(600,8,200,25)
    assert r['status'].startswith('PRELIMINARY')
    assert 'anchorage' in r['status']

def test_dimension_candidates_are_unverified():
    r=candidate_dimensions('Beam B1 450mm wide 600 mm deep, span 4.2m',2)
    assert len(r)>=3
    assert all(x['status']=='Unverified' and x['page']==2 for x in r)

def test_knowledge_results_are_renderable_and_reference_labelled():
    hits=search_knowledge('characteristic strength concrete',5)
    assert hits
    readable=readable_record(hits[0])
    assert readable['reference']
    assert readable['title']

def test_retrieval_returns_ranked_records_with_positive_scores():
    hits = search_knowledge("What is the scope of BS 8110-1:1997?", limit=5)
    assert hits
    assert all(hit["score"] > 0 for hit in hits)
    assert readable_record(hits[0])["reference"] == "1.1"

def test_knowledge_audit_reports_structural_summary():
    from lode.knowledge.audit import audit_knowledge_datasets
    audit = audit_knowledge_datasets()
    assert audit["summary"]["rule"]["records"] == 135
    assert audit["summary"]["qa"]["records"] == 200
    assert audit["limitations"]


def test_retrieval_tokenises_numeric_clause_references():
    from lode.knowledge.retrieval import _tokens
    tokens = _tokens("Clause 3.4.4 requires 450 mm depth")
    assert "3.4.4" in tokens
    assert "450" in tokens


def test_retrieval_exact_clause_filter_is_strict():
    exact = search_knowledge("Explain clause 1.1", limit=10)
    assert exact
    assert all(readable_record(hit)["reference"] == "1.1" for hit in exact)
    assert search_knowledge("Explain clause 99.99.99", limit=5) == []


def test_retrieval_context_includes_provenance_and_uncertainty_label():
    from lode.knowledge.retrieval import format_retrieval_context
    hits = search_knowledge("scope of BS 8110", limit=2)
    context = format_retrieval_context(hits)
    assert "Dataset file:" in context
    assert "Record identifier:" in context
    assert "verify wording and applicability" in context
    assert "not confidence" in context


def test_zero_retrieval_limit_returns_no_records():
    assert search_knowledge("beam design", limit=0) == []


def test_project_context_excludes_pending_drawing_proposals():
    from lode.ai.context import build_project_context
    context = build_project_context(
        project_name="Test building",
        project_notes="Three-storey RC frame",
        verified_observations=[
            {"element_type": "beam", "label": "B1", "value": "450", "unit": "mm", "page": 2,
             "status": "Verified by engineer"},
            {"element_type": "column", "label": "C1", "value": "300", "unit": "mm", "page": 2,
             "status": "Pending engineer verification"},
        ],
    )
    assert "Test building" in context
    assert "B1" in context
    assert "C1" not in context


def test_project_context_is_empty_without_project_details_or_verified_observations():
    from lode.ai.context import build_project_context
    assert build_project_context() == ""


def test_vision_observation_validation_rejects_invalid_boxes_and_types():
    from lode.drawing.validation import normalise_vision_response
    result = normalise_vision_response({
        "page_summary": "A structural plan",
        "observations": [
            {"element_type": "beam", "label": "B1", "value": "450", "unit": "mm",
             "bbox_normalized": [0.1, 0.2, 0.8, 0.9], "model_certainty": "high"},
            {"element_type": "invented", "label": "X", "bbox_normalized": [0.8, 0.2, 0.1, 0.9]},
        ],
        "uncertain_or_missing": ["Depth unclear"],
    })
    assert result["observations"][0]["bbox_normalized"] == [0.1, 0.2, 0.8, 0.9]
    assert result["observations"][0]["verification_status"] == "Pending engineer verification"
    assert result["observations"][1]["element_type"] == "unknown"
    assert result["observations"][1]["bbox_normalized"] is None
    assert result["validation_warnings"]
    assert "not a calibrated" in result["safety_note"] or "require engineer confirmation" in result["safety_note"]


def test_vision_observation_validation_requires_list_shape():
    from lode.drawing.validation import normalise_vision_response
    with pytest.raises(ValueError, match="must be a list"):
        normalise_vision_response({"observations": {"element_type": "beam"}})


def test_review_register_merge_suppresses_duplicate_vision_proposals():
    from lode.drawing.validation import merge_review_observations
    existing = [{"page": 1, "source_drawing": "plan.pdf", "element_type": "beam", "label": "B1", "value": "450"}]
    candidates = [
        {"element_type": "beam", "label": "B1", "value": "450", "unit": "mm"},
        {"element_type": "column", "label": "C1", "value": "300", "unit": "mm"},
    ]
    merged, added = merge_review_observations(existing, candidates, page=1, source_drawing="plan.pdf")
    assert added == 1
    assert len(merged) == 2
    assert merged[-1]["status"] == "Pending engineer verification"
    assert merged[-1]["model_certainty"] == "unknown"
