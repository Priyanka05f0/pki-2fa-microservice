import base64
import hashlib
from typing import Optional

import pyotp


def _hex_seed_to_base32(hex_seed: str) -> str:
    """
    Helper: convert 64-character hex seed to base32 string.
    """
    hex_seed = hex_seed.strip().lower()

    if len(hex_seed) != 64:
        raise ValueError(f"hex_seed must be 64 characters, got {len(hex_seed)}")

    # Make sure it's valid hex
    try:
        seed_bytes = bytes.fromhex(hex_seed)
    except ValueError as e:
        raise ValueError(f"hex_seed is not valid hexadecimal: {e}")

    # Convert bytes to base32 (returns bytes), then decode to str
    base32_seed = base64.b32encode(seed_bytes).decode("utf-8")

    # Most TOTP libs accept either padded or unpadded base32; pyotp handles padding.
    return base32_seed


def generate_totp_code(hex_seed: str) -> str:
    """
    Generate current TOTP code from hex seed.

    Args:
        hex_seed: 64-character hex string

    Returns:
        6-digit TOTP code as string (e.g. "123456")
    """
    # 1. Convert hex seed to base32 (via bytes)
    base32_seed = _hex_seed_to_base32(hex_seed)

    # 2. Create TOTP object (SHA-1, 30 sec period, 6 digits by default)
    totp = pyotp.TOTP(
        base32_seed,
        digits=6,
        interval=30,
        digest=hashlib.sha1,  # explicitly specify SHA-1
    )

    # 3. Generate current code
    code = totp.now()  # returns string like "123456"

    # 4. Return the code
    return code


def verify_totp_code(hex_seed: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify TOTP code with time window tolerance.

    Args:
        hex_seed: 64-character hex seed string
        code: 6-digit code to verify (string)
        valid_window: number of periods before/after to accept (default 1 = ±30s)

    Returns:
        True if code is valid, False otherwise.
    """
    # Basic sanity cleanup
    code = code.strip()

    if not (code.isdigit() and len(code) == 6):
        # Invalid format immediately fails
        return False

    base32_seed = _hex_seed_to_base32(hex_seed)

    totp = pyotp.TOTP(
        base32_seed,
        digits=6,
        interval=30,
        digest=hashlib.sha1,
    )

    # valid_window=1 means: accept current period ±1 step (±30s)
    return totp.verify(code, valid_window=valid_window)
