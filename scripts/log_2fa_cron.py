#!/usr/bin/env python3
"""
Cron script to read a hex seed and print a TOTP code with UTC timestamp.
Outputs a single line to stdout like:
2025-12-03 21:50:01 UTC - 2FA Code: 123456
"""

import time
import hmac
import hashlib
import struct
import sys
from datetime import datetime, timezone
import base64

SEED_PATH = "/data/seed.txt"
DIGITS = 6
INTERVAL = 30

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC"

def read_seed(path):
    try:
        with open(path, "r") as f:
            s = f.read().strip()
            if not s:
                raise ValueError("Seed file is empty")
            return s
    except FileNotFoundError:
        print(f"{utc_now()} - ERROR: seed file not found at {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{utc_now()} - ERROR reading seed: {e}", file=sys.stderr)
        sys.exit(1)

def seed_to_bytes(seed_str):
    seed = seed_str.strip()
    try:
        return bytes.fromhex(seed)
    except Exception:
        try:
            return base64.b32decode(seed.upper(), casefold=True)
        except Exception:
            raise ValueError("Seed is not valid hex or base32")

def generate_totp(secret_bytes, digits=6, interval=30, for_time=None):
    if for_time is None:
        for_time = int(time.time())
    counter = for_time // interval
    counter_bytes = struct.pack(">Q", counter)
    h = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code_int = struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF
    code = code_int % (10 ** digits)
    return f"{code:0{digits}d}"

def main():
    seed_str = read_seed(SEED_PATH)
    try:
        secret = seed_to_bytes(seed_str)
    except Exception as e:
        print(f"{utc_now()} - ERROR: invalid seed format: {e}", file=sys.stderr)
        sys.exit(1)

    code = generate_totp(secret, digits=DIGITS, interval=INTERVAL)
    print(f"{utc_now()} - 2FA Code: {code}")

if __name__ == "__main__":
    main()
