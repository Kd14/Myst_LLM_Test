import requests
from authlib.jose import jwt
from datetime import datetime, timedelta, timezone
import uuid
import time
from dotenv import load_dotenv
import os

load_dotenv()

# ==== CONFIGURATION ====
CLIENT_ID = os.getenv("CLIENT_ID")
PRIVATE_KEY_PATH = "private_key.pem"  
TOKEN_URL = os.getenv("TOKEN_URL")
AUDIENCE = TOKEN_URL
GROUP_ID = os.getenv("GROUP_ID")

# ==== BUILD SIGNED JWT ====
def build_jwt(client_id, audience, private_key):
    header = {"alg": "RS384", "kid": "577ED89C846294D944A31D981E91B2F9935837CA"}
    now = datetime.now(timezone.utc)
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": audience,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp":  int((now + timedelta(minutes=5)).timestamp())
    }
    return jwt.encode(header, payload, private_key).decode("utf-8")

# ==== GET ACCESS TOKEN ====
def get_access_token(client_id, jwt_token, token_url):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token,
        "scope": os.getenv("SCOPE") 
    }
    response = requests.post(token_url, headers=headers, data=data)
    print("Response:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()["access_token"]


# ==== BULK EXPORT KICKOFF ====
def bulk_kickoff_request(group_id, access_token):
    kickoff_url = f"https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/Group/{group_id}/$export"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/fhir+json",
        "Prefer": "respond-async"
    }
    response = requests.get(kickoff_url, headers=headers)
    if response.status_code == 202:
        print("Kickoff accepted. Status URL:")
        return response.headers['Content-Location']
    else:
        print("Kickoff failed:", response.status_code)
        print(response.text)
        return None
    
# ==== POLLING FOR STATUS ====

def poll_export_status(status_url, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    print("Polling export status...")
    while True:
        response = requests.get(status_url, headers=headers)
        if response.status_code == 202:
            print("Export still in progress...")
        elif response.status_code == 200:
            print("Export is ready.")
            status_json = response.json()
            return status_json.get("output", [])
        else:
            print("Error polling:", response.status_code, response.text)
            return []
        time.sleep(5)


# ==== DOWNLOAD NDJSON FILE ====
def download_ndjson(file_url, access_token, output_path):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    r = requests.get(file_url, headers=headers)
    r.raise_for_status()
    with open(output_path, 'wb') as f:
        f.write(r.content)
    print(f"Saved to {output_path}")

# ==== MAIN FLOW ====
def main():
    with open(PRIVATE_KEY_PATH, 'r') as f:
        private_key = f.read()

    print("Building JWT...")
    jwt_token = build_jwt(CLIENT_ID, AUDIENCE, private_key)

    print("Requesting access token...")
    access_token = get_access_token(CLIENT_ID, jwt_token, TOKEN_URL)

    print("Making bulk data kickoff request...")
    status_url = bulk_kickoff_request(GROUP_ID, access_token)

    if status_url:
        print("\n➡️  Check status at:", status_url)
        print("Polling export status...")
        export_files = poll_export_status(status_url, access_token)

        if export_files:
            print("\nExport completed successfully!")
            for file_entry in export_files:
                file_type = file_entry["type"]
                file_url = file_entry["url"]
                output_path = f"{file_type}.ndjson"
                download_ndjson(file_url, access_token, output_path)
        else:
            print("No export files found.")


if __name__ == "__main__":
    main()
