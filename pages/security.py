import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices
from pages.components import (
    kpi_card, chart_card, table_card, page_header,
    apply_theme, TABLE_KWARGS,
    PRIMARY, SUCCESS, WARNING, DANGER, MUTED, TEXT, TEXT_SOFT, BORDER, _hex_to_rgb,
)

COMPLIANCE_COLORS = {
    "compliant":     SUCCESS,
    "noncompliant":  DANGER,
    "inGracePeriod": WARNING,
    "error":         DANGER,
    "conflict":      "#f97316",
    "unknown":       "#9ca3af",
    "configManager": "#6366f1",
}


def layout() -> html.Div:
    df    = get_devices()
    total = len(df)

    compliant      = len(df[df["complianceState"] == "compliant"])    if "complianceState" in df.columns else 0
    noncompliant   = len(df[df["complianceState"] == "noncompliant"]) if "complianceState" in df.columns else 0
    compliance_pct = round(compliant / total * 100, 1) if total > 0 else 0

    jailbroken    = len(df[df["jailBroken"]  == "Jailbroken"]) if "jailBroken"  in df.columns else 0
    not_encrypted = len(df[df["isEncrypted"] == False])        if "isEncrypted" in df.columns else 0

    # ── Gauge de compliance ───────────────────────────────────
    gauge_color = SUCCESS if compliance_pct >= 80 else (WARNING if compliance_pct >= 60 else DANGER)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=compliance_pct,
        number={"font": {"color": gauge_color, "size": 42}, "suffix": "%"},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#e5e7eb",
                     "tickfont": {"color": MUTED, "size": 11}},
            "bar": {"color": gauge_color, "thickness": 0.25},
            "bgcolor": "#f9fafb",
            "bordercolor": "#e5e7eb",
            "borderwidth": 1,
            "steps": [
                {"range": [0,  60], "color": f"rgba({_hex_to_rgb(DANGER)},0.08)"},
                {"range": [60, 80], "color": f"rgba({_hex_to_rgb(WARNING)},0.08)"},
                {"range": [80, 100], "color": f"rgba({_hex_to_rgb(SUCCESS)},0.08)"},
            ],
            "threshold": {
                "line": {"color": DANGER, "width": 2},
                "thickness": 0.8,
                "value": 90,
            },
        },
    ))
    fig_gauge.update_layout(
        height=260,
        margin=dict(t=30, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SOFT),
        annotations=[{
            "text": "Meta: 90%",
            "x": 0.5, "y": -0.02,
            "showarrow": False,
            "font": {"size": 11, "color": MUTED},
        }],
    )

    # ── Distribuição de compliance (donut) ────────────────────
    if "complianceState" in df.columns:
        comp_dist = df["complianceState"].value_counts().reset_index()
        comp_dist.columns = ["Estado", "Total"]
        colors    = [COMPLIANCE_COLORS.get(s, "#9ca3af") for s in comp_dist["Estado"]]

        fig_compliance = go.Figure(go.Pie(
            labels=comp_dist["Estado"],
            values=comp_dist["Total"],
            hole=0.60,
            marker=dict(colors=colors),
            textinfo="label+percent",
            textposition="outside",
            hovertemplate="%{label}: %{value}<extra></extra>",
        ))
        fig_compliance.update_layout(
            showlegend=False,
            margin=dict(t=20, b=30, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            height=260,
        )
    else:
        fig_compliance = apply_theme(go.Figure())

    # ── Compliance por plataforma (stacked bar) ───────────────
    if "complianceState" in df.columns and "operatingSystem" in df.columns:
        plat_comp = (
            df.groupby(["operatingSystem", "complianceState"])
            .size().reset_index(name="Total")
        )
        fig_plat = apply_theme(px.bar(
            plat_comp, x="operatingSystem", y="Total", color="complianceState",
            labels={"operatingSystem": "Plataforma", "complianceState": "Estado"},
            color_discrete_map=COMPLIANCE_COLORS,
            barmode="stack",
        ))
        fig_plat.update_layout(height=280)
    else:
        fig_plat = apply_theme(go.Figure())

    # ── Tabela de risco ───────────────────────────────────────
    risk_df   = df[df["complianceState"] != "compliant"].copy() if "complianceState" in df.columns else df.copy()
    risk_cols = ["deviceName", "operatingSystem", "osVersion", "userDisplayName",
                 "complianceState", "isEncrypted", "jailBroken", "lastSyncDateTime"]
    risk_cols  = [c for c in risk_cols if c in risk_df.columns]
    risk_table = risk_df[risk_cols].copy()

    if "lastSyncDateTime" in risk_table.columns:
        risk_table["lastSyncDateTime"] = risk_table["lastSyncDateTime"].dt.strftime("%d/%m/%Y")
    if "isEncrypted" in risk_table.columns:
        risk_table["isEncrypted"] = risk_table["isEncrypted"].map(
            {True: "✓ Sim", False: "✗ Não", None: "—"}
        ).fillna("—")

    return html.Div([
        page_header(
            "Segurança",
            "Compliance, criptografia e riscos de segurança dos dispositivos",
        ),

        # KPI Cards
        dbc.Row([
            dbc.Col(kpi_card(
                "Conformes", compliant,
                color_key="success", icon="bi-patch-check",
                subtitle=f"{compliance_pct}% do total",
            ), md=3),
            dbc.Col(kpi_card(
                "Não Conformes", noncompliant,
                color_key="danger", icon="bi-patch-exclamation",
                subtitle="Requerem atenção imediata",
            ), md=3),
            dbc.Col(kpi_card(
                "Jailbroken / Root", jailbroken,
                color_key="danger" if jailbroken > 0 else "success",
                icon="bi-bug",
                subtitle="Dispositivos comprometidos",
            ), md=3),
            dbc.Col(kpi_card(
                "Sem Criptografia", not_encrypted,
                color_key="danger" if not_encrypted > 0 else "success",
                icon="bi-unlock",
                subtitle="Dados em risco",
            ), md=3),
        ], className="mb-4 g-3"),

        # Gráficos linha 1
        dbc.Row([
            dbc.Col(
                chart_card(
                    "Compliance Geral",
                    dcc.Graph(figure=fig_gauge, config={"displayModeBar": False}),
                ),
                md=4,
            ),
            dbc.Col(
                chart_card(
                    "Distribuição de Compliance",
                    dcc.Graph(figure=fig_compliance, config={"displayModeBar": False}),
                ),
                md=4,
            ),
            dbc.Col(
                # Card de resumo de riscos
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Resumo de Riscos", className="fw-semibold mb-3",
                                style={"color": TEXT, "fontSize": "14px"}),
                        *[
                            html.Div([
                                html.Div([
                                    html.I(className=f"bi {icon} me-2",
                                           style={"color": color, "fontSize": "1rem"}),
                                    html.Span(label, style={"color": TEXT_SOFT, "fontSize": "13px"}),
                                ], className="d-flex align-items-center"),
                                html.Span(str(value), style={
                                    "color": color,
                                    "fontWeight": "700",
                                    "fontSize": "1.1rem",
                                }),
                            ], className="d-flex justify-content-between align-items-center mb-3")
                            for label, value, color, icon in [
                                ("Não Conformes",    noncompliant,   DANGER,   "bi-exclamation-circle"),
                                ("Jailbroken",       jailbroken,     DANGER,   "bi-bug"),
                                ("Sem Criptografia", not_encrypted,  WARNING,  "bi-unlock"),
                                ("Conformes",        compliant,      SUCCESS,  "bi-check-circle"),
                            ]
                        ],
                    ]),
                ], style={
                    "backgroundColor": "#ffffff",
                    "border": f"1px solid {BORDER}",
                    "borderRadius": "12px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
                    "height": "100%",
                }),
                md=4,
            ),
        ], className="mb-4"),

        # Gráfico compliance por plataforma
        dbc.Row([
            dbc.Col(
                chart_card(
                    "Compliance por Plataforma",
                    dcc.Graph(figure=fig_plat, config={"displayModeBar": False}),
                ),
                md=12,
            ),
        ], className="mb-4"),

        # Tabela de risco
        table_card(
            "Dispositivos com Risco",
            dash_table.DataTable(
                data=risk_table.to_dict("records"),
                columns=[{"name": c, "id": c} for c in risk_table.columns],
                **TABLE_KWARGS,
                style_data_conditional=[
                    {"if": {"filter_query": '{complianceState} = "noncompliant"'},
                     "backgroundColor": "#fef2f2", "color": DANGER},
                    {"if": {"filter_query": '{isEncrypted} = "✗ Não"'},
                     "backgroundColor": "#fffbeb", "color": WARNING},
                    {"if": {"filter_query": '{jailBroken} = "Jailbroken"'},
                     "backgroundColor": "#fef2f2", "color": DANGER},
                ],
            ),
            link_text=f"{len(risk_table)} dispositivos",
        ),
    ])
