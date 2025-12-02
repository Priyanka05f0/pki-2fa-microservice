from pathlib import Path
from datetime import datetime, timezone
from totp_utils import generate_totp_code

SEED_PATH = Path("/data/seed.txt")
LOG_PATH = Path("/cron/last_code.txt")

def main():
    if not SEED_PATH.exists():
        return

    hex_seed = SEED_PATH.read_text(encoding="utf-8").strip()
    if not hex_seed:
        return

    code = generate_totp_code(hex_seed)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    timestamp = now_utc.strftime("%Y-%m-%d %H:%M:%S")

    line = f"{timestamp} - 2FA Code: {code}\n"
    LOG_PATH.write_text(line, encoding="utf-8")

if __name__ == "__main__":
    main()
