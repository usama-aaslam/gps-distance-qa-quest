"""
1. Generate labelled synthetic GPS data.
2. Prove the old engine fails the acceptance criteria.
3. Prove the corrected engine passes.
4. Run deterministic automated regression tests.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(*args):
    """Execute a command and display its complete output."""
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, end="", flush=True)

    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)

    return result.returncode

def main():
    print("=" * 65, flush=True)
    print("GPS DISTANCE ACCURACY QUEST - SYNTHETIC DATA", flush=True)
    print("=" * 65, flush=True)

    # Step 1: Generate the synthetic dataset.
    print("\nSTEP 1: Generate synthetic GPS dataset", flush=True)

    if run("generate_data.py") != 0:
        sys.exit("FAILED: Dataset generation")

    # Step 2: Demonstrate the original defect.
    print("\nSTEP 2: BEFORE FIX - OLD ENGINE", flush=True)
    print("Expected result: FAIL (duplicate distance inflation)", flush=True)

    old_exit = run("qa.py", "--mode", "old", "--verify")

    if old_exit == 0:
        sys.exit(
            "FAILED: Old behaviour unexpectedly passed. "
            "Regression verification is invalid."
        )

    print("\nCONFIRMED: Old engine failed as expected.", flush=True)

    # Step 3: Verify the corrected calculation.
    print("\nSTEP 3: AFTER FIX - CORRECTED ENGINE", flush=True)
    print("Expected result: PASS (duplicates removed)", flush=True)

    fixed_exit = run("qa.py", "--mode", "fixed", "--verify")

    if fixed_exit != 0:
        sys.exit("FAILED: Corrected engine did not pass verification")

    print("\nCONFIRMED: Corrected engine passed.", flush=True)

    # Step 4: Run automated regression tests.
    print("\nSTEP 4: Automated regression tests", flush=True)

    tests_exit = run("-m", "pytest", "-q", "tests")

    if tests_exit != 0:
        sys.exit("FAILED: Automated regression tests")

    print("\n" + "=" * 65, flush=True)
    print("FINAL RESULT: SUCCESS", flush=True)
    print("Old engine: FAIL (expected)", flush=True)
    print("Fixed engine: PASS", flush=True)
    print("Automated tests: PASS", flush=True)
    print("=" * 65, flush=True)


if __name__ == "__main__":
    main()