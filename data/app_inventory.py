"""Fetches app inventory (AppInvRawData) and computes update status per device.

Tracked apps and the rule (latest version found = "Atualizado") are configured
in TRACKED_APPS below. To add/change an app, edit only this dict.
"""
import time
import zipfile
import io
import requests
import pandas as pd
import msal

from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET

# package_name -> friendly label shown in the dashboard
TRACKED_APPS = {
    "br.com.cea.associada": "Associada",
    "br.com.cea.xstore.eftlink": "PDV Móvel",
    "br.com.cea.xstore.eftlink.ace": "PDV Móvel ACE",
}


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


def _version_key(v: str):
    """Sortable key for versions like '2.9.2.20260526.1431'. Falls back to string."""
    if pd.isna(v):
        return ()
    parts = []
    for chunk in str(v).replace("(", ".").replace(")", "").split("."):
        chunk = chunk.strip()
        parts.append((1, int(chunk)) if chunk.isdigit() else (0, chunk))
    return tuple(parts)


def fetch_app_status() -> pd.DataFrame:
    """Returns one row per DeviceId with version + status columns per tracked app.

    Columns: DeviceId, <label>_version, <label>_status for each tracked app.
    Status is one of: "Atualizado", "Desatualizado", "Não instalado".
    """
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = requests.post(
        "https://graph.microsoft.com/beta/deviceManagement/reports/exportJobs",
        headers=headers,
        json={"reportName": "AppInvRawData", "format": "csv", "select": []},
        timeout=20,
    )
    r.raise_for_status()
    job_id = r.json()["id"]

    df = None
    for _ in range(36):
        time.sleep(5)
        token = _get_token()
        job = requests.get(
            f"https://graph.microsoft.com/beta/deviceManagement/reports/exportJobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        ).json()
        if job.get("status") == "completed":
            resp = requests.get(job["url"], timeout=180)
            resp.raise_for_status()
            zf = zipfile.ZipFile(io.BytesIO(resp.content))
            with zf.open(zf.namelist()[0]) as f:
                df = pd.read_csv(
                    f, encoding="utf-8-sig", low_memory=False,
                    usecols=["ApplicationName", "ApplicationVersion", "DeviceId"],
                )
            break
        if job.get("status") == "failed":
            raise RuntimeError(f"AppInvRawData export failed: {job}")
    if df is None:
        raise TimeoutError("AppInvRawData export timed out")

    # Build per-device status for each tracked app
    result = pd.DataFrame({"DeviceId": df["DeviceId"].dropna().unique()})

    for pkg, label in TRACKED_APPS.items():
        app_df = df[df["ApplicationName"] == pkg][["DeviceId", "ApplicationVersion"]].copy()
        if app_df.empty:
            result[f"{label}_version"] = None
            result[f"{label}_status"] = "Não instalado"
            continue

        # Latest version across the fleet = the "current" target
        versions = app_df["ApplicationVersion"].dropna().unique()
        latest = max(versions, key=_version_key) if len(versions) else None

        # Keep one (latest installed) version per device
        app_df["vkey"] = app_df["ApplicationVersion"].apply(_version_key)
        app_df = app_df.sort_values("vkey").drop_duplicates("DeviceId", keep="last")
        app_df = app_df[["DeviceId", "ApplicationVersion"]].rename(
            columns={"ApplicationVersion": f"{label}_version"}
        )

        result = result.merge(app_df, on="DeviceId", how="left")
        result[f"{label}_status"] = result[f"{label}_version"].apply(
            lambda v: "Não instalado" if pd.isna(v)
            else ("Atualizado" if v == latest else "Desatualizado")
        )

    return result


def latest_versions(df: pd.DataFrame) -> dict:
    """Returns {label: latest_version_string} for display."""
    out = {}
    for label in TRACKED_APPS.values():
        col = f"{label}_version"
        if col in df.columns:
            atual = df[df.get(f"{label}_status") == "Atualizado"][col].dropna()
            out[label] = atual.iloc[0] if not atual.empty else None
    return out
