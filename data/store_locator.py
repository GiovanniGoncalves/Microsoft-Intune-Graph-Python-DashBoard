from typing import Optional
import pandas as pd
from ipaddress import ip_address

BOUNDARY_FILE = (
    "/Users/dsiwrkmng/Library/CloudStorage/"
    "OneDrive-BibliotecasCompartilhadas-C&AModasS.A/"
    "Field Sharepoint - Documentos/Controles/REPORTS_BI/"
    "REPORT_ANDROID_FULL_LOJA/BASE_GATEWAY_BAUDERY.xlsx"
)

_boundaries: Optional[pd.DataFrame] = None


def _load_boundaries() -> pd.DataFrame:
    global _boundaries
    if _boundaries is None:
        df = pd.read_excel(BOUNDARY_FILE, sheet_name="Boundaries Full")
        df.columns = ["start_ip", "end_ip", "loja"]
        df["start_int"] = df["start_ip"].apply(lambda x: int(ip_address(str(x))))
        df["end_int"] = df["end_ip"].apply(lambda x: int(ip_address(str(x))))
        df = df.sort_values("start_int").reset_index(drop=True)
        _boundaries = df
    return _boundaries


def ip_to_loja(ip_str: str) -> Optional[str]:
    if not ip_str or pd.isna(ip_str):
        return None
    try:
        bounds = _load_boundaries()
        ip_int = int(ip_address(str(ip_str).strip()))
        match = bounds[(bounds["start_int"] <= ip_int) & (bounds["end_int"] >= ip_int)]
        if not match.empty:
            return match.iloc[0]["loja"]
    except Exception:
        pass
    return None


def enrich_with_loja(df: pd.DataFrame, ip_col: str = "WiFiIPv4Address") -> pd.DataFrame:
    if ip_col not in df.columns:
        df["loja"] = None
        return df
    bounds = _load_boundaries()

    def _match(ip_str):
        if not ip_str or pd.isna(ip_str):
            return None
        try:
            ip_int = int(ip_address(str(ip_str).strip()))
            match = bounds[(bounds["start_int"] <= ip_int) & (bounds["end_int"] >= ip_int)]
            return match.iloc[0]["loja"] if not match.empty else None
        except Exception:
            return None

    df = df.copy()
    df["loja"] = df[ip_col].apply(_match)
    return df
