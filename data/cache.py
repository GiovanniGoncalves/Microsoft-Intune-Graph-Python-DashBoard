import time
import pandas as pd
from data.graph_client import fetch_devices
from data.inventory_report import fetch_inventory_report
from data.store_locator import enrich_with_loja

_devices_store: dict = {"df": None, "ts": 0.0}
_inventory_store: dict = {"df": None, "ts": 0.0}

TTL_DEVICES = 300    # 5 minutes
TTL_INVENTORY = 900  # 15 minutes (report takes ~15s to generate)


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


def invalidate():
    _devices_store["df"] = None
    _devices_store["ts"] = 0.0
    _inventory_store["df"] = None
    _inventory_store["ts"] = 0.0
