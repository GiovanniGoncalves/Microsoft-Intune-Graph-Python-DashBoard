import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices
from pages.components import (
    kpi_card, chart_card, page_header, section_title,
    apply_dark, TABLE_KWARGS, BG_CARD, BORDER, TEXT,
    PRIMARY, SUCCESS, WARNING, DANGER,
)

COMPLIANCE_COLORS = {
    "compliant":     SUCCESS,
    "noncompliant":  DANGER,
    "inGracePeriod": WARNING,
    "error":         DANGER,
    "conflict":      "#ffa657",
    "unknown":       "#7d8590",
    "configManager": "#79c0ff",
}


def layout() -> html.Div:
    df    = get_devices()
    total = len(df)

    compliant      = len(df[df["complianceState"] == "compliant"])    if "complianceState" in df.columns else 0
    noncompliant   = len(df[df["complianceState"] == "noncompliant"]) if "complianceState" in df.columns else 0
    compliance_pct = round(compliant / total * 100, 1) if total > 0 else 0

    jailbroken    = len(df[df["jailBroken"]   == "Jailbroken"]) if "jailBroken"   in df.columns else 0
    not_encrypted = len(df[df["isEncrypted"]  == False])        if "isEncrypted"  in df.columns else 0

    # ── Gauge de compliance ───────────────────────────────────
    gauge_color = SUCCESS if compliance_pct >= 80 else (WARNING if compliance_pct >= 60 else DANGER)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=compliance_pct,
        title={"text": "Compliance Geral (%)", "font": {"color": TEXT, "size": 14}},
        number={"font": {"color": gauge_color, "size": 48}, "suffix": "%"},
        delta={"reference": 90, "suffix": "% meta", "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": TEXT},
            "bar": {"color": gauge_color},
            "bgcolor": "#1c2128",
            "bordercolor": BORDER,
            "steps": [
                {"range": [0,  60], "color": "rgba(248,81,73,0.15)"},
                {"range": [60, 80], "color": "rgba(210,153,34,0.15)"},
                {"range": [80, 100], "color": "rgba(63,185,80,0.15)"},
            ],
            "threshold": {
                "line": {"color": DANGER, "width": 3},
                "thickness": 0.75,
                "value": 90,
            },
        },
    ))
    fig_gauge.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        margin=dict(t=50, b=10),
    )

    # ── Distribuição de compliance ────────────────────────────
    if "complianceState" in df.columns:
        comp_dist = df["complianceState"].value_counts().reset_index()
        comp_dist.columns = ["Estado", "Total"]
        fig_compliance = apply_dark(px.bar(
            comp_dist, x="Estado", y="Total",
            title="Distribuição de Compliance",
            color="Estado",
            color_discrete_map=COMPLIANCE_COLORS,
            labels={"Total": "Dispositivos"},
        ))
        fig_compliance.update_layout(showlegend=False)
    else:
        fig_compliance = apply_dark(go.Figure())

    # ── Compliance por plataforma ─────────────────────────────
    if "complianceState" in df.columns and "operatingSystem" in df.columns:
        plat_comp = (
            df.groupby(["operatingSystem", "complianceState"])
            .size().reset_index(name="Total")
        )
        fig_plat_comp = apply_dark(px.bar(
            plat_comp, x="operatingSystem", y="Total", color="complianceState",
            title="Compliance por Plataforma",
            labels={"operatingSystem": "Plataforma", "complianceState": "Estado"},
            color_discrete_map=COMPLIANCE_COLORS,
            barmode="stack",
        ))
    else:
        fig_plat_comp = apply_dark(go.Figure())

    # ── Tabela de dispositivos com risco ──────────────────────
    risk_df   = df[df["complianceState"] != "compliant"].copy() if "complianceState" in df.columns else df.copy()
    risk_cols = ["deviceName", "operatingSystem", "osVersion", "userDisplayName",
                 "complianceState", "isEncrypted", "jailBroken", "lastSyncDateTime"]
    risk_cols  = [c for c in risk_cols if c in risk_df.columns]
    risk_table = risk_df[risk_cols].copy()

    if "lastSyncDateTime" in risk_table.columns:
        risk_table["lastSyncDateTime"] = risk_table["lastSyncDateTime"].dt.strftime("%Y-%m-%d")
    if "isEncrypted" in risk_table.columns:
        risk_table["isEncrypted"] = risk_table["isEncrypted"].map(
            {True: "Sim", False: "Não", None: "Desconhecido"}
        ).fillna("Desconhecido")

    return html.Div([
        page_header("Segurança", "bi-shield-check"),

        dbc.Row([
            dbc.Col(kpi_card("Conformes",        compliant,     "success", "bi-patch-check"),       md=3),
            dbc.Col(kpi_card("Não Conformes",    noncompliant,  "danger",  "bi-patch-exclamation"),  md=3),
            dbc.Col(kpi_card("Jailbroken / Root", jailbroken,
                             "danger" if jailbroken    > 0 else "success", "bi-bug"),    md=3),
            dbc.Col(kpi_card("Sem Criptografia", not_encrypted,
                             "danger" if not_encrypted > 0 else "success", "bi-unlock"), md=3),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(chart_card(dcc.Graph(figure=fig_gauge)),      md=5),
            dbc.Col(chart_card(dcc.Graph(figure=fig_compliance)), md=7),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(chart_card(dcc.Graph(figure=fig_plat_comp)), md=12),
        ], className="mb-4"),

        section_title("Dispositivos com Risco", str(len(risk_table)), "danger"),
        dbc.Card(
            dbc.CardBody(
                dash_table.DataTable(
                    data=risk_table.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in risk_table.columns],
                    **TABLE_KWARGS,
                    style_data_conditional=[
                        {"if": {"filter_query": '{complianceState} = "noncompliant"'},
                         "backgroundColor": "rgba(248,81,73,0.08)", "color": "#f85149"},
                        {"if": {"filter_query": '{isEncrypted} = "Não"'},
                         "backgroundColor": "rgba(210,153,34,0.08)", "color": "#d29922"},
                        {"if": {"filter_query": '{jailBroken} = "Jailbroken"'},
                         "backgroundColor": "rgba(248,81,73,0.08)", "color": "#f85149"},
                    ],
                ),
            ),
            style={"backgroundColor": BG_CARD, "border": f"1px solid {BORDER}", "borderRadius": "8px"},
        ),
    ])
