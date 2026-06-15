"""
start_servers.py — HIPNUS COSMÉTICOS
=====================================
Inicia todo o ambiente local com um único comando:

  1. Valida o ambiente virtual e dependências instaladas.
  2. Carrega variáveis de ambiente do arquivo .env (se existir).
  3. Executa o seed do catálogo (scripts/seed_catalog.py) se o banco
     ainda não existir.
  4. Sobe os dois servidores em paralelo:
       • Backend  → uvicorn app.main:app --reload   (http://localhost:8000)
       • Frontend → streamlit run frontend/Home.py  (http://localhost:8501)

Uso:
    python start_servers.py

    Flags opcionais:
      --no-seed     Pula o seed do catálogo.
      --no-backend  Sobe apenas o Streamlit (modo Streamlit Cloud local).

Encerramento:
    Pressione Ctrl+C para derrubar ambos os processos simultaneamente.

Pré-requisitos:
    pip install -r requirements.txt
    cp .env.example .env   # preencha ASAAS_API_KEY etc.
"""

import subprocess
import sys
import signal
import os
import time
import threading
import argparse
from pathlib import Path

# ─── Constantes de cor ANSI ───────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
GRAY    = "\033[90m"

# Linhas separadoras pré-computadas (evita backslash dentro de f-string — Python 3.11)
LINE_DOUBLE = "\u2550" * 57
LINE_SINGLE = "\u2500" * 57

# ─── Raiz do projeto ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent

# ─── Definição dos servidores ─────────────────────────────────────────────────
SERVERS = [
    {
        "name": "BACKEND  (FastAPI)",
        "color": CYAN,
        "cmd": [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
        ],
    },
    {
        "name": "FRONTEND (Streamlit)",
        "color": MAGENTA,
        "cmd": [
            sys.executable, "-m", "streamlit",
            "run", "frontend/Home.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
        ],
    },
]

# ─── Estado global ────────────────────────────────────────────────────────────
processes: list = []


# ─── Helpers de output ────────────────────────────────────────────────────────
def log(msg, color=GREEN):
    print(color + BOLD + "[HIPNUS]" + RESET + " " + msg)


def prefix(name, color):
    return color + BOLD + "[" + name + "]" + RESET + " "


def stream_output(proc, name, color):
    """Lê stdout do processo linha a linha e imprime com prefixo colorido."""
    for line in iter(proc.stdout.readline, b""):
        print(prefix(name, color) + line.decode("utf-8", errors="replace"), end="")
    proc.stdout.close()


def stream_errors(proc, name, color):
    """Lê stderr do processo linha a linha e imprime com prefixo colorido."""
    for line in iter(proc.stderr.readline, b""):
        decoded = line.decode("utf-8", errors="replace")
        cor = RED if ("error" in decoded.lower() or "exception" in decoded.lower()) else color
        print(prefix(name, cor) + decoded, end="")
    proc.stderr.close()


# ─── Pré-checagens ────────────────────────────────────────────────────────────
def check_venv():
    """Avisa se não estiver rodando dentro de um ambiente virtual."""
    in_venv = (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )
    if not in_venv:
        print(YELLOW + BOLD + "[AVISO]" + RESET + " Você não está dentro de um venv.")
        print(GRAY + "         Ative com: source .venv/bin/activate" + RESET + "\n")


def check_dependencies():
    """Verifica se as dependências críticas estão instaladas."""
    deps = ["fastapi", "uvicorn", "streamlit", "sqlalchemy", "httpx"]
    faltando = []
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            faltando.append(dep)
    if faltando:
        print(RED + BOLD + "[ERRO]" + RESET + " Dependências não instaladas: " + ", ".join(faltando))
        print(GRAY + "       Execute: pip install -r requirements.txt" + RESET)
        sys.exit(1)


def load_dotenv():
    """Carrega o .env manualmente sem dependência extra."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        print(YELLOW + BOLD + "[AVISO]" + RESET + " Arquivo .env não encontrado.")
        print(GRAY + "         Copie o exemplo: cp .env.example .env" + RESET + "\n")
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    log(".env carregado.", GRAY)


def run_seed():
    """
    Executa o seed do catálogo se o banco SQLite ainda não existir.
    Usa o arquivo data/hipnus.db como flag de controle.
    """
    db_path = ROOT / "data" / "hipnus.db"
    if db_path.exists():
        log("Banco já existente — seed ignorado.", GRAY)
        return
    log("Executando seed do catálogo Hipnus...", YELLOW)
    result = subprocess.run(
        [sys.executable, "-m", "scripts.seed_catalog"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        log("Seed concluído com sucesso.", GREEN)
    else:
        print(RED + BOLD + "[ERRO no seed]" + RESET + "\n" + result.stderr)
        print(YELLOW + "Continuando sem seed — a API criará as tabelas no startup." + RESET + "\n")


# ─── Encerramento ─────────────────────────────────────────────────────────────
def shutdown(signum=None, frame=None):
    """Encerra todos os processos filhos com segurança."""
    print("\n" + YELLOW + BOLD + "[HIPNUS] Encerrando servidores..." + RESET)
    for proc in processes:
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass
    deadline = time.time() + 5
    for proc in processes:
        try:
            while proc.poll() is None and time.time() < deadline:
                time.sleep(0.1)
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass
    print(RED + BOLD + "[HIPNUS] Todos os servidores encerrados." + RESET + "\n")
    sys.exit(0)


# ─── Lógica principal ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="HIPNUS COSMETICOS - Starter")
    parser.add_argument("--no-seed",    action="store_true", help="Pula o seed do catálogo")
    parser.add_argument("--no-backend", action="store_true", help="Sobe apenas o Streamlit")
    args = parser.parse_args()

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("\n" + GREEN + BOLD + LINE_DOUBLE)
    print("  HIPNUS COSMÉTICOS — Iniciando ambiente local")
    print(LINE_DOUBLE + RESET + "\n")

    # 1. Pré-checagens
    check_venv()
    check_dependencies()

    # 2. Carrega .env
    load_dotenv()

    # 3. Seed
    if not args.no_seed:
        run_seed()

    # 4. Sobe servidores
    servidores_ativos = [
        s for s in SERVERS
        if not (args.no_backend and "FastAPI" in s["name"])
    ]

    for server in servidores_ativos:
        cmd_str = " ".join(server["cmd"])
        print("  " + server["color"] + BOLD + "\u25b6  " + server["name"] + RESET)
        print("  " + GRAY + "   " + cmd_str + RESET + "\n")

        proc = subprocess.Popen(
            server["cmd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(ROOT),
        )
        processes.append(proc)

        threading.Thread(
            target=stream_output,
            args=(proc, server["name"], server["color"]),
            daemon=True,
        ).start()
        threading.Thread(
            target=stream_errors,
            args=(proc, server["name"], server["color"]),
            daemon=True,
        ).start()

    print("\n" + GREEN + BOLD + LINE_SINGLE)
    if not args.no_backend:
        print("  API FastAPI  \u2192  http://localhost:8000")
        print("  Swagger Docs \u2192  http://localhost:8000/docs")
    print("  Frontend     \u2192  http://localhost:8501")
    print("  Checkout     \u2192  http://localhost:8501  (pág. Checkout)")
    print(LINE_SINGLE + RESET)
    print(YELLOW + "  Ctrl+C para encerrar todos os servidores." + RESET + "\n")

    # 5. Loop de monitoramento
    try:
        while True:
            for i, proc in enumerate(processes):
                if proc.poll() is not None:
                    name = servidores_ativos[i]["name"]
                    code = proc.returncode
                    print(
                        RED + BOLD + "[HIPNUS] ATEN\u00c7\u00c3O: " + name +
                        " encerrou inesperadamente (c\u00f3digo " + str(code) + ")." + RESET
                    )
                    print(GRAY + "  Reinicie com: python start_servers.py" + RESET)
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
