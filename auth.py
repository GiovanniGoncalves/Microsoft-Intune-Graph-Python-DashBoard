import msal
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, GRAPH_SCOPES


def get_access_token() -> str:
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=GRAPH_SCOPES)
    if "access_token" not in result:
        raise RuntimeError(result.get("error_description", "Token acquisition failed"))
    return result["access_token"]
