"""Generate entirely fictional GPS pings, plus an independent clean-track oracle."""
import csv, json, random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from pyproj import CRS, Transformer
from shapely.geometry import LineString, box

ROOT=Path(__file__).resolve().parent
LOCAL=ZoneInfo('Asia/Tokyo')
CRS_LOCAL=CRS.from_proj4('+proj=aeqd +lat_0=35.7 +lon_0=139.7 +datum=WGS84 +units=m +no_defs')
TO_GEO=Transformer.from_crs(CRS_LOCAL,'EPSG:4326',always_xy=True)
ZONE=box(400,-100,2600,100)
DRIVERS=['SYNTH-A','SYNTH-B','SYNTH-C']

def segment_km(a,b):
    return LineString([a,b]).intersection(ZONE).length / 1000 if a != b else 0.0

def main():
    rng=random.Random(20261118)
    clean=[]; noise=[]; duplicates=[]; truth=defaultdict(float)
    seq=0
    for driver_idx,driver in enumerate(DRIVERS):
      for day_no in range(2):
        date=(datetime(2026,11,16,tzinfo=LOCAL)+timedelta(days=day_no)).date()
        # Two runs per day, no distance credited across a long stop.
        for session,n,start_hour,start_minute,step in [(0,300,12,0,60),(1,120,23,40,38)]:
          start=datetime(date.year,date.month,date.day,start_hour,start_minute,tzinfo=LOCAL)
          previous=None
          for i in range(n):
            # A fictional vehicle repeatedly driving along a straight road, with turns at its ends.
            progress=(i*step + driver_idx*77 + day_no*113 + session*51)%6400
            x=progress if progress<=3200 else 6400-progress
            y=0.0
            t=start+timedelta(seconds=10*i)
            lon,lat=TO_GEO.transform(x,y)
            seq+=1
            ping={'ping_id':f'P{seq:05d}','driver_id':driver,'timestamp_utc':t.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                  'lat':f'{lat:.9f}','lon':f'{lon:.9f}','arrival_order':seq,'synthetic_fault':'none'}
            clean.append(ping)
            if previous is not None:
              truth[(driver,t.date().isoformat())]+=segment_km(previous,(x,y))
            previous=(x,y)
            # Duplicated timestamp but different near-road position: accepted by buggy speed filter.
            if i>8 and i%37==0:
              oldprogress=((i-1)*step + driver_idx*77 + day_no*113 + session*51)%6400
              oldx=oldprogress if oldprogress<=3200 else 6400-oldprogress
              duplicate_x=x+(oldx-x)*0.45
              dlon,dlat=TO_GEO.transform(duplicate_x,0)
              seq+=1
              duplicates.append({**ping,'ping_id':f'P{seq:05d}','lat':f'{dlat:.9f}','lon':f'{dlon:.9f}',
                                 'arrival_order':seq,'synthetic_fault':'duplicate_timestamp'})
            if i>9 and i%101==0:
              nlon,nlat=TO_GEO.transform(x,240)
              seq+=1
              noise.append({**ping,'ping_id':f'P{seq:05d}','timestamp_utc':(t+timedelta(seconds=2)).astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                            'lat':f'{nlat:.9f}','lon':f'{nlon:.9f}','arrival_order':seq,'synthetic_fault':'off_road'})
            if i>9 and i%137==0:
              jumpx=3200 if x<1600 else 0
              jlon,jlat=TO_GEO.transform(jumpx,0)
              seq+=1
              noise.append({**ping,'ping_id':f'P{seq:05d}','timestamp_utc':(t+timedelta(seconds=3)).astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                            'lat':f'{jlat:.9f}','lon':f'{jlon:.9f}','arrival_order':seq,'synthetic_fault':'speed_spike'})
    rows=clean+duplicates+noise
    rng.shuffle(rows) # Late/out-of-order arrival order in file, original arrival_order preserved.
    with (ROOT/'data'/'synthetic_pings.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    oracle={'disclaimer':'ALL DATA SYNTHETIC. Fictional Tokyo-like coordinate reference; no real drivers or journeys.',
            'generation_seed':20261118,'clean_pings':len(clean),'total_pings':len(rows),
            'injected_duplicate_rows':len(duplicates),'injected_offroad_rows':sum(r['synthetic_fault']=='off_road' for r in noise),
            'injected_speed_spike_rows':sum(r['synthetic_fault']=='speed_spike' for r in noise),
            'expected_km':{d:{day:round(truth[(d,day)],6) for day in ['2026-11-16','2026-11-17']} for d in DRIVERS}}
    (ROOT/'data'/'oracle.json').write_text(json.dumps(oracle,indent=2)+'\n')
    print(f'Generated {len(rows)} labelled synthetic rows; {len(duplicates)} duplicates; {len(noise)} noise rows')

if __name__=='__main__':main()
