import sys
from pathlib import Path

frontend = Path(__file__).resolve().parents[1] / "frontend"
if str(frontend) not in sys.path:
    sys.path.insert(0, str(frontend))

exec(open(frontend / "pages" / "2_✨_Linhas.py", encoding="utf-8").read())
