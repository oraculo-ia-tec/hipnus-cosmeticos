import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend"))

from frontend.lib.user_db import autenticar_parceiro

for ident in ("helialdalili@yahoo.com.br", "helialda"):
    r = autenticar_parceiro(ident, "helialda@2026")
    if r:
        print(f"[OK] login por '{ident}' -> nome={r['nome']}, role={r['role']}")
    else:
        print(f"[FAIL] login por '{ident}' falhou")
