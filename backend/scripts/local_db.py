"""Run a local PostgreSQL server for development, with no Docker or installer needed.

It uses the PostgreSQL binaries bundled with the `pgserver` dev dependency and keeps
its data in backend/.localdb/ (git-ignored).

    uv run python scripts/local_db.py start    # first run creates the database
    uv run python scripts/local_db.py status
    uv run python scripts/local_db.py psql     # open an SQL shell
    uv run python scripts/local_db.py stop

Connection URL (already the default in .env.example):
    postgresql://postgres:postgres@localhost:5433/lead_agent
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pgserver

BACKEND_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = BACKEND_DIR / ".localdb"
DATA_DIR = STATE_DIR / "data"
LOG_FILE = STATE_DIR / "postgres.log"
BIN_DIR = Path(pgserver.__file__).parent / "pginstall" / "bin"

PORT = 5433
USER = "postgres"
# Development only: the server accepts connections from this computer only.
PASSWORD = "postgres"  # noqa: S105
DATABASE = "lead_agent"
URL = f"postgresql://{USER}:{PASSWORD}@localhost:{PORT}/{DATABASE}"


def _bin(name: str) -> str:
    return str(BIN_DIR / name)


def _client_args() -> list[str]:
    return ["-h", "localhost", "-p", str(PORT), "-U", USER]


def _client_env() -> dict[str, str]:
    return {**os.environ, "PGPASSWORD": PASSWORD}


def is_running() -> bool:
    if not DATA_DIR.exists():
        return False
    result = subprocess.run([_bin("pg_ctl"), "-D", str(DATA_DIR), "status"], capture_output=True)
    return result.returncode == 0


def _initialize() -> None:
    print(f"Creating a new database cluster in {DATA_DIR} ...", flush=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as pwfile:
        pwfile.write(PASSWORD)
    try:
        subprocess.run(
            [
                _bin("initdb"),
                "-D", str(DATA_DIR),
                "-U", USER,
                "--auth=scram-sha-256",
                f"--pwfile={pwfile.name}",
                "--encoding=UTF8",
            ],
            check=True,
        )  # fmt: skip
    finally:
        os.unlink(pwfile.name)


def _ensure_database() -> None:
    exists = subprocess.run(
        [_bin("psql"), *_client_args(), "-d", "postgres", "-tAc",
         f"SELECT 1 FROM pg_database WHERE datname = '{DATABASE}'"],  # noqa: S608 (constant)
        env=_client_env(), capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip
    if exists != "1":
        subprocess.run([_bin("createdb"), *_client_args(), DATABASE], env=_client_env(), check=True)
        print(f"Created database '{DATABASE}'.")


def start() -> None:
    if not (DATA_DIR / "PG_VERSION").exists():
        _initialize()
    if is_running():
        print("PostgreSQL is already running.")
    else:
        subprocess.run(
            [
                _bin("pg_ctl"),
                "-D", str(DATA_DIR),
                "-l", str(LOG_FILE),
                "-o", f"-p {PORT} -c listen_addresses=localhost",
                "-w",
                "start",
            ],
            check=True,
        )  # fmt: skip
    _ensure_database()
    print(f"\nPostgreSQL is ready at:\n  {URL}")


def stop() -> None:
    if not is_running():
        print("PostgreSQL is not running.")
        return
    subprocess.run([_bin("pg_ctl"), "-D", str(DATA_DIR), "-m", "fast", "stop"], check=True)


def status() -> None:
    print(f"running at {URL}" if is_running() else "stopped")


def psql() -> None:
    subprocess.run([_bin("psql"), *_client_args(), "-d", DATABASE], env=_client_env())


COMMANDS = {"start": start, "stop": stop, "status": status, "psql": psql}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
