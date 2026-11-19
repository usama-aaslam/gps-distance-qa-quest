# Final directive repeatable AI-assisted instructions

## Task instructions given to the AI assistant

> Build a minimal, verifiable demonstration of an advertiser/driver vehicle-ad billing bug using **only fictional GPS coordinates**. Generate at least 2,000 timestamped observations from three fictional drivers over at least two UTC+9 local days; inject same-driver/same-timestamp records, off-road deviations of over 100 m, jumps over 150 km/h, and shuffled arrival order. Compute a reference distance from the clean pre-injection route separately from the faulty engine. Focus the fix only on deduplicating by `(driver_id, UTC timestamp)` before calculating distance. Reuse standard geospatial, projection, timezone, and testing libraries. Build a single CLI checker that shows row IDs and reasons, six driver-day distances before and after, a full CSV duplicate audit, and a regression that fails on the old engine and passes on the corrected engine. Package everything to run with `python run.py`; document assumptions, omissions, and checks honestly.

## Execution instructions

1. Create a clean Python virtual environment; install dependencies in `requirements.txt`.
2. Run `python run.py`. It regenerates the synthetic CSV and oracle from a fixed seed, runs the old engine with a numerical acceptance check **expected to exit 1**, runs the fixed engine **expected to exit 0**, and runs pytest.
3. Inspect `data/duplicate_audit.csv` for every duplicate and the retained timestamp-peer, `data/oracle.json` for independent targets, and the terminal report for six driver-days.
4. For a direct independent old-behaviour failure, run `python qa.py --mode old --verify` and observe exit code 1. Then run `python qa.py --mode fixed --verify` and observe exit code 0.

## Human-facing review / AI checks

- **Data generation verified:** original count is exactly 2,520, with 66 deliberate duplicated timestamps and 30 labelled noise records. The CSV records have fabricated `SYNTH-*` IDs. Reproducing the generator should give the same numbers due to the fixed seed `20261118`.
- **Oracle independence verified:** `generate_data.py` calculates reference kilometres directly from original clean, pre-injection XY segments. It does not call `qa.compute`, `qa.distances`, or the deduplication function. It saves six reference values before `qa.py` is run.
- **Old-vs-fixed verified:** `run.py` explicitly fails if the old regression unexpectedly succeeds; the old engine produces a nonzero exit with the same acceptance check that the new engine passes.
- **All injected noise verified:** `tests/test_regression.py` asserts separate counts of 18 off-road and 12 speed-spike removals, along with exactly 66 duplicate removals and zero remaining timestamp duplication.
- **Time cutoff checked:** automated test asserts 14:59:59 UTC is the prior UTC+9 day and 15:00:00 UTC is the next day.
- **Manual engineering caution:** `arrival_order` is synthetic event-ingest metadata; “first arrived wins” is a deliberately stated conflict resolution policy, not a universally safe GPS policy. In a live system, a source-quality or immutable upstream event-ID policy would need product approval.

The assistant produced code and documentation. Actual execution outputs were checked locally rather than invented. No claims of a Loom recording or external submission are made.
