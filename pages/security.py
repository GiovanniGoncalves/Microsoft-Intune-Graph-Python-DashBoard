import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices

COMPLIANCE_COLORS = {
    "compliant": "#198754",
    "noncompliant": "#dc3545",
    "inGracePeriod": "#ffc107",
    "error": "#dc3545",
    "conflict": "#fd7e14",
    "unknown": "#6c757d",
    "configManager": "#0dcaf0",
}


def _kpi(title: str, value, color: str = "primary") -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted small"),
            html.H2(str(value), className=f"text-{color} fw-bold mb-0"),
        ]),
        className="shadow-sm text-center h-100",
    )


def layout() -> html.Div:
    df = get_devices()
    total = len(df)

    compliant = len(df[df["complianceState"] == "compliant"]) if "complianceState" in df.columns else 0
    noncompliant = len(df[df["complianceState"] == "noncompliant"]) if "complianceState" in df.columns else 0
    compliance_pct = round(compliant / total * 100, 1) if total > 0 else 0

    jailbroken = len(df[df["jailBroken"] == "Jailbroken"]) if "jailBroken" in df.columns else 0
    not_encrypted = len(df[df["isEncrypted"] == False]) if "isEncrypted" in df.columns else 0

    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=compliance_pct,
        title={"text": "Compliance Geral (%)"},
        delta={"reference": 90, "suffix": "% meta"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#198754"},
            "steps": [
                {"range": [0, 60], "color": "#f8d7da"},
                {"range": [60, 80], "color": "#fff3cd"},
                {"range": [80, 100], "color": "#d1e7dd"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 90,
            },
        },
    ))
    fig_gauge.update_layout(height=320, margin=dict(t=50, b=10))

    # Compliance distribution
    if "complianceState" in df.columns:
        comp_dist = df["complianceState"].value_counts().reset_index()
        comp_dist.columns = ["Estado", "Total"]
        fig_compliance = px.bar(
            comp_dist, x="Estado", y="Total",
            title="Distribuição de Compliance",
            color="Estado",
            color_discrete_map=COMPLIANCE_COLORS,
            labels={"Total": "Dispositivos"},
        )
        fig_compliance.update_layout(showlegend=False, margin=dict(t=50, b=10))
    else:
        fig_compliance = go.Figure()

    # Non-compliant + security risk table
    risk_df = df[df["complianceState"] != "compliant"].copy() if "complianceState" in df.columns else df.copy()
    risk_cols = ["deviceName", "operatingSystem", "osVersion", "userDisplayName", "complianceState", "isEncrypted", "jailBroken", "lastSyncDateTime"]
    risk_cols = [c for c in risk_cols if c in risk_df.columns]
    risk_table = risk_df[risk_cols].copy()

    if "lastSyncDateTime" in risk_table.columns:
        risk_table["lastSyncDateTime"] = risk_table["lastSyncDateTime"].dt.strftime("%Y-%m-%d")
    if "isEncrypted" in risk_table.columns:
        risk_table["isEncrypted"] = risk_table["isEncrypted"].map({True: "Sim", False: "Não", None: "Desconhecido"}).fillna("Desconhecido")

    # Compliance by platform
    if "complianceState" in df.columns and "operatingSystem" in df.columns:
        plat_comp = df.groupby(["operatingSystem", "complianceState"]).size().reset_index(name="Total")
        fig_plat_comp = px.bar(
            plat_comp, x="operatingSystem", y="Total", color="complianceState",
            title="Compliance por Plataforma",
            labels={"operatingSystem": "Plataforma", "complianceState": "Estado"},
            color_discrete_map=COMPLIANCE_COLORS,
            barmode="stack",
        )
        fig_plat_comp.update_layout(margin=dict(t=50, b=10))
    else:
        fig_plat_comp = go.Figure()

    return html.Div([
        html.H4("Segurança", className="mb-4 fw-bold"),

        dbc.Row([
            dbc.Col(_kpi("Conformes", compliant, "success"), md=3),
            dbc.Col(_kpi("Não Conformes", noncompliant, "danger"), md=3),
            dbc.Col(_kpi("Jailbroken / Root", jailbroken, "danger" if jailbroken > 0 else "success"), md=3),
            dbc.Col(_kpi("Sem Criptografia", not_encrypted, "danger" if not_encrypted > 0 else "success"), md=3),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_gauge), md=5),
            dbc.Col(dcc.Graph(figure=fig_compliance), md=7),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_plat_comp), md=12),
        ], className="mb-4"),

        html.H5(f"Dispositivos com Risco ({len(risk_table)})", className="mb-3 fw-semibold text-danger"),
        dash_table.DataTable(
            data=risk_table.to_dict("records"),
            columns=[{"name": c, "id": c} for c in risk_table.columns],
            sort_action="native",
            filter_action="native",
            page_size=20,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px", "fontSize": "13px"},
            style_header={"backgroundColor": "#343a40", "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": '{complianceState} = "noncompliant"'}, "backgroundColor": "#f8d7da"},
                {"if": {"filter_query": '{isEncrypted} = "Não"'}, "backgroundColor": "#fff3cd"},
                {"if": {"filter_query": '{jailBroken} = "Jailbroken"'}, "backgroundColor": "#f8d7da"},
            ],
        ),
    ])
