import pytest
from lode.analysis.beam_analysis import (
    analyse_cantilever_point_load,
    analyse_propped_cantilever_central_point_load,
)
from lode.analysis.frame2d import analyse_frame_2d


def test_bm003_cantilever_point_load_closed_form():
    r = analyse_cantilever_point_load(3.0, 10.0)
    assert r["reaction_vertical_kN"] == pytest.approx(10.0)
    assert r["reaction_moment_kNm"] == pytest.approx(30.0)
    assert r["max_abs_shear_kN"] == pytest.approx(10.0)
    assert r["max_abs_moment_kNm"] == pytest.approx(30.0)


def test_bm004_propped_cantilever_closed_form():
    r = analyse_propped_cantilever_central_point_load(6.0, 20.0)
    assert r["reaction_A_vertical_kN"] == pytest.approx(13.75)
    assert r["reaction_B_vertical_kN"] == pytest.approx(6.25)
    assert r["reaction_A_moment_kNm"] == pytest.approx(22.5)
    assert r["equilibrium_vertical_error_kN"] == pytest.approx(0.0)
    assert r["equilibrium_moment_error_kNm"] == pytest.approx(0.0)


def test_bm004_frame_solver_matches_propped_cantilever_reactions():
    nodes = [{"id": "A", "x_m": 0, "y_m": 0}, {"id": "M", "x_m": 3, "y_m": 0}, {"id": "B", "x_m": 6, "y_m": 0}]
    def m(mid, i, j):
        return {"id": mid, "i": i, "j": j, "E_kN_m2": 200_000_000, "A_m2": 0.02, "I_m4": 8e-5}
    result = analyse_frame_2d(nodes, [m("AM", "A", "M"), m("MB", "M", "B")],
                             {"A": [True, True, True], "B": [False, True, False]}, {"M": [0, -20, 0]})
    n = {x["node_id"]: x for x in result["nodes"]}
    assert n["A"]["reaction_Fy_kN"] == pytest.approx(13.75, abs=1e-8)
    assert n["B"]["reaction_Fy_kN"] == pytest.approx(6.25, abs=1e-8)
    assert n["A"]["reaction_Mz_kNm"] == pytest.approx(22.5, abs=1e-8)


def test_bm005_and_bm006_benchmark_runner_passes():
    from benchmarks.run_benchmarks import run
    results = {x["id"]: x for x in run()["results"]}
    assert all(results[k]["status"] == "PASS" for k in ["BM001", "BM002", "BM003", "BM004", "BM005", "BM006"])
    assert results["BM005"]["max_abs_difference"] < 1e-6
    assert results["BM006"]["max_abs_difference"] < 1e-6


def test_cantilever_rejects_negative_load():
    with pytest.raises(ValueError):
        analyse_cantilever_point_load(3, -1)
