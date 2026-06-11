import time
import zipfile
import io
import requests
import pandas as pd
import msal

from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, GRAPH_BASE_URL

REPORT_NAME = "DevicesWithInventory"
EXPORT_URL = f"{GRAPH_BASE_URL}/beta/deviceManagement/reports/exportJobs"


def _get_token() -> str:
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(result.get("error_description", "Token acquisition failed"))
    return result["access_token"]


def fetch_inventory_report() -> pd.DataFrame:
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create export job
    r = requests.post(
        "https://graph.microsoft.com/beta/deviceManagement/reports/exportJobs",
        headers=headers,
        json={"reportName": REPORT_NAME, "format": "csv", "select": []},
        timeout=20,
    )
    r.raise_for_status()
    job_id = r.json()["id"]

    # Poll until complete (max 2 min)
    for _ in range(24):
        time.sleep(5)
        token = _get_token()
        r2 = requests.get(
            f"https://graph.microsoft.com/beta/deviceManagement/reports/exportJobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        r2.raise_for_status()
        job = r2.json()
        if job.get("status") == "completed" and job.get("url"):
            resp = requests.get(job["url"], timeout=120)
            resp.raise_for_status()
            zf = zipfile.ZipFile(io.BytesIO(resp.content))
            with zf.open(zf.namelist()[0]) as f:
                df = pd.read_csv(f, encoding="utf-8-sig", low_memory=False)
            for col in ["EnrolledDate", "LastContact"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
            return df
        if job.get("status") == "failed":
            raise RuntimeError(f"Export job failed: {job}")

    raise TimeoutError("Export job timed out after 2 minutes")
