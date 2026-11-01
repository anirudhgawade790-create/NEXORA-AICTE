from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app

app.frontend(
    "/",
    directory=str(Path(__file__).resolve().parent / "frontend" / "dist"),
    fallback="index.html",
)
