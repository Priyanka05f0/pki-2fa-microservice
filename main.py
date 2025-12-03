from pathlib import Path
import time
import re
import os
import traceback

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from decrypt_seed import decrypt_seed, load_private_key_from_pem
from totp_utils import generate_totp_code, verify_totp_code

app = FastAPI()

# Determine seed file path:
_env_path = os.getenv("SEED_FILE_PATH")
if _env_path:
    SEED_FILE_PATH = Path(_env_path)
elif Path("/data/seed.txt").exists():
    SEED_FILE_PATH = Path("/data/seed.txt")
else:
    SEED_FILE_PATH = Path("data/seed.txt")

print("Using seed path:", SEED_FILE_PATH.resolve())
print("Seed exists:", SEED_FILE_PATH.exists())

class DecryptRequest(BaseModel):
    encrypted_seed: str

class VerifyRequest(BaseModel):
    code: str

@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(req: DecryptRequest):
    try:
        private_key = load_private_key_from_pem("student_private.pem")
        hex_seed = decrypt_seed(req.encrypted_seed, private_key)
        SEED_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SEED_FILE_PATH.write_text(hex_seed, encoding="utf-8")
        return {"status": "ok"}
    except Exception as e:
        # log the error to console for debugging
        print("[decrypt-seed] Exception:", str(e))
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Decryption failed"})

@app.get("/generate-2fa")
async def generate_2fa_endpoint():
    if not SEED_FILE_PATH.exists():
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})
    try:
        hex_seed = SEED_FILE_PATH.read_text(encoding="utf-8").strip()
        code = generate_totp_code(hex_seed)
        now = int(time.time())
        valid_for = 29 - (now % 30)
        if valid_for < 0:
            valid_for = 0
        return {"code": code, "valid_for": valid_for}
    except Exception as e:
        print("[generate-2fa] Exception:", str(e))
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

@app.post("/verify-2fa")
async def verify_2fa_endpoint(req: VerifyRequest):
    code = (req.code or "").strip()
    # validate code is 6 digits
    if not code:
        return JSONResponse(status_code=400, content={"error": "Missing code"})
    if not re.fullmatch(r"\d{6}", code):
        return JSONResponse(status_code=400, content={"error": "Invalid code format"})

    if not SEED_FILE_PATH.exists():
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    try:
        hex_seed = SEED_FILE_PATH.read_text(encoding="utf-8").strip()
        is_valid = verify_totp_code(hex_seed, code, valid_window=1)
        return {"valid": is_valid}
    except Exception as e:
        print("[verify-2fa] Exception:", str(e))
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})
