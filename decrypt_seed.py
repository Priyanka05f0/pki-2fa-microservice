import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


def decrypt_seed(encrypted_seed_b64: str, private_key) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP (SHA-256).

    Args:
        encrypted_seed_b64: Base64-encoded ciphertext string
        private_key: RSA private key object

    Returns:
        Decrypted seed as a 64-character hex string
    """

    # 1️⃣ Base64 decode the encrypted seed string
    try:
        ciphertext = base64.b64decode(encrypted_seed_b64.strip())
    except Exception as e:
        raise ValueError(f"Failed to base64-decode encrypted seed: {e}")

    # 2️⃣ RSA/OAEP decrypt with SHA-256
    try:
        plaintext_bytes = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as e:
        raise ValueError(f"RSA decryption failed: {e}")

    # 3️⃣ Decode bytes to UTF-8 string
    try:
        seed_str = plaintext_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"Decrypted bytes are not valid UTF-8: {e}")

    # 4️⃣ Validate: must be 64-character hex string
    if len(seed_str) != 64:
        raise ValueError(f"Seed length is {len(seed_str)}, expected 64")

    allowed_chars = set("0123456789abcdef")
    if not set(seed_str).issubset(allowed_chars):
        raise ValueError("Seed contains non-hex characters")

    # 5️⃣ Return hex seed
    return seed_str


def load_private_key_from_pem(path: str = "student_private.pem"):
    """
    Load RSA private key from PEM file.
    """
    pem_path = Path(path)
    if not pem_path.exists():
        raise FileNotFoundError(f"Private key file not found: {path}")

    with open(pem_path, "rb") as f:
        key_data = f.read()

    private_key = serialization.load_pem_private_key(
        key_data,
        password=None,  # we generated key without password
    )
    return private_key


def decrypt_seed_from_file(
    encrypted_seed_file: str = "encrypted_seed.txt",
    output_seed_file: str = "data/seed.txt",
):
    """
    Helper for CLI use:

    1. Load private key from student_private.pem
    2. Read encrypted seed from encrypted_seed.txt
    3. Decrypt it using decrypt_seed()
    4. Save decrypted hex seed to data/seed.txt
    """

    # Ensure data/ directory exists
    Path("data").mkdir(exist_ok=True)

    # Load private key
    private_key = load_private_key_from_pem("student_private.pem")

    # Read encrypted seed (base64 text)
    enc_path = Path(encrypted_seed_file)
    if not enc_path.exists():
        raise FileNotFoundError(
            f"Encrypted seed file not found: {encrypted_seed_file}. "
            "Make sure Step 4 has created encrypted_seed.txt."
        )

    encrypted_seed_b64 = enc_path.read_text(encoding="utf-8").strip()

    # Decrypt
    hex_seed = decrypt_seed(encrypted_seed_b64, private_key)

    # Save decrypted seed to data/seed.txt
    out_path = Path(output_seed_file)
    out_path.write_text(hex_seed, encoding="utf-8")

    print("✅ Decrypted seed (hex):", hex_seed)
    print(f"✅ Saved decrypted seed to {out_path}")


if __name__ == "__main__":
    # When you run:  python decrypt_seed.py
    decrypt_seed_from_file()
