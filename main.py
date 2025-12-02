from pathlib import Path
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from decrypt_seed import decrypt_seed, load_private_key_from_pem
from totp_utils import generate_totp_code, verify_totp_code

app = FastAPI()

# Path where decrypted seed will be stored INSIDE the container
SEED_FILE_PATH = Path("/data/seed.txt")


# ---------- Request models ----------

class DecryptRequest(BaseModel):
    encrypted_seed: str


class VerifyRequest(BaseModel):
    code: str


# ---------- Endpoint 1: POST /decrypt-seed ----------

@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(req: DecryptRequest):
    """
    Decrypt base64 encrypted seed and store hex seed at /data/seed.txt
    """
    try:
        # 1. Load student private key
        private_key = load_private_key_from_pem("student_private.pem")

        # 2. Decrypt using the function from decrypt_seed.py
        hex_seed = decrypt_seed(req.encrypted_seed, private_key)

        # 3. Ensure /data directory exists
        SEED_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 4. Save hex seed to /data/seed.txt
        SEED_FILE_PATH.write_text(hex_seed, encoding="utf-8")

        # 5. Return success
        return {"status": "ok"}

    except Exception:
        # On ANY error, match spec: 500 with {"error": "Decryption failed"}
        return JSONResponse(
            status_code=500,
            content={"error": "Decryption failed"},
        )


# ---------- Endpoint 2: GET /generate-2fa ----------

@app.get("/generate-2fa")
async def generate_2fa_endpoint():
    """
    Generate current TOTP code and remaining validity.
    """
    # 1. Check if /data/seed.txt exists
    if not SEED_FILE_PATH.exists():
        return JSONResponse(
            status_code=500,
            content={"error": "Seed not decrypted yet"},
        )

    try:
        # 2. Read hex seed from file
        hex_seed = SEED_FILE_PATH.read_text(encoding="utf-8").strip()

        # 3. Generate TOTP code
        code = generate_totp_code(hex_seed)

        # 4. Calculate remaining seconds in current 30-second period (0–29)
        now = int(time.time())
        valid_for = 29 - (now % 30)
        if valid_for < 0:
            valid_for = 0

        # 5. Return code and valid_for
        return {"code": code, "valid_for": valid_for}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "Seed not decrypted yet"},
        )


# ---------- Endpoint 3: POST /verify-2fa ----------

@app.post("/verify-2fa")
async def verify_2fa_endpoint(req: VerifyRequest):
    """
    Verify a 6-digit TOTP code with ±1 period tolerance.
    """
    # 1. Validate code is provided
    code = (req.code or "").strip()
    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing code"},
        )

    # 2. Check if /data/seed.txt exists
    if not SEED_FILE_PATH.exists():
        return JSONResponse(
            status_code=500,
            content={"error": "Seed not decrypted yet"},
        )

    try:
        # 3. Read hex seed from file
        hex_seed = SEED_FILE_PATH.read_text(encoding="utf-8").strip()

        # 4. Verify code with ±1 period tolerance
        is_valid = verify_totp_code(hex_seed, code, valid_window=1)

        # 5. Return {"valid": true/false}
        return {"valid": is_valid}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "Seed not decrypted yet"},
        )
