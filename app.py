import streamlit as st
import json
import pandas as pd

def load_ndjson(file_obj):
    return [json.loads(line) for line in file_obj if line.strip()]

def extract_patient_summary(resource):
    name = resource.get("name", [{}])[0]
    given = " ".join(name.get("given", []))
    family = name.get("family", "")
    gender = resource.get("gender", "")
    birthDate = resource.get("birthDate", "")
    return {
        "ID": resource.get("id", ""),
        "Name": f"{given} {family}".strip(),
        "Gender": gender,
        "Birth Date": birthDate,
    }

def extract_immunization_summary(resource):
    patient_ref = resource.get("patient", {}).get("reference", "")
    status = resource.get("status", "")
    vaccine_code = resource.get("vaccineCode", {}).get("text", "")
    occurrence = resource.get("occurrenceDateTime", "")
    return {
        "Patient": patient_ref,
        "Status": status,
        "Vaccine": vaccine_code,
        "Date": occurrence,
    }

def display_summary(records, resource_type):
    if resource_type == "Patient":
        rows = [extract_patient_summary(r) for r in records]
        df = pd.DataFrame(rows)
        st.dataframe(df)
    elif resource_type == "Immunization":
        rows = [extract_immunization_summary(r) for r in records]
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.warning(f"No custom view for resourceType '{resource_type}'. Showing raw data.")
        df = pd.json_normalize(records)
        st.dataframe(df)

    # Optional: download as CSV
    csv = df.to_csv(index=False)
    st.download_button(f"Download {resource_type} data as CSV", csv, f"{resource_type}.csv", "text/csv")

def main():
    st.title("FHIR NDJSON Viewer")

    uploaded_file = st.file_uploader("Upload a FHIR .ndjson file", type=["ndjson"])
    if uploaded_file:
        try:
            records = load_ndjson(uploaded_file)
            if not records:
                st.error("The file appears to be empty or not properly formatted.")
                return

            resource_type = records[0].get("resourceType", "Unknown")
            st.subheader(f"Detected Resource Type: {resource_type}")

            display_summary(records, resource_type)

            with st.expander("View Raw JSON Records"):
                for i, record in enumerate(records[:10]):
                    st.json(record)

        except Exception as e:
            st.error(f"Error parsing file: {e}")

if __name__ == "__main__":
    main()
 