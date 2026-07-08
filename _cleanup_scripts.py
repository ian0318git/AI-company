"""Clean up accumulated temporary working scripts from prior cycles."""
import os
import glob

targets = []
# Cycle 13 files
targets.extend(glob.glob("_cycle13_*.py"))
# Cycle 67 files
targets.extend(glob.glob("_cycle67_*.py"))
# Cycle 68 files
targets.extend(glob.glob("_cycle68_*.py"))
# Other temp scripts
for f in ["_check_schema.py", "_run_classifier.py", "_check_review_schema.py"]:
    if os.path.exists(f):
        targets.append(f)

removed = 0
for f in sorted(targets):
    # Don't remove the cycle70 script
    if "cycle70" in f:
        continue
    os.remove(f)
    print(f"  Removed: {f}")
    removed += 1

print(f"Cleaned up {removed} temporary files.")
