"""Export the frontend contract without starting a server or connecting to the DB."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402

if __name__ == "__main__":
    destination = PROJECT_ROOT / "frontend" / "openapi.json"
    destination.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported OpenAPI to {destination.relative_to(PROJECT_ROOT)}")
