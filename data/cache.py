import time
import pandas as pd
from data.graph_client import fetch_devices
from data.inventory_report import fetch_inventory_report
from data.store_locator import enrich_with_loja
from data.app_inventory import fetch_app_status

_devices_store: dict = {"df": None, "ts": 0.0}
_inventory_store: dict = {"df": None, "ts": 0.0}
_master_store: dict = {"df": None, "ts": 0.0}

TTL_DEVICES = 300     # 5 minutes
TTL_INVENTORY = 900   # 15 minutes (report takes ~15s to generate)
TTL_MASTER = 900      # 15 minutes


def get_devices() -> pd.DataFrame:
    if _devices_store["df"] is None or (time.time() - _devices_store["ts"]) > TTL_DEVICES:
        _devices_store["df"] = fetch_devices()
        _devices_store["ts"] = time.time()
    return _devices_store["df"].copy()


def get_inventory() -> pd.DataFrame:
    if _inventory_store["df"] is None or (time.time() - _inventory_store["ts"]) > TTL_INVENTORY:
        df = fetch_inventory_report()
        df = enrich_with_loja(df, ip_col="WiFiIPv4Address")
        _inventory_store["df"] = df
        _inventory_store["ts"] = time.time()
    return _inventory_store["df"].copy()


def get_stores_master() -> pd.DataFrame:
    """Device inventory + loja + app update status, one row per device (Android)."""
    if _master_store["df"] is None or (time.time() - _master_store["ts"]) > TTL_MASTER:
        inv = fetch_inventory_report()
        inv = enrich_with_loja(inv, ip_col="WiFiIPv4Address")
        apps = fetch_app_status()
        master = inv.merge(apps, left_on="Device ID", right_on="DeviceId", how="left")
        if "OS" in master.columns:
            master = master[master["OS"].str.contains("Android", case=False, na=False)]
        _master_store["df"] = master
        _master_store["ts"] = time.time()
    return _master_store["df"].copy()


def invalidate():
    for store in (_devices_store, _inventory_store, _master_store):
        store["df"] = None
        store["ts"] = 0.0
