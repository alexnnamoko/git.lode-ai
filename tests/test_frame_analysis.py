import math
import pytest
from lode.analysis.frame_model import build_regular_frame
from lode.analysis.frame2d import analyse_frame_2d


def test_generated_frame_has_expected_connectivity_and_properties():
    model = build_regular_frame(2, 2, 4, 3, 225, 450, 300, 300, 25)
    assert len(model['nodes']) == 9
    assert len(model['members']) == 12  # 6 beam segments + 6 column segments
    assert len(model['supports']) == 3
    assert all(m['A_m2'] > 0 and m['I_m4'] > 0 for m in model['members'])


def test_cantilever_column_matches_closed_form_tip_displacement_and_reactions():
    nodes = [{'id':'A','x_m':0,'y_m':0},{'id':'B','x_m':0,'y_m':3}]
    members = [{'id':'C1','i':'A','j':'B','E_kN_m2':200_000_000,'A_m2':0.01,'I_m4':0.0001}]
    r = analyse_frame_2d(nodes, members, {'A':[True,True,True]}, {'B':[10,0,0]})
    top = next(n for n in r['nodes'] if n['node_id']=='B')
    base = next(n for n in r['nodes'] if n['node_id']=='A')
    expected_mm = 10*3**3/(3*200_000_000*0.0001)*1000
    assert top['ux_mm'] == pytest.approx(expected_mm, rel=1e-8)
    assert base['reaction_Fx_kN'] == pytest.approx(-10, abs=1e-8)
    assert base['reaction_Mz_kNm'] == pytest.approx(30, abs=1e-8)


def test_unrestrained_frame_is_rejected_as_singular():
    nodes = [{'id':'A','x_m':0,'y_m':0},{'id':'B','x_m':1,'y_m':0}]
    members = [{'id':'B1','i':'A','j':'B','E_kN_m2':25e6,'A_m2':0.1,'I_m4':0.001}]
    with pytest.raises(ValueError, match='restrained'):
        analyse_frame_2d(nodes,members,{}, {'B':[1,0,0]})


def test_generated_frame_can_be_analysed():
    model=build_regular_frame(1,1,4,3,225,450,300,300,25)
    loads={'N1_0':[10,-20,0], 'N1_1':[10,-20,0]}
    r=analyse_frame_2d(model['nodes'],model['members'],model['supports'],loads)
    assert len(r['members']) == 4
    assert all(math.isfinite(x['ux_mm']) and math.isfinite(x['uy_mm']) for x in r['nodes'])
