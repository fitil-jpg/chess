import sys
from pathlib import Path

# Directory containing vendored third-party packages.
VENDOR_DIR = Path(__file__).resolve().parent

# Ensure the vendor directory itself has import precedence so packages like
# ``chess`` can be imported directly from ``vendors/``.
sys.path.insert(0, str(VENDOR_DIR))

# Add wheel or archive files contained within the vendor directory.
for entry in VENDOR_DIR.iterdir():
    if entry.name == "setup_path.py":
        continue
    if entry.suffix in {".whl", ".zip"} or entry.name.endswith((".tar.gz", ".tar")):
        sys.path.insert(0, str(entry))
