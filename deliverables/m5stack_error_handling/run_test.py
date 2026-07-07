#!/usr/bin/env python3
"""Run a specific doctest test case."""
import subprocess, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
case = sys.argv[1] if len(sys.argv) > 1 else ""
args = ["./test_error_handling"]
if case:
    args.append(f"--dt-case={case}")

r = subprocess.run(args, capture_output=True, text=True)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr)
print(f"Exit: {r.returncode}", file=sys.stderr)
sys.exit(r.returncode)
