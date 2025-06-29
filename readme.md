# FHIR Bulk Export and NDJSON Viewer

## Overview

This project includes two Python scripts designed to work with the Epic EHR Sandbox FHIR APIs:

- **`bulk_export.py`**:  
  Initiates and manages asynchronous Bulk Data Export jobs to retrieve large sets of FHIR resources (Patients, Immunizations, Observations, etc.) from the Epic sandbox. Downloads the resulting NDJSON files locally.

- **`app.py`**:  
  A Streamlit-based web app to upload and view the exported NDJSON files. It parses and displays resource data in human-friendly tables and JSON views, including custom formatting for Observations like vital signs.

---

## How They Work

### `bulk_export.py`

- Implements OAuth 2.0 Client Credentials flow **using JWT-based authentication** with a client certificate.
- Generates a signed JWT assertion using a private key to request an access token from Epic's authorization server.
- Starts a Bulk Data Export job by calling the sandbox `$export` endpoint.
- Polls the export status endpoint until the job completes.
- Downloads NDJSON export files to disk.

### `app.py`

- Provides a Streamlit web interface to upload exported NDJSON files.
- Parses and displays FHIR resource data with formatting tailored to resource types.
- Allows users to download filtered data as CSV.
- Displays raw JSON for detailed inspection.

---

## Setup

### 1. Register Your Backend Service Application in Epic Developer Sandbox

- Create an OAuth2 **Backend Service** app in the Epic Developer Sandbox portal.
- Upload a **public X.509 certificate** that corresponds to your private key.
- Configure the app to allow the Bulk FHIR Export scopes you need (e.g., `system/Patient.read`, `system/Observation.read`, etc.).
- Note the **Client ID** generated for your app.

### 2. Generate Your Public/Private Key Pair

You need to generate an RSA key pair to authenticate with Epic via JWT-based client assertion.

Here is a sample way to generate keys using OpenSSL:

```bash
# Generate a private key (PEM format)
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048

# Generate a public key certificate (self-signed) from the private key
openssl req -new -x509 -key private_key.pem -out public_cert.pem -days 365 -subj "/CN=YourAppName"


Upload `public_cert.pem` to the Epic Developer Sandbox portal when registering your app.

Keep `private_key.pem` secure on your backend server.

### 3. Configure Environment Variables
Create a `.env` file with your sensitive configuration (never commit this to source control):

```env
CLIENT_ID=your-epic-client-id
PRIVATE_KEY_PATH=/path/to/private_key.pem
AUTH_URL=[https://fhir.epic.com/interconnect-fhir/oauth2/token](https://fhir.epic.com/interconnect-fhir/oauth2/token)
FHIR_BASE_URL=[https://fhir.epic.com/interconnect-fhir/api/FHIR/DSTU2](https://fhir.epic.com/interconnect-fhir/api/FHIR/DSTU2)
SCOPES=system/Patient.read system/Observation.read system/Immunization.read system/DiagnosticReport.read system/$export