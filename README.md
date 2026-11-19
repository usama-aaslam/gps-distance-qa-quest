# Synthetic GPS distance billing duplicate timestamp defect

**Fictional case study. No real drivers, MUST data, API keys, or actual financial records.**

## Run

Python 3.10+:

```bash
python -m pip install -r requirements.txt
python run.py
```

The one-command run generates over 2,000 labelled GPS records, checks that the **old behaviour fails**, checks that the **fixed behaviour passes**, and runs automated tests. Output is also captured in `run_output.txt` from a locally verified execution.

Alternatively:

```bash
python qa.py --mode old --verify   # deliberately exits 1
python qa.py --mode fixed --verify # exits 0
python -m pytest -q tests
```

## File guide

- `intent.md`: ranked problem choice, numeric acceptance and scope
- `Final directive.md`: repeatable AI-assisted build/verification directions
- `evidence.md`: six before/after values, verification and open risks
- `generate_data.py`: deterministic synthetic generator and independent clean-track oracle
- `data/synthetic_pings.csv`: labelled shuffled GPS records, WGS84 degrees + UTC times
- `data/oracle.json`: trusted reference built without using the calculation engine
- `qa.py`: one checker with old and corrected engine modes; auto-writes `data/duplicate_audit.csv`
- `data/duplicate_audit.csv`: which duplicate row was discarded, its retained peer and why
- `tests/test_regression.py`: acceptance and boundary tests
- `run.py`: one-command demonstration wrapper
- `loom_script.md`: under-5-minute recording outline (recording not included)

## Design limits

A fictional straight road is defined in local metres near a public Tokyo-region projection centre solely to generate plausible WGS84 coordinates. Shapely clips each retained segment against a rectangular fictional campaign polygon. The distance unit is kilometres. Sessions do not include a moving segment that crosses local midnight. The CLI checker reports values and row IDs; no map or dashboard is built.
