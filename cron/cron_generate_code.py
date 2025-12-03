#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# --- Make imports robust: ensure repo root is on sys.path ---
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from totp_utils import generate_totp_code

# Paths used inside container; local tests will fall back to repo paths
SEED_PATH = Path("/data/seed.txt")
LOG_PATH = Path("/cron/last_code.txt")

# Fallbacks for local dev (when /data or /cron aren't available)
if not SEED_PATH.exists():
    local_seed = Path(__file__).resolve().parents[1] / "data" / "seed.txt"
    if local_seed.exists():
        SEED_PATH = local_seed

if not LOG_PATH.parent.exists():
    # fallback local logs folder
    local_logs = Path(__file__).resolve().parents[1] / "logs"
    LOG_PATH = local_logs / "last_code.txt"

def main():
    if not SEED_PATH.exists():
        # nothing to do (seed not present)
        return

    hex_seed = SEED_PATH.read_text(encoding="utf-8").strip()
    if not hex_seed:
        return

    code = generate_totp_code(hex_seed)

    # Ensure directory exists
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    timestamp = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    line = f"{timestamp} - 2FA Code: {code}\n"

    # Append (do NOT overwrite) so cron logs accumulate
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)

if __name__ == "__main__":
    main()
