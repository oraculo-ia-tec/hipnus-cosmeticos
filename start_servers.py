"""
start_servers.py — HIPNUS COSMÉTICOS
=====================================
Inicia os dois servidores do projeto em paralelo com um único comando:

  - Backend  → uvicorn app.main:app --reload   (http://localhost:8000)
  - Frontend → streamlit run frontend/Home.py  (http://localhost:8501)

Uso:
    python start_servers.py

Encerramento:
    Pressione Ctrl+C para derrubar ambos os processos simultaneamente.
"""

import subprocess
import sys
import signal
import os
import time
import threading

# ─── Configurações ────────────────────────────────────────────────────────────

SERVERS = [
    {
        "name": "BACKEND  (FastAPI)",
        "color": "\033[96m",   # ciano
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
        "color": "\033[95m",   # magenta
        "cmd": [
            sys.executable, "-m", "streamlit",
            "run", "frontend/Home.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
        ],
    },
]

RESET = "\033[0m"
BOLD  = "\033[1m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def prefix(name: str, color: str) -> str:
    return f"{color}{BOLD}[{name}]{RESET} "


def stream_output(proc: subprocess.Popen, name: str, color: str) -> None:
    """Lê stdout do processo linha a linha e imprime com prefixo colorido."""
    for line in iter(proc.stdout.readline, b""):
        print(prefix(name, color) + line.decode("utf-8", errors="replace"), end="")
    proc.stdout.close()


def stream_errors(proc: subprocess.Popen, name: str, color: str) -> None:
    """Lê stderr do processo linha a linha e imprime com prefixo colorido."""
    for line in iter(proc.stderr.readline, b""):
        print(prefix(name, color) + f"{RED}{line.decode('utf-8', errors='replace')}{RESET}", end="")
    proc.stderr.close()


# ─── Lógica principal ─────────────────────────────────────────────────────────

processes: list[subprocess.Popen] = []


def shutdown(signum=None, frame=None) -> None:
    """Encerra todos os processos filhos com segurança."""
    print(f"\n{YELLOW}{BOLD}[HIPNUS] Encerrando servidores...{RESET}")
    for proc in processes:
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass

    # Aguarda até 5s para encerramento limpo, depois força kill
    deadline = time.time() + 5
    for proc in processes:
        try:
            while proc.poll() is None and time.time() < deadline:
                time.sleep(0.1)
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass

    print(f"{RED}{BOLD}[HIPNUS] Todos os servidores encerrados.{RESET}\n")
    sys.exit(0)


def main() -> None:
    # Captura Ctrl+C e SIGTERM
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"\n{GREEN}{BOLD}{'═' * 55}")
    print(f"  HIPNUS COSMÉTICOS — Iniciando servidores")
    print(f"{'═' * 55}{RESET}\n")

    threads: list[threading.Thread] = []

    for server in SERVERS:
        print(f"{server['color']}{BOLD}  ▶  {server['name']}{RESET}")
        print(f"     Comando: {' '.join(server['cmd'])}\n")

        proc = subprocess.Popen(
            server["cmd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        processes.append(proc)

        # Thread para stdout
        t_out = threading.Thread(
            target=stream_output,
            args=(proc, server["name"], server["color"]),
            daemon=True,
        )
        # Thread para stderr
        t_err = threading.Thread(
            target=stream_errors,
            args=(proc, server["name"], server["color"]),
            daemon=True,
        )
        t_out.start()
        t_err.start()
        threads.extend([t_out, t_err])

    print(f"{GREEN}{BOLD}{'─' * 55}")
    print(f"  API FastAPI  →  http://localhost:8000")
    print(f"  Docs Swagger →  http://localhost:8000/docs")
    print(f"  Frontend     →  http://localhost:8501")
    print(f"{'─' * 55}{RESET}")
    print(f"{YELLOW}  Pressione Ctrl+C para encerrar ambos os servidores.{RESET}\n")

    # Mantém o processo principal vivo enquanto os filhos rodam
    try:
        while True:
            # Verifica se algum processo morreu inesperadamente
            for i, proc in enumerate(processes):
                if proc.poll() is not None:
                    name = SERVERS[i]["name"]
                    print(f"{RED}{BOLD}[HIPNUS] ATENÇÃO: {name} encerrou inesperadamente (código {proc.returncode}).{RESET}")
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
