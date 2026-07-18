import os
import sys
from pathlib import Path

import uvicorn

# Add the Phase 5 folder to the Python search path.
base_dir = Path(__file__).resolve().parent
phase5_candidates = [
    base_dir / "5. Project Development Phase",
    base_dir / "5.Project Development Phase",
]

for candidate in phase5_candidates:
    if candidate.exists():
        sys.path.insert(0, str(candidate))
        break
else:
    raise FileNotFoundError("Could not find the Phase 5 project directory.")

# Import FastAPI app from main.py inside Phase 5 folder.
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Run uvicorn server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
