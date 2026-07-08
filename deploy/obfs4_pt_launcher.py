#!/usr/bin/env python3
"""Minimal Tor PT supervisor so obfs4proxy can run without tor."""

from __future__ import annotations

import os
import subprocess
import sys


def _pt_exchange(proc: subprocess.Popen[str]) -> None:
    assert proc.stdin and proc.stdout
    version = proc.stdout.readline().strip()
    if not version.startswith("VERSION"):
        raise RuntimeError(f"unexpected PT greeting: {version!r}")

    proc.stdin.write("SMETHODS obfs4\n")
    proc.stdin.flush()
    while True:
        line = proc.stdout.readline().strip()
        if line == "SMETHODS DONE":
            break
        if not line.startswith("SMETHOD"):
            raise RuntimeError(f"unexpected server transport line: {line!r}")

    proc.stdin.write("ARGS\n")
    proc.stdin.flush()
    args_reply = proc.stdout.readline().strip()
    if args_reply != "ARGS-OK":
        raise RuntimeError(f"ARGS failed: {args_reply!r}")

    proc.stdin.write("SETUP\n")
    proc.stdin.flush()
    setup_reply = proc.stdout.readline().strip()
    if not setup_reply.startswith("DONE"):
        raise RuntimeError(f"SETUP failed: {setup_reply!r}")
    print(setup_reply, flush=True)


def main() -> int:
    state = os.environ.get("OBFS4_STATE", "/opt/phoenix/obfs4/state")
    bind = os.environ.get("OBFS4_BIND", "0.0.0.0")
    port = os.environ.get("OBFS4_PORT", "1080")
    target = os.environ.get("OBFS4_TARGET", "127.0.0.1:1194")
    binary = os.environ.get("OBFS4_BINARY", "obfs4proxy")

    env = os.environ.copy()
    env.update(
        {
            "TOR_PT_MANAGED_TRANSPORT_VER": "1",
            "TOR_PT_STATE_LOCATION": state,
            "TOR_PT_SERVER_TRANSPORTS": "obfs4",
            "TOR_PT_SERVER_BINDADDR": f"obfs4-{bind}:{port}",
            "TOR_PT_ORPORT": target,
        }
    )

    proc = subprocess.Popen(
        [binary, "-enableLogging", "-logLevel", os.environ.get("OBFS4_LOG_LEVEL", "INFO")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        env=env,
        text=True,
        bufsize=1,
    )
    try:
        _pt_exchange(proc)
    except Exception as exc:
        print(f"[obfs4-pt] setup failed: {exc}", file=sys.stderr)
        proc.terminate()
        return 1

    return proc.wait()


if __name__ == "__main__":
    sys.exit(main())
