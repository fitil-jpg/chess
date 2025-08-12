# run_all_tests.py
import subprocess

tests = [
    "tests/test_evaluator.py",
    "tests/test_metrics.py"   # replace with your second test's filename
]

for test in tests:
    print(f"\n=== Running {test} ===")
    subprocess.run(["python", test])
