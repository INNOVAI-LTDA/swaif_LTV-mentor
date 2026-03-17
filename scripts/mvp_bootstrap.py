#!/usr/bin/env python
"""Bootstrap local para subir backend e frontend opcional do MVP."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
LOG_DIR = ROOT_DIR / ".logs" / "mvp-bootstrap"

IGNORED_DISCOVERY_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".vendor",
    ".deps",
    ".pytest_cache",
    ".hypothesis",
    ".logs",
    "backend",
    "docs",
    "origin",
    "dist",
    "build",
    "coverage",
    "test_tmp",
    "test_tmp_bootstrap",
}

IGNORED_DISCOVERY_PREFIXES = ("test_tmp", ".tmp", ".localtmp")


def print_info(message: str) -> None:
    print(f"[INFO] {message}")


def print_ok(message: str) -> None:
    print(f"[ OK ] {message}")


def print_err(message: str) -> None:
    print(f"[ERR ] {message}")


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value < 1 or value > 65535:
        return default
    return value


def process_name_by_pid(pid: int) -> str:
    if pid <= 0:
        return "unknown"

    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
            output = (result.stdout or "").strip()
            if not output or output.startswith("INFO:"):
                return "unknown"
            parts = [part.strip('"') for part in output.split(",")]
            if parts:
                return parts[0] or "unknown"
            return "unknown"

        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True,
            text=True,
            check=False,
        )
        name = (result.stdout or "").strip()
        return name or "unknown"
    except OSError:
        return "unknown"


def pids_on_port_windows(port: int) -> list[int]:
    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = (result.stdout or "").splitlines()
    pids: set[int] = set()
    for line in lines:
        text = line.strip()
        if not text:
            continue
        upper = text.upper()
        if not upper.startswith("TCP"):
            continue
        if "LISTENING" not in upper and "ESCUTANDO" not in upper:
            continue
        parts = text.split()
        if len(parts) < 5:
            continue
        local_addr = parts[1]
        pid_raw = parts[-1]
        if not local_addr.endswith(f":{port}"):
            continue
        try:
            pids.add(int(pid_raw))
        except ValueError:
            continue
    return sorted(pid for pid in pids if pid > 0)


def pids_on_port_posix(port: int) -> list[int]:
    pids: set[int] = set()

    if shutil.which("lsof"):
        result = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            capture_output=True,
            text=True,
            check=False,
        )
        for raw in (result.stdout or "").splitlines():
            text = raw.strip()
            if not text:
                continue
            try:
                pids.add(int(text))
            except ValueError:
                continue

    if not pids and shutil.which("ss"):
        result = subprocess.run(
            ["ss", "-ltnp"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in (result.stdout or "").splitlines():
            if f":{port} " not in line and not line.strip().endswith(f":{port}"):
                continue
            marker = "pid="
            idx = line.find(marker)
            if idx < 0:
                continue
            tail = line[idx + len(marker) :]
            pid_text = ""
            for ch in tail:
                if ch.isdigit():
                    pid_text += ch
                else:
                    break
            if not pid_text:
                continue
            try:
                pids.add(int(pid_text))
            except ValueError:
                continue

    return sorted(pid for pid in pids if pid > 0)


def pids_on_port(port: int) -> list[int]:
    if os.name == "nt":
        return pids_on_port_windows(port)
    return pids_on_port_posix(port)


def describe_port_usage(port: int) -> list[tuple[int, str]]:
    return [(pid, process_name_by_pid(pid)) for pid in pids_on_port(port)]


def kill_pid(pid: int) -> bool:
    if pid <= 0:
        return False

    try:
        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
            # Fallback para ambientes com restricao de taskkill.
            try:
                os.kill(pid, signal.SIGTERM)
                return True
            except OSError:
                return False

        os.kill(pid, signal.SIGTERM)
        return True
    except OSError:
        return False


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((host, port)) == 0


def wait_until_port_open(host: str, port: int, timeout_sec: float, process: subprocess.Popen[str]) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        if is_port_open(host, port):
            return True
        time.sleep(0.25)
    return False


def wait_until_backend_healthy(
    host: str,
    port: int,
    health_path: str,
    timeout_sec: float,
    process: subprocess.Popen[str],
) -> bool:
    if not health_path.startswith("/"):
        health_path = f"/{health_path}"
    url = f"http://{host}:{port}{health_path}"
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen(url, timeout=0.9) as response:
                if response.status == 200:
                    return True
        except URLError:
            pass
        except OSError:
            pass
        time.sleep(0.3)
    return False


def ensure_ports_available(
    targets: Iterable[tuple[str, int]],
    auto_kill: bool,
) -> None:
    for label, port in targets:
        usage = describe_port_usage(port)
        if not usage:
            print_ok(f"Porta {port} ({label}) livre.")
            continue

        joined = ", ".join([f"PID {pid} ({name})" for pid, name in usage])
        print_info(f"Porta {port} ({label}) em uso: {joined}")
        if not auto_kill:
            raise RuntimeError(f"Porta {port} ocupada e --no-kill ativo.")

        for pid, name in usage:
            print_info(f"Encerrando PID {pid} ({name}) da porta {port}...")
            if not kill_pid(pid):
                raise RuntimeError(f"Nao foi possivel encerrar PID {pid} na porta {port}.")

        time.sleep(0.6)
        if describe_port_usage(port):
            raise RuntimeError(f"Porta {port} continua ocupada apos tentativa de encerramento.")
        print_ok(f"Porta {port} liberada.")


def should_ignore_discovery_dir(name: str) -> bool:
    lower = name.lower()
    if lower in IGNORED_DISCOVERY_DIRS:
        return True
    return any(lower.startswith(prefix) for prefix in IGNORED_DISCOVERY_PREFIXES)


def iter_package_json_files(root_dir: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root_dir):
        dirs[:] = [name for name in dirs if not should_ignore_discovery_dir(name)]
        if "package.json" in files:
            yield Path(current) / "package.json"


def read_dev_script(package_json: Path, strict: bool) -> str | None:
    try:
        raw = package_json.read_text(encoding="utf-8")
    except OSError:
        if strict:
            raise RuntimeError(f"Nao foi possivel ler {package_json}.")
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        if strict:
            raise RuntimeError(f"package.json invalido em {package_json}.")
        return None

    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        if strict:
            raise RuntimeError(f"Campo scripts ausente ou invalido em {package_json}.")
        return None

    dev_script = scripts.get("dev")
    if not isinstance(dev_script, str) or not dev_script.strip():
        if strict:
            raise RuntimeError(f"Script 'dev' ausente em {package_json}.")
        return None

    return dev_script.strip()


def discover_frontend_dir() -> tuple[Path, str] | None:
    candidates: list[tuple[Path, str]] = []
    for package_json in iter_package_json_files(ROOT_DIR):
        dev_script = read_dev_script(package_json, strict=False)
        if not dev_script:
            continue
        candidates.append((package_json.parent, dev_script))

    if not candidates:
        return None

    candidates.sort(key=lambda item: str(item[0]).lower())
    if len(candidates) == 1:
        return candidates[0]

    listed = ", ".join([str(path) for path, _ in candidates[:4]])
    suffix = " ..." if len(candidates) > 4 else ""
    raise RuntimeError(
        "Multiplos frontends candidatos encontrados. "
        f"Informe --frontend-dir. Candidatos: {listed}{suffix}"
    )


def resolve_frontend_dir(frontend_dir_arg: str) -> tuple[Path, str] | None:
    if frontend_dir_arg:
        frontend_dir = Path(frontend_dir_arg).expanduser()
        if not frontend_dir.is_absolute():
            frontend_dir = ROOT_DIR / frontend_dir
        frontend_dir = frontend_dir.resolve()
        if not frontend_dir.exists() or not frontend_dir.is_dir():
            raise RuntimeError(f"Diretorio de frontend invalido: {frontend_dir}")
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            raise RuntimeError(f"package.json nao encontrado em {frontend_dir}")
        dev_script = read_dev_script(package_json, strict=True)
        if not dev_script:
            raise RuntimeError(f"Script 'dev' ausente em {package_json}")
        return frontend_dir, dev_script

    return discover_frontend_dir()


def detect_frontend_command(frontend_port: int, dev_script: str) -> str:
    if not dev_script:
        raise RuntimeError("Script 'dev' vazio para o frontend.")

    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    if "vite" in dev_script.lower():
        return f'{npm_cmd} run dev -- --host 127.0.0.1 --port {frontend_port}'
    return f"{npm_cmd} run dev"


def default_backend_command(backend_port: int) -> str:
    py = "python"
    return f'{py} -m uvicorn app.main:app --host 127.0.0.1 --port {backend_port}'


def build_env(base: dict[str, str], extra: dict[str, str]) -> dict[str, str]:
    env = dict(base)
    env.update(extra)
    return env


def start_service(
    label: str,
    command: str,
    cwd: Path,
    log_file: Path,
    env: dict[str, str],
) -> subprocess.Popen[str]:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = open(log_file, "w", encoding="utf-8")
    print_info(f"Subindo {label}...")
    print_info(f"Comando: {command}")
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        shell=True,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    setattr(process, "_log_handle", log_handle)
    return process


def stop_process(process: subprocess.Popen[str] | None, label: str) -> None:
    if process is None:
        return

    try:
        if process.poll() is None:
            print_info(f"Encerrando {label} (PID {process.pid})...")
            process.terminate()
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
    finally:
        log_handle = getattr(process, "_log_handle", None)
        if log_handle:
            log_handle.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap local do MVP (backend e frontend opcional).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--backend-port", type=int, default=env_int("BACKEND_PORT", 8000))
    parser.add_argument("--frontend-port", type=int, default=env_int("FRONTEND_PORT", 5173))
    parser.add_argument("--backend-host", default=os.getenv("BACKEND_HOST", "127.0.0.1"))
    parser.add_argument("--frontend-host", default=os.getenv("FRONTEND_HOST", "127.0.0.1"))
    parser.add_argument("--backend-health-path", default=os.getenv("BACKEND_HEALTH_PATH", "/health"))
    parser.add_argument("--startup-timeout", type=float, default=float(os.getenv("STARTUP_TIMEOUT", "25")))
    parser.add_argument("--backend-cmd", default=os.getenv("BACKEND_CMD", "").strip())
    parser.add_argument("--frontend-cmd", default=os.getenv("FRONTEND_CMD", "").strip())
    parser.add_argument(
        "--frontend-dir",
        default=os.getenv("FRONTEND_DIR", "").strip(),
        help="Diretorio do frontend com package.json e script dev (ou FRONTEND_DIR).",
    )
    parser.add_argument("--no-kill", action="store_true", help="Nao encerra processos em portas ocupadas.")
    parser.add_argument("--backend-only", action="store_true", help="Sobe apenas backend.")
    parser.add_argument("--frontend-only", action="store_true", help="Sobe apenas frontend.")
    parser.add_argument("--ports", action="store_true", help="Somente inspeciona portas e sai.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.backend_only and args.frontend_only:
        raise RuntimeError("Use apenas uma opcao entre --backend-only e --frontend-only.")

    for label, port in (("backend", args.backend_port), ("frontend", args.frontend_port)):
        if port < 1 or port > 65535:
            raise RuntimeError(f"Porta invalida para {label}: {port}")


def print_ports(args: argparse.Namespace) -> int:
    print_info("Inspecao de portas:")
    for label, port in (("backend", args.backend_port), ("frontend", args.frontend_port)):
        usage = describe_port_usage(port)
        if not usage:
            print_ok(f"{label}: porta {port} livre.")
            continue
        joined = ", ".join([f"PID {pid} ({name})" for pid, name in usage])
        print_info(f"{label}: porta {port} ocupada por {joined}.")
    return 0


def main() -> int:
    args = parse_args()
    validate_args(args)

    if args.ports:
        return print_ports(args)

    start_backend = not args.frontend_only
    start_frontend = not args.backend_only

    backend_cmd = args.backend_cmd or default_backend_command(args.backend_port)
    frontend_cmd = ""
    frontend_dir: Path | None = None
    if start_frontend:
        resolved_frontend = resolve_frontend_dir(args.frontend_dir)
        if resolved_frontend is None:
            if args.frontend_only:
                raise RuntimeError("frontend nao encontrado neste projeto")
            print_info("frontend nao encontrado neste projeto")
            print_info("iniciando apenas o backend")
            start_frontend = False
        else:
            frontend_dir, dev_script = resolved_frontend
            frontend_cmd = args.frontend_cmd or detect_frontend_command(args.frontend_port, dev_script)

    targets: list[tuple[str, int]] = []
    if start_backend:
        targets.append(("backend", args.backend_port))
    if start_frontend:
        targets.append(("frontend", args.frontend_port))

    ensure_ports_available(targets, auto_kill=not args.no_kill)

    backend_process: subprocess.Popen[str] | None = None
    frontend_process: subprocess.Popen[str] | None = None
    try:
        if start_backend:
            backend_env = build_env(os.environ, {"PYTHONPATH": os.getenv("PYTHONPATH", ".vendor")})
            backend_log = LOG_DIR / "backend.log"
            backend_process = start_service(
                "backend",
                backend_cmd,
                BACKEND_DIR,
                backend_log,
                backend_env,
            )
            if not wait_until_port_open(args.backend_host, args.backend_port, args.startup_timeout, backend_process):
                raise RuntimeError("Backend nao abriu porta dentro do timeout.")
            if not wait_until_backend_healthy(
                args.backend_host,
                args.backend_port,
                args.backend_health_path,
                args.startup_timeout,
                backend_process,
            ):
                raise RuntimeError("Backend nao respondeu healthcheck dentro do timeout.")
            print_ok(f"Backend pronto em http://{args.backend_host}:{args.backend_port}")
            print_info(f"Log backend: {LOG_DIR / 'backend.log'}")

        if start_frontend:
            frontend_env = build_env(
                os.environ,
                {
                    "API_BASE_URL": f"http://{args.backend_host}:{args.backend_port}",
                    "VITE_API_BASE_URL": f"http://{args.backend_host}:{args.backend_port}",
                },
            )
            frontend_log = LOG_DIR / "frontend.log"
            frontend_process = start_service(
                "frontend",
                frontend_cmd,
                frontend_dir if frontend_dir is not None else ROOT_DIR,
                frontend_log,
                frontend_env,
            )
            if not wait_until_port_open(args.frontend_host, args.frontend_port, args.startup_timeout, frontend_process):
                raise RuntimeError("Frontend nao abriu porta dentro do timeout.")
            print_ok(f"Frontend pronto em http://{args.frontend_host}:{args.frontend_port}")
            print_info(f"Log frontend: {LOG_DIR / 'frontend.log'}")

        print("")
        print_ok("Bootstrap concluido.")
        if start_backend:
            print_info(f"Backend URL : http://{args.backend_host}:{args.backend_port}")
        if start_frontend:
            print_info(f"Frontend URL: http://{args.frontend_host}:{args.frontend_port}")
        print_info("Pressione Ctrl+C para encerrar os servicos.")

        while True:
            if backend_process and backend_process.poll() is not None:
                raise RuntimeError("Backend encerrou inesperadamente.")
            if frontend_process and frontend_process.poll() is not None:
                raise RuntimeError("Frontend encerrou inesperadamente.")
            time.sleep(0.7)

    except KeyboardInterrupt:
        print_info("Interrupcao recebida. Encerrando...")
        return 0
    finally:
        stop_process(frontend_process, "frontend")
        stop_process(backend_process, "backend")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print_err(str(exc))
        print_err("Bootstrap encerrado com falha.")
        sys.exit(1)
    except Exception:
        print_err("Falha inesperada no bootstrap.")
        sys.exit(2)
