"""Launch and supervise a real, separately installed mining executable.

This module does not mine by itself. It starts the exact external miner configured
by the operator, without a shell, and derives share counters only from its output.
It never estimates earnings or claims a Binance deposit.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_process: subprocess.Popen[str] | None = None
_reader: threading.Thread | None = None
_started_at: float | None = None
_output: deque[str] = deque(maxlen=120)
_accepted = 0
_rejected = 0
_last_error: str | None = None


def _configuration(env: dict[str, str] | None = None) -> tuple[str, list[str]]:
    values = os.environ if env is None else env
    executable = values.get("GENESE_MINER_EXECUTABLE", "").strip()
    raw_args = values.get("GENESE_MINER_ARGS_JSON", "").strip()
    if not executable:
        raise ValueError("Configure GENESE_MINER_EXECUTABLE com o caminho do minerador real instalado.")
    resolved = shutil.which(executable) if not Path(executable).is_absolute() else executable
    if not resolved:
        raise ValueError("Executável do minerador não encontrado no sistema.")
    path = Path(resolved)
    if not path.is_file():
        raise ValueError("GENESE_MINER_EXECUTABLE não aponta para um arquivo.")
    if os.name != "nt" and not os.access(path, os.X_OK):
        raise ValueError("O arquivo do minerador não tem permissão de execução.")
    if not raw_args:
        raise ValueError("Configure GENESE_MINER_ARGS_JSON como uma lista JSON de argumentos do minerador.")
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        raise ValueError("GENESE_MINER_ARGS_JSON deve ser uma lista JSON válida.") from exc
    if not isinstance(args, list) or not all(isinstance(item, str) and "\x00" not in item for item in args):
        raise ValueError("Os argumentos devem ser uma lista JSON composta apenas por textos.")
    if not args:
        raise ValueError("Informe os argumentos necessários para conectar o minerador à pool.")
    return str(path.resolve()), args


def _read_output(proc: subprocess.Popen[str]) -> None:
    global _accepted, _rejected, _last_error
    stream = proc.stdout
    if stream is None:
        return
    for line in stream:
        clean = line.rstrip()[:2000]
        with _lock:
            _output.append(clean)
            lowered = clean.lower()
            if re.search(r"\baccepted\b", lowered) and not re.search(r"\brejected\b", lowered):
                _accepted += 1
            if re.search(r"\brejected\b", lowered):
                _rejected += 1
            if "error" in lowered or "fatal" in lowered:
                _last_error = clean


def start_miner() -> dict[str, Any]:
    global _process, _reader, _started_at, _accepted, _rejected, _last_error
    with _lock:
        if _process is not None and _process.poll() is None:
            return status()
        executable, args = _configuration()
        _output.clear()
        _accepted = 0
        _rejected = 0
        _last_error = None
        try:
            proc = subprocess.Popen(
                [executable, *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
                close_fds=True,
            )
        except OSError as exc:
            raise RuntimeError(f"Não foi possível iniciar o minerador: {exc}") from exc
        _process = proc
        _started_at = time.time()
        _reader = threading.Thread(target=_read_output, args=(proc,), daemon=True)
        _reader.start()
        return status()


def stop_miner() -> dict[str, Any]:
    global _process
    with _lock:
        proc = _process
        if proc is None or proc.poll() is not None:
            return status()
        proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
    return status()


def status() -> dict[str, Any]:
    with _lock:
        proc = _process
        running = proc is not None and proc.poll() is None
        return {
            "configured": bool(
                os.environ.get("GENESE_MINER_EXECUTABLE", "").strip()
                and os.environ.get("GENESE_MINER_ARGS_JSON", "").strip()
            ),
            "running": running,
            "pid": proc.pid if proc is not None and running else None,
            "started_at_unix": _started_at,
            "runtime_seconds": round(time.time() - _started_at) if running and _started_at else 0,
            "accepted_shares_observed": _accepted,
            "rejected_shares_observed": _rejected,
            "last_error_line": _last_error,
            "recent_output": list(_output)[-30:],
            "earnings_confirmed": False,
            "binance_deposit_confirmed": False,
            "note": "Contadores vêm apenas do texto emitido pelo processo externo; não comprovam pagamento nem lucro.",
        }
