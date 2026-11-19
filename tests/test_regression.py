import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa import compute,read_pings,distances,LOCAL
from collections import Counter
from datetime import datetime,timezone

def test_fixed_matches_independent_clean_oracle():
    import json
    root=Path(__file__).resolve().parents[1]
    oracle=json.loads((root/'data/oracle.json').read_text())
    actual,duplicates,noise,kept=compute(read_pings(),'fixed')
    for driver,days in oracle['expected_km'].items():
        for day,expected in days.items():
            assert abs(actual[(driver,day)]-expected)<0.002
    assert len(duplicates)==oracle['injected_duplicate_rows']
    assert len(set((r['driver_id'],r['time']) for r in kept))==len(kept)
    reasons=Counter(reason for _,reason in noise)
    assert reasons['off_road_gt_100m']==oracle['injected_offroad_rows']
    assert reasons['speed_gt_150kmh']==oracle['injected_speed_spike_rows']

def test_old_engine_must_not_match_oracle():
    import json
    root=Path(__file__).resolve().parents[1]
    oracle=json.loads((root/'data/oracle.json').read_text())
    actual,_,_,_=compute(read_pings(),'old')
    assert any(abs(actual[(d,day)]-v)>0.002 for d,days in oracle['expected_km'].items() for day,v in days.items())

def test_utc_to_local_midnight_cut():
    assert datetime(2026,11,16,14,59,59,tzinfo=timezone.utc).astimezone(LOCAL).date().isoformat()=='2026-11-16'
    assert datetime(2026,11,16,15,0,0,tzinfo=timezone.utc).astimezone(LOCAL).date().isoformat()=='2026-11-17'

def test_no_extra_distance_for_equal_coordinates():
    r=read_pings()[0].copy();q=r.copy();q['time']=r['time']
    assert sum(distances([r,q]).values())==0
