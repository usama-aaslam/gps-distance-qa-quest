# Evidence reproducible problem, fix and regression

**Status:** Tested locally using synthetic data only. Not deployed to any live platform. No actual advertiser charges or driver payments occurred.

## One-command reproduction

From the repository root, with Python 3.10+:

```bash
python -m pip install -r requirements.txt
python run.py
```

`run.py` deterministically regenerates the synthetic dataset and independent oracle, deliberately runs the old checker expecting **exit 1**, then runs the fixed checker expecting **exit 0**, then executes four pytest tests. The final wrapper exits **0 only if** the old regression failed, the fixed check passed, and the tests passed. A checked execution transcript is included in `run_output.txt`.

## Before / after, kilometres inside zone

| Driver | Local day UTC+9 | Old km | Fixed km | Oracle km | Artificial km removed |
|---|---|---:|---:|---:|---:|
| SYNTH-A | 2026-11-16 | 15.705400 | 15.313000 | 15.313000 | 0.392400 |
| SYNTH-A | 2026-11-17 | 15.931400 | 15.539000 | 15.539000 | 0.392400 |
| SYNTH-B | 2026-11-16 | 15.859400 | 15.467000 | 15.467000 | 0.392400 |
| SYNTH-B | 2026-11-17 | 16.085400 | 15.693000 | 15.693000 | 0.392400 |
| SYNTH-C | 2026-11-16 | 15.987400 | 15.621000 | 15.621000 | 0.366400 |
| SYNTH-C | 2026-11-17 | 16.239400 | 15.847000 | 15.847000 | 0.392400 |
| **Total** | **6 driver-days** | **95.808400** | **93.480000** | **93.480000** | **2.328400** |

*The displayed six-decimal numerical results are reproducible. Projection/serialization differences below 0.002 km are tolerated per driver-day.*

## Fault root cause

The old engine sorts pings by UTC timestamp but never removes duplicate `(driver_id, timestamp_utc)` observations. Synthetic duplicates have slightly different near-road coordinates. A speed validation that checks only positive elapsed time does not treat an equal-timestamp pair as a speed violation. The distance integrator then treats the two coordinates as real consecutive motion, introducing invented backtracking and forward travel. The result was **2.3284 false kilometres, a 2.49% overstatement relative to 93.48 legitimate kilometres**.

The corrected path selects the *earliest ingested* record per driver/UTC timestamp before applying the same off-road/speed filters and clipping line segments against the zone. Exact row-level exclusions appear in `data/duplicate_audit.csv`. Example: excluded `P00039` in favour of `P00038` at `2026-11-16T03:06:10Z`, because the driver/timestamp is identical but `P00039` arrived later. This choice is explicitly a synthetic conflict-resolution policy.

## Regression evidence

- Old: `python qa.py --mode old --verify` => **exit 1**, all six daily distances **FAIL**; 0 duplicates removed.
- Fixed: `python qa.py --mode fixed --verify` => **exit 0**, all six daily distances **PASS**; 66 duplicates removed.
- Pytest: **4 passed**. Tests cover agreement with independently generated expected values; injected noise counts; no counted duplicate keys; proof that the old reference is incorrect; exact UTC+9 date change; and zero distance for repeated identical coordinates.
- Noise: **30 of 30 injected pings excluded** (18 off-road >100m and 12 jumps >150km/h); this pre-existing capability is held constant in both versions. Among 2,616 total records, noise is **1.1468%**; duplicates are a further **2.5229%**. Correct accepted unique clean rows: 2,520.
- Input rows are deliberately shuffled, but calculation sorts by each event's UTC timestamp; no reliance on CSV row order.

## Existing pieces reused versus gap built

| Component | Existing capability reused | Work built |
|---|---|---|
| Distance, road and zone geometry | Shapely `LineString`, `Point`, `box` intersections and line lengths | Campaign zone and reference synthetic route; distance aggregation |
| Coordinate reference | `pyproj` AEQD metres ↔ WGS84 lat/lon | Deterministic fictional track generator and conversion |
| Local date | Python standard `datetime`, `zoneinfo` (`Asia/Tokyo`, UTC+9) | Per-driver local-day grouping |
| Tests | `pytest` | Regression cases and old-vs-new CLI verification |
| Root-cause QA | Standard `csv`, `collections`, `argparse` | Timestamp deduplication, audit CSV linking excluded and retained row IDs, driver-day evidence |

`Shapely`, `pyproj`, `zoneinfo` and `pytest` were checked for availability before implementation. No bespoke geospatial or timezone library was necessary. Dependencies are recorded in `requirements.txt`.

## AI assistance and checking

AI drafted the scenario, synthetic generator, one checker, tests and narrative. Checks were performed by executing the generated code: count assertions, oracle comparisons independent of the engine, nonzero old exit, zero fixed exit, and four passing automated tests. A fixed RNG seed makes the shuffled dataset deterministic. AI-generated statements were reconciled against the printed numbers; no live incidents, production screenshots or financial results are claimed.

## Remaining unsolved

1. Long GPS gaps are **not interpolated**: segments more than 20 seconds apart earn no distance here; a production policy needs agreement.
2. A moving segment crossing precisely 00:00 local is **not split** and would currently be skipped; the generated sessions contain no such segment. The tested clock cutoff is correct, but cross-midnight distance attribution needs further work.
3. Multiple position reports sharing one timestamp may require a stronger representative-selection policy than earliest ingestion, especially if the first report itself is corrupt.
4. A linear synthetic road and rectangular zone are not a realistic production road network; no map matching, multipath confidence, tunnels or phone power-saving behaviour is evaluated.
5. The filtering intentionally retains the existing simple last-valid-point speed check; performance on sustained GPS drift, rejected-anchor cascades, and complex boundary crossings is not fully proven.
6. No commercial deployment, advertiser reconciliation, API security review, or real driver payout integration is performed.
