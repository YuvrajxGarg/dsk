"""Smoke-test a built app: run its command line scan and check the report it writes.
    python tests/smoke_app.py <path to Dsk executable>
"""
import json
import os
import subprocess
import sys
import tempfile

exe = sys.argv[1]
d = tempfile.mkdtemp()
report = os.path.join(d, "report.json")
r = subprocess.run([exe, "scan", "--only", "caches,trash", "--report", report], timeout=600)
assert os.path.isfile(report), "app wrote no report (exit %s)" % r.returncode
with open(report, encoding="utf-8") as f:
    data = json.load(f)
scan = data["scan"]
assert scan["done"], scan
assert scan["disk"]["total"] > 0 and scan["disk"]["used"] > 0, scan["disk"]
assert set(scan["sizes"]) == {"apps", "dev", "photos", "movies", "docs", "music", "system", "caches", "trash"}, scan["sizes"]
assert isinstance(data["groups"], list)
# The Claude SDK, keyring and send2trash must be bundled.
r2 = subprocess.run([exe, "selftest", os.path.join(d, "selftest.json")], timeout=120)
with open(os.path.join(d, "selftest.json"), encoding="utf-8") as f:
    st = json.load(f)
assert st["anthropic"] and st["send2trash"] and st["keyring"], st
print("smoke test passed: %s, %s used, %d groups (exit %s)" % (exe, scan["disk"]["used"], len(data["groups"]), r.returncode))
