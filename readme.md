# Epic EHR Proof of Concept

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
```

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
```
The scripts load these variables securely to handle authentication and API endpoints.

### 4.Running the project
Start the streamlit app:

```bash
streamlit run app.py
```

Press the "Run Bulk Export" button to trigger the bulk_export.py as a subporcess and wait for the .ndjson files to be downloaded. 

Select and of the files to view their contents in a user-friendly manner

### 5. Notes of EPIC Sandbox data
#### Read-Only Environment

The Epic Sandbox is a read-only testing environment. You cannot create, update, or delete data programmatically or via UI. This protects the sandbox from corruption and mimics production constraints.

#### No Data Upload
You cannot import or upload external datasets (e.g., Kaggle data) into the sandbox.

#### Data Persistence
The sandbox is periodically reset by Epic, so data may revert to its initial state.

#### Asynchronous Data Updates & Bulk Export
Epic does not support webhooks or push notifications for real-time data changes in the sandbox.

To check for new data, you must poll FHIR endpoints or use Bulk Data Export repeatedly.

The Bulk Data Export API allows asynchronous batch export of large datasets via a job system:

* Initiate export job

* Poll job status

* Download completed NDJSON files

This method is suitable for periodic sync but not for real-time streaming.

## Summary
This project demonstrates:

* How to securely authenticate with Epic sandbox backend service apps using JWT client assertion and uploaded certificates.

* How to perform bulk asynchronous export of FHIR resources.

* How to view and explore exported data via an interactive Streamlit web app.

* The operational constraints of the Epic sandbox environment and strategies for asynchronous data handling.