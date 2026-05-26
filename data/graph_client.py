import requests
import pandas as pd
from auth import get_access_token
from config import GRAPH_BASE_URL

DEVICE_FIELDS = [
    "id", "deviceName", "operatingSystem", "osVersion", "complianceState",
    "lastSyncDateTime", "enrolledDateTime", "userPrincipalName", "userDisplayName",
    "manufacturer", "model", "managedDeviceOwnerType", "isEncrypted", "jailBroken",
    "managementState", "emailAddress", "serialNumber", "phoneNumber",
    "deviceEnrollmentType", "deviceCategoryDisplayName", "azureADRegistered",
    "androidSecurityPatchLevel", "managementAgent", "subscriberCarrier",
    "totalStorageSpaceInBytes", "freeStorageSpaceInBytes", "physicalMemoryInBytes",
    "partnerReportedThreatState", "imei",
]


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_access_token()}"}


def _paginate(url: str) -> list:
    items = []
    while url:
        r = requests.get(url, headers=_headers(), timeout=30)
        r.raise_for_status()
        body = r.json()
        items.extend(body.get("value", []))
        url = body.get("@odata.nextLink")
    return items


def fetch_devices() -> pd.DataFrame:
    select = ",".join(DEVICE_FIELDS)
    url = f"{GRAPH_BASE_URL}/deviceManagement/managedDevices?$select={select}&$top=999"
    records = _paginate(url)
    if not records:
        return pd.DataFrame(columns=DEVICE_FIELDS)
    df = pd.DataFrame(records)
    for col in ["lastSyncDateTime", "enrolledDateTime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df
