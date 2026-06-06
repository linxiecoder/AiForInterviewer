"""Application tests path bootstrap."""

from pathlib import Path
import sys

API_SRC = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))
