import requests
import json
import os

# --- Configuration (CRITICAL: UPDATE STUDENT_ID MANUALLY) ---

STUDENT_ID = "23MH1A05F0"  
# Your provided GitHub URL
GITHUB_REPO_URL = "https://github.com/Priyanka05f0/pki-2fa-microservice"  
API_URL = "https://eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"
PUBLIC_KEY_FILE = "student_public.pem"
OUTPUT_FILE = "encrypted_seed.txt" 

def format_public_key_for_json(key_path: str) -> str:
    """
    Reads the public key, keeps the newline characters as they are, and 
    lets the requests library handle the standard JSON escaping. 
    This is the fix for the double-escaping error.
    """
    try:
        with open(key_path, 'r') as f:
            key_content = f.read()
            # 1. Strip external whitespace
            key_content = key_content.strip()
            # 2. Return content with actual newlines. Requests/json will convert this to \n automatically.
            return key_content
            
    except FileNotFoundError:
        print(f"Error: Public key file not found at {key_path}.")
        return None
    except Exception as e:
        print(f"Error reading public key: {e}")
        return None

def request_seed(student_id: str, github_repo_url: str, api_url: str):
    """
    Requests encrypted seed from instructor API and saves it to a file.
    """
    # 1. Read and format student public key
    public_key_string = format_public_key_for_json(PUBLIC_KEY_FILE)
    if not public_key_string:
        print("Failed to format public key. Exiting.")
        return

    # 2. Prepare HTTP POST request payload
    payload = {
        "student_id": student_id,
        "github_repo_url": github_repo_url,
        "public_key": public_key_string
    }
    
    print(f"Requesting seed for student ID: {student_id}...")
    print(f"Using Repository URL: {github_repo_url}")

    # 3. Send POST request to instructor API
    headers = {'Content-Type': 'application/json'}
    try:
        # Note: requests.post handles the JSON serialization (including the \n escaping)
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        
        # Check for non-200 status codes
        if response.status_code != 200:
            try:
                # Try to extract the specific error message from the JSON response
                error_details = response.json().get('error', response.text)
            except json.JSONDecodeError:
                # If the response isn't JSON, just print the text content
                error_details = response.text
                
            print(f"\n[ERROR] API Request Failed: HTTP {response.status_code}")
            print(f"  API Error Detail: {error_details}")
            print("\nPOSSIBLE CAUSES TO CHECK:")
            print("1. Did you fill in your FULL STUDENT_ID?")
            print("2. Is 'student_public.pem' correctly committed and public on GitHub?")
            return

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] API Request Failed: {e}")
        return

    # 4. Parse JSON response
    try:
        data = response.json()
        if data.get("status") != "success":
            print(f"\n[ERROR] API returned status: {data.get('status', 'unknown')}")
            print(f"Details: {data.get('error', 'No error detail provided.')}")
            return
        
        encrypted_seed = data.get("encrypted_seed")
        if not encrypted_seed:
            print("[ERROR] API response missing 'encrypted_seed' field.")
            return

        # 5. Save encrypted seed to file
        with open(OUTPUT_FILE, 'w') as f:
            f.write(encrypted_seed)
        
        print("\n[SUCCESS] Encrypted seed received.")
        print(f"Seed saved to: {OUTPUT_FILE}")
        print("REMINDER: DO NOT commit 'encrypted_seed.txt' to Git.")
        
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to decode JSON response: {response.text}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Safety check for placeholder
    if "FULL" in STUDENT_ID:
        print("=========================================================================")
        print("  CRITICAL ERROR: Please update STUDENT_ID in the script with your FULL ID.")
        print("=========================================================================")
    else:
        request_seed(STUDENT_ID, GITHUB_REPO_URL, API_URL)
