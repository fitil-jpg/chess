"""Bootstrap sys.path to include vendored third-party packages."""
import sys
from pathlib import Path

vendor_root = Path(__file__).resolve().parent

# Ensure the vendor root is importable
if str(vendor_root) not in sys.path:
    sys.path.insert(0, str(vendor_root))

# Ensure the vendored ``chess`` package has highest priority
chess_vendor = vendor_root / "chess"
if chess_vendor.exists():
    sys.path.insert(0, str(chess_vendor))

# Append wheel files or package directories to ``sys.path``
for path in vendor_root.iterdir():
    if path in {chess_vendor, vendor_root / "setup_path.py"}:
        continue
    if path.suffix == ".whl" or path.is_dir():
        sys.path.insert(0, str(path))
