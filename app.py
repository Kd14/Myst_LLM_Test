import streamlit as st
import json
import pandas as pd
import subprocess
from datetime import datetime

st.title("Bulk Export Trigger")

if st.button("Run Bulk Export"):
    st.write("Starting bulk export...")
    try:
        # Run the bulk_export.py script
        result = subprocess.run(
            ["python3", "bulk_export.py"],
            capture_output=True,
            text=True,
            check=True
        )
        st.success("Bulk export completed successfully!")
        st.text_area("Output", result.stdout, height=300)
    except subprocess.CalledProcessError as e:
        st.error("Bulk export failed!")
        st.text_area("Error output", e.stderr, height=300)


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

def render_diagnostic_report(report):
    st.markdown("### 🧪 Diagnostic Report")
    st.info(f"**Report Type:** {report.get('code', {}).get('text', 'N/A')}  |  **Status:** `{report.get('status', 'N/A')}`")

    st.write("**Issued:**", format_datetime(report.get("issued")))
    st.write("**Effective Date:**", format_datetime(report.get("effectiveDateTime")))

    # Subject
    subject = report.get("subject", {}).get("display", report.get("subject", {}).get("reference", "Unknown"))
    st.write("**Patient:**", subject)

    # Encounter
    if "encounter" in report:
        st.write("**Encounter:**", report["encounter"].get("display", report["encounter"].get("reference", "N/A")))

    # Category
    categories = [cat.get("text", "") for cat in report.get("category", [])]
    st.write("**Category:**", ", ".join(categories) or "N/A")

    # Performer(s)
    performers = [perf.get("display", perf.get("reference", "")) for perf in report.get("performer", [])]
    st.write("**Performed By:**", ", ".join(performers) or "N/A")

    # Based on
    if "basedOn" in report:
        st.write("**Based On:**")
        for based in report["basedOn"]:
            st.markdown(f"- {based.get('display', based.get('reference'))}")

    # Results
    if "result" in report:
        st.write("**Results:**")
        for result in report["result"]:
            st.markdown(f"- {result.get('display', result.get('reference'))}")

    # Imaging Studies
    if "imagingStudy" in report:
        st.write("**Imaging Studies:**")
        for study in report["imagingStudy"]:
            st.markdown(f"- {study.get('reference')}")

    # Presented Form
    if "presentedForm" in report:
        st.write("**Report Files:**")
        for form in report["presentedForm"]:
            title = form.get("title", "Download")
            url = form.get("url", "#")
            st.markdown(f"[{title}]({url})")

def extract_observation_summary(resource):
    """
    Custom summary extractor for Observation resource, especially BP vitals with components.
    """
    # Basic info
    obs_id = resource.get("id", "")
    status = resource.get("status", "")
    category = ", ".join([cat.get("text", "") for cat in resource.get("category", [])])
    code = resource.get("code", {}).get("text", "")

    subject = resource.get("subject", {}).get("display", resource.get("subject", {}).get("reference", ""))
    effective = resource.get("effectiveDateTime", "")
    issued = resource.get("issued", "")

    # Components (e.g. systolic/diastolic for BP)
    components = resource.get("component", [])
    comp_summary = {}
    for c in components:
        ctext = c.get("code", {}).get("text", "")
        val_qty = c.get("valueQuantity", {})
        val = val_qty.get("value", "")
        unit = val_qty.get("unit", "")
        if ctext:
            comp_summary[ctext] = f"{val} {unit}".strip()

    # Compose a display string for components if exist
    if comp_summary:
        comp_display = "; ".join([f"{k}: {v}" for k, v in comp_summary.items()])
    else:
        # Fallback to valueQuantity on root Observation if no components
        val_qty = resource.get("valueQuantity", {})
        if val_qty:
            comp_display = f"{val_qty.get('value', '')} {val_qty.get('unit', '')}".strip()
        else:
            comp_display = ""

    return {
        "ID": obs_id,
        "Status": status,
        "Category": category,
        "Code": code,
        "Subject": subject,
        "Effective Date": effective,
        "Issued": issued,
        "Values": comp_display,
    }


def format_datetime(dt_string):
    try:
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00")).strftime("%b %d, %Y %H:%M")
    except:
        return dt_string or "N/A"

def display_summary(records, resource_type):
    if resource_type == "Patient":
        rows = [extract_patient_summary(r) for r in records]
        df = pd.DataFrame(rows)
        st.dataframe(df)
    elif resource_type == "Immunization":
        rows = [extract_immunization_summary(r) for r in records]
        df = pd.DataFrame(rows)
        st.dataframe(df)
    elif resource_type == "DiagnosticReport":
        for report in records:
            with st.expander(f"Report ID: {report.get('id', 'Unknown')}"):
                render_diagnostic_report(report)
        # Optional: for download
        df = pd.json_normalize(records)
        csv = df.to_csv(index=False)
        st.download_button("Download DiagnosticReport data as CSV", csv, "DiagnosticReport.csv", "text/csv")
    elif resource_type == "Observation":
        rows = [extract_observation_summary(r) for r in records]
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.warning(f"No custom view for resourceType '{resource_type}'. Showing raw data.")
        df = pd.json_normalize(records)
        st.dataframe(df)
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
