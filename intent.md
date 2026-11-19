# Intent GPS billing accuracy quest

**Context.** All data in this repository are synthetic. There are no MUST records, live device locations, or credentials. The exercise measures fairness of the kilometres on which fictional advertisers are billed and fictional drivers are paid. For each driver and local day (UTC+9), count only movement within the campaign polygon; reject positions over 100 m from the road and speed jumps above 150 km/h; count at most one observation per driver/timestamp; sort events by their actual UTC timestamp rather than ingest order.

## Three problems found and ranked

| Rank | Data/calculation defect | Advertiser effect | Driver effect | Why this ranking |
|---|---|---|---|---|
| 1 (solve) | Two observations share a driver and UTC timestamp but their slightly different positions both contribute segments | Pays for movement that did not occur | Artificial kilometres can later be clawed back and undermine trust in the payout | **Demonstrated** 2.3284 km overcount in six driver-days; invisible if only outliers are inspected |
| 2 (not fixed) | Off-road drift and implausible jumps | Pays for fictitious travel if not rejected | Reports can spike or be arbitrarily discounted | Generated 18 off-road and 12 speed-spike faults; an existing filter handles these in this scoped reference |
| 3 (not fixed) | Grouping by UTC date or file arrival order instead of UTC+9 event date/time | Misallocates campaign-day charges | Misallocates daily earnings and disputes | Data deliberately contains shuffled arrivals and records near the UTC+9 day cut; reference already uses UTC+9 and event time |

**Selection.** Solve the *duplicate-timestamp billing defect* only. The old reference already sorts by event time, rejects the synthetic noise cases and uses the zone/timezone. Its single deliberate defect is failing to select one observation per (driver_id, timestamp_utc) **before** integrating path length.

## Numeric acceptance criteria specified before implementation of the correction

These targets are calculated by the independent clean-track synthetic generator, before injecting duplicates/noise, and stored in `data/oracle.json`. A 0.002 km tolerance allows rounding when coordinates are serialized to 9 decimal places.

| Driver | Local day (UTC+9) | Required billable km |
|---|---|---:|
| SYNTH-A | 2026-11-16 | 15.313000 |
| SYNTH-A | 2026-11-17 | 15.539000 |
| SYNTH-B | 2026-11-16 | 15.467000 |
| SYNTH-B | 2026-11-17 | 15.693000 |
| SYNTH-C | 2026-11-16 | 15.621000 |
| SYNTH-C | 2026-11-17 | 15.847000 |

Additional measurable acceptance:

- 2,616 input pings = 2,520 unique clean records + 66 duplicate-timestamp rows + 30 noise rows.
- **100% (30/30) injected noise pings excluded** (18/18 off-road and 12/12 speed spikes); noise filtering is reused unchanged by old and fixed calculations.
- **Zero duplicate driver+timestamp pairs counted** after the fix, with exactly 66 duplicate rows removed; old calculation removes zero.
- All 6 corrected driver-days match the independent oracle within 0.002 km; the old version must fail on at least one driver-day (observed: all six).
- No cross-session distance for gaps over 20 seconds; movement within the campaign zone is clipped to the polygon, not awarded merely because one endpoint is inside.

## Boundary and scope

Four-hour ceiling: one Python checker, one corrected reference engine, four regression/behaviour tests, one synthetic dataset, and direct reproducibility evidence. **No map, dashboard, production integration, fraud classification, real map matching, or live location data.** Interpolation for a segment that crosses local midnight, on-road speed spikes whose neighbours create ambiguous trajectories, ambiguous duplicate ingestion provenance, and gaps beyond 20 seconds remain unaddressed production edge cases. The generator has no moving segment crossing local midnight (sessions stop at 23:59:50); a separate test checks the UTC/local reporting cutoff.
