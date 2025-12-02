import os
import requests
from typing import Dict

API_URL = "https://eajeyq4r32ljqo4rpvoy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"

# Your real student ID
STUDENT_ID = "23MH1A05F0"

# Your exact GitHub repo URL (no .git at the end)
GITHUB_REPO_URL = "https://github.com/Priyanka05f0/pki-2fa-microservice"


def request_seed(student_id: str, github_repo_url: str, api_url: str) -> Dict:
    """
    Request encrypted seed from instructor API.
    """

    # 1️⃣ Read and validate student public key
    print("1. Reading student_public.pem...")
    try:
        with open("student_public.pem", "r", encoding="utf-8") as f:
            public_key_raw = f.read().strip()

        # Check BEGIN/END markers
        if not (
            public_key_raw.startswith("-----BEGIN PUBLIC KEY-----")
            and public_key_raw.endswith("-----END PUBLIC KEY-----")
        ):
            raise ValueError("Public key file is missing BEGIN/END markers.")

        # Format for API: single line string with literal '\n'
        public_key_formatted = public_key_raw.replace("\n", "\\n")

    except FileNotFoundError:
        print("🚨 ERROR: 'student_public.pem' not found.")
        print("Please ensure the public key file is in the same directory.")
        return {}
    except ValueError as e:
        print(f"🚨 ERROR: Public key format issue: {e}")
        return {}

    # 2️⃣ Prepare JSON payload
    payload = {
        "student_id": student_id,
        "github_repo_url": github_repo_url,
        "public_key": public_key_formatted,
    }

    # 3️⃣ Optional: API key / Bearer token (if instructor gives you one)
    api_key = os.getenv("INSTRUCTOR_API_KEY")

    headers = {
        "Content-Type": "application/json",
    }

    if api_key:
        # If your assignment says to use a different header name,
        # like 'X-API-Key', change this line accordingly.
        headers["Authorization"] = f"Bearer {api_key}"

    print("\n2. Sending payload to instructor API...")
    print("   student_id:", student_id)
    print("   github_repo_url:", github_repo_url)
    print("   public_key (first 50 chars):", public_key_formatted[:50] + "...")
    if api_key:
        print("   Using API key from INSTRUCTOR_API_KEY.")
    else:
        print("   No API key configured (INSTRUCTOR_API_KEY not set).")

    # 4️⃣ Send POST request
    response = requests.post(api_url, json=payload, headers=headers, timeout=20)

    print("\n3. API Response:")
    print("   Status code:", response.status_code)
    print("   Raw response text:", response.text)

    if response.status_code != 200:
        raise RuntimeError(f"API returned non-200 status: {response.status_code}")

    # 5️⃣ Parse JSON
    data = response.json()
    if data.get("status") != "success":
        raise RuntimeError(f"API Error (status != success): {data}")

    encrypted_seed = data.get("encrypted_seed")
    if not encrypted_seed:
        raise RuntimeError("Missing encrypted_seed in API response")

    # 6️⃣ Save result locally (DO NOT commit this file)
    with open("encrypted_seed.txt", "w", encoding="utf-8") as f:
        f.write(encrypted_seed)

    print("\n4. 🎉 Encrypted seed saved to encrypted_seed.txt ✔")
    return data


if __name__ == "__main__":
    request_seed(STUDENT_ID, GITHUB_REPO_URL, API_URL)
