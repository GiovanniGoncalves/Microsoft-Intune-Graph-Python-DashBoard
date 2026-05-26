import time
import pandas as pd
from data.graph_client import fetch_devices

_store: dict = {"df": None, "ts": 0.0}
TTL = 300  # 5 minutes


def get_devices() -> pd.DataFrame:
    if _store["df"] is None or (time.time() - _store["ts"]) > TTL:
        _store["df"] = fetch_devices()
        _store["ts"] = time.time()
    return _store["df"].copy()


def invalidate():
    _store["df"] = None
    _store["ts"] = 0.0
