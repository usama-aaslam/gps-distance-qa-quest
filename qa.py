"""One QA tool: explain GPS distance errors, compare against an independent oracle."""
import argparse,csv,json,math
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from pyproj import CRS,Transformer
from shapely.geometry import LineString, Point,box

ROOT=Path(__file__).resolve().parent
LOCAL=ZoneInfo('Asia/Tokyo')
CRS_LOCAL=CRS.from_proj4('+proj=aeqd +lat_0=35.7 +lon_0=139.7 +datum=WGS84 +units=m +no_defs')
TO_METERS=Transformer.from_crs('EPSG:4326',CRS_LOCAL,always_xy=True)
ROAD=LineString([(0,0),(3200,0)])
ZONE=box(400,-100,2600,100)
MAX_SPEED_MPS=150/3.6

def read_pings(path=ROOT/'data'/'synthetic_pings.csv'):
  with Path(path).open(newline='') as f:
    data=list(csv.DictReader(f))
  for r in data:
    r['time']=datetime.fromisoformat(r['timestamp_utc'].replace('Z','+00:00'))
    r['point']=TO_METERS.transform(float(r['lon']),float(r['lat']))
    r['arrival_order']=int(r['arrival_order'])
  return data

def deduplicate(rows):
  """Policy: first received observation for a (driver,timestamp), based on arrival_order."""
  seen=set(); out=[]; removed=[]
  for r in sorted(rows,key=lambda p:p['arrival_order']):
    k=(r['driver_id'],r['time'])
    if k in seen:removed.append(r)
    else:seen.add(k);out.append(r)
  return out,removed

def filter_noise(rows):
  """Road tolerance first, then speed versus last retained DISTINCT timestamp."""
  grouped=defaultdict(list)
  for r in rows:grouped[r['driver_id']].append(r)
  kept=[];excluded=[]
  for driver,arr in grouped.items():
    previous=None
    for r in sorted(arr,key=lambda p:(p['time'],p['arrival_order'])):
      if Point(r['point']).distance(ROAD)>100:
        excluded.append((r,'off_road_gt_100m'));continue
      if previous is not None:
        elapsed=(r['time']-previous['time']).total_seconds()
        if elapsed>0 and elapsed<=20 and math.dist(r['point'],previous['point'])/elapsed>MAX_SPEED_MPS:
          excluded.append((r,'speed_gt_150kmh'));continue
      kept.append(r)
      # An equal-time duplicate is not a speed reference; this is the defect under test.
      if previous is None or r['time']>previous['time']:
        previous=r
  return kept,excluded

def distances(rows):
  groups=defaultdict(list)
  for r in rows:groups[r['driver_id']].append(r)
  totals=defaultdict(float)
  for driver,arr in groups.items():
    arr=sorted(arr,key=lambda p:(p['time'],p['arrival_order']))
    for prev,cur in zip(arr,arr[1:]):
      dt=(cur['time']-prev['time']).total_seconds()
      if dt<0 or dt>20:continue  # No interpolation over an unknown long gap.
      # The generator avoids moving segments across local midnight; regression covers boundary assignment.
      day=cur['time'].astimezone(LOCAL).date().isoformat()
      if prev['time'].astimezone(LOCAL).date().isoformat()!=day:
        continue # crossing-midnight segments explicitly out of scope (documented)
      if cur['point']!=prev['point']:
        totals[(driver,day)]+=LineString([prev['point'],cur['point']]).intersection(ZONE).length/1000
  return totals

def compute(rows,mode='fixed'):
  if mode=='fixed':
    rows,duplicate_removed=deduplicate(rows)
  else:duplicate_removed=[]
  kept,excluded=filter_noise(rows)
  return distances(kept),duplicate_removed,excluded,kept

def report(mode='fixed',verbose=True):
  rows=read_pings()
  observed,dupes,excluded,kept=compute(rows,mode)
  oracle=json.loads((ROOT/'data'/'oracle.json').read_text())
  expected={(d,day):km for d,days in oracle['expected_km'].items() for day,km in days.items()}
  # Measurement tolerances cover 9-decimal-place synthetic coordinate storage.
  violations=[(key,observed.get(key,0)-km) for key,km in expected.items() if abs(observed.get(key,0)-km)>0.002]
  # Catch invented extra driver-days too.
  violations.extend((key,km) for key,km in observed.items() if key not in expected and abs(km)>0.002)
  if mode=='fixed':
    audit_path=ROOT/'data'/'duplicate_audit.csv'
    canonical={(r['driver_id'],r['time']):r for r in sorted(rows,key=lambda r:r['arrival_order']) if r not in dupes}
    with audit_path.open('w',newline='') as out:
      w=csv.DictWriter(out,fieldnames=['excluded_ping_id','retained_ping_id','driver_id','timestamp_utc','local_day','reason'])
      w.writeheader()
      for r in dupes:
        winner=canonical[(r['driver_id'],r['time'])]
        w.writerow({'excluded_ping_id':r['ping_id'],'retained_ping_id':winner['ping_id'],'driver_id':r['driver_id'],
                    'timestamp_utc':r['timestamp_utc'],'local_day':r['time'].astimezone(LOCAL).date().isoformat(),
                    'reason':'same driver+timestamp; later arrival_order'})
  if verbose:
    print(f'\n=== {mode.upper()} ENGINE — ALL DATA SYNTHETIC ===')
    print(f'input={len(rows)} accepted={len(kept)} duplicates_removed={len(dupes)} noise_removed={len(excluded)}')
    print('noise_types='+str(dict(Counter(why for _,why in excluded))))
    print('driver       local_day    actual_km    oracle_km    error_km   status')
    for key in sorted(expected):
      actual=observed.get(key,0);delta=actual-expected[key]
      print(f'{key[0]:12} {key[1]} {actual:11.6f} {expected[key]:11.6f} {delta:+11.6f}  {"FAIL" if abs(delta)>0.002 else "PASS"}')
    print('verdict='+('FAIL' if violations else 'PASS'))
    if mode=='fixed':
      print('\nDuplicate examples (full 66-row audit: data/duplicate_audit.csv):')
      for r in dupes[:8]:
        prev=canonical[(r['driver_id'],r['time'])]
        print(f'  {r["ping_id"]} -> {prev["ping_id"]} / {r["timestamp_utc"]} / same driver+timestamp, later arrival')
  return not violations

if __name__=='__main__':
  ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['old','fixed'],default='fixed');ap.add_argument('--verify',action='store_true')
  args=ap.parse_args();ok=report(args.mode)
  if args.verify and not ok:raise SystemExit(1)
