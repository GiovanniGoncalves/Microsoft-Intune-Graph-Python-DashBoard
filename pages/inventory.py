import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices
from pages.components import (
    kpi_card, chart_card, table_card, page_header, section_title,
    apply_theme, PALETTE, TABLE_KWARGS, PRIMARY, SUCCESS, WARNING, DANGER,
    BG_CARD, BORDER, MUTED, TEXT, TEXT_SOFT,
)


def layout() -> html.Div:
    df = get_devices()

    total         = len(df)
    platforms     = df["operatingSystem"].nunique() if "operatingSystem" in df.columns else 0
    manufacturers = df["manufacturer"].nunique()    if "manufacturer"    in df.columns else 0
    compliant     = len(df[df["complianceState"] == "compliant"]) if "complianceState" in df.columns else 0
    compliance_pct = f"{round(compliant / total * 100)}%" if total > 0 else "0%"

    # ── Gráfico: donut por plataforma (estilo DORA) ───────────
    platform_counts = df["operatingSystem"].value_counts().reset_index()
    platform_counts.columns = ["Plataforma", "Total"]

    # Pull no maior segmento (índice 0 = maior valor)
    pull_values = [0.06 if i == 0 else 0 for i in range(len(platform_counts))]

    DONUT_COLORS = ["#1e40af", "#3b82f6", "#f97316", "#10b981", "#a855f7", "#f59e0b"]

    fig_platform = go.Figure(go.Pie(
        labels=platform_counts["Plataforma"],
        values=platform_counts["Total"],
        hole=0.60,
        pull=pull_values,
        marker=dict(
            colors=DONUT_COLORS[:len(platform_counts)],
            line=dict(color="white", width=2),
        ),
        textinfo="label+value",
        textposition="outside",
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig_platform.add_annotation(
        text=f"<b>{total}</b>",
        x=0.5, y=0.55,
        font=dict(size=32, color=TEXT, family="inherit"),
        showarrow=False,
    )
    fig_platform.add_annotation(
        text="Total",
        x=0.5, y=0.40,
        font=dict(size=11, color=MUTED, family="inherit"),
        showarrow=False,
    )
    fig_platform.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.15, font=dict(color=TEXT_SOFT, size=11)),
        margin=dict(t=20, b=50, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        height=300,
    )

    # ── Gráfico: versões de SO ────────────────────────────────
    if "osVersion" in df.columns:
        os_df = (
            df.groupby(["operatingSystem", "osVersion"])
            .size().reset_index(name="Total")
            .sort_values("Total", ascending=False).head(12)
        )
        fig_os = apply_theme(px.bar(
            os_df, x="Total", y="osVersion", color="operatingSystem",
            orientation="h", title=None,
            labels={"osVersion": "Versão", "operatingSystem": "Plataforma", "Total": "Dispositivos"},
            color_discrete_sequence=PALETTE,
        ))
        fig_os.update_layout(yaxis={"categoryorder": "total ascending"}, height=300)
    else:
        fig_os = apply_theme(go.Figure())

    # ── Gráfico: fabricantes ──────────────────────────────────
    if "manufacturer" in df.columns:
        mfr_df = (
            df[df["manufacturer"].notna() & (df["manufacturer"] != "")]
            ["manufacturer"].value_counts().head(8).reset_index()
        )
        mfr_df.columns = ["Fabricante", "Dispositivos"]
        fig_mfr = apply_theme(px.bar(
            mfr_df, x="Dispositivos", y="Fabricante", orientation="h",
            labels={"Fabricante": "", "Dispositivos": "Dispositivos"},
            color="Dispositivos",
            color_continuous_scale=[[0, "#dbeafe"], [1, PRIMARY]],
        ))
        fig_mfr.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=280,
        )
    else:
        fig_mfr = apply_theme(go.Figure())

    # ── Gráfico: ownership ────────────────────────────────────
    if "managedDeviceOwnerType" in df.columns:
        owner_df = df["managedDeviceOwnerType"].value_counts().reset_index()
        owner_df.columns = ["Tipo", "Total"]
        fig_owner = apply_theme(px.pie(
            owner_df, names="Tipo", values="Total",
            color_discrete_sequence=[PRIMARY, "#93c5fd"],
            hole=0.55,
        ))
        fig_owner.update_traces(textposition="inside", textinfo="percent+label")
        fig_owner.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=280,
        )
    else:
        fig_owner = apply_theme(go.Figure())

    # ── Tabela de dispositivos ────────────────────────────────
    table_cols = [
        "deviceName", "operatingSystem", "osVersion", "userDisplayName",
        "complianceState", "manufacturer", "model",
    ]
    table_cols = [c for c in table_cols if c in df.columns]
    table_df   = df[table_cols].head(100).copy()

    return html.Div([
        page_header(
            "Inventário de Dispositivos",
            "Visão completa de todos os dispositivos gerenciados no Intune",
        ),

        # KPI Cards
        dbc.Row([
            dbc.Col(kpi_card(
                "Total de Dispositivos", total,
                color_key="primary", icon="bi-laptop",
                subtitle="Dispositivos cadastrados",
            ), md=3),
            dbc.Col(kpi_card(
                "Compliance", compliance_pct,
                color_key="success", icon="bi-patch-check",
                subtitle=f"{compliant} dispositivos conformes",
            ), md=3),
            dbc.Col(kpi_card(
                "Plataformas", platforms,
                color_key="info", icon="bi-grid-1x2",
                subtitle="Sistemas operacionais ativos",
            ), md=3),
            dbc.Col(kpi_card(
                "Fabricantes", manufacturers,
                color_key="warning", icon="bi-building",
                subtitle="Marcas diferentes",
            ), md=3),
        ], className="mb-4 g-3"),

        # Gráficos linha 1
        dbc.Row([
            dbc.Col(
                chart_card(
                    "Distribuição por Plataforma",
                    dcc.Graph(figure=fig_platform, config={"displayModeBar": False}),
                ),
                md=4,
            ),
            dbc.Col(
                chart_card(
                    "Top 12 — Versões de SO",
                    dcc.Graph(figure=fig_os, config={"displayModeBar": False}),
                ),
                md=8,
            ),
        ], className="mb-4"),

        # Gráficos linha 2
        dbc.Row([
            dbc.Col(
                chart_card(
                    "Top 8 Fabricantes",
                    dcc.Graph(figure=fig_mfr, config={"displayModeBar": False}),
                ),
                md=8,
            ),
            dbc.Col(
                chart_card(
                    "Corporativo vs. BYOD",
                    dcc.Graph(figure=fig_owner, config={"displayModeBar": False}),
                ),
                md=4,
            ),
        ], className="mb-4"),

        # Tabela
        table_card(
            "Lista de Dispositivos",
            dash_table.DataTable(
                data=table_df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in table_df.columns],
                **TABLE_KWARGS,
                style_data_conditional=[
                    {"if": {"filter_query": '{complianceState} = "noncompliant"'},
                     "backgroundColor": "#fef2f2", "color": DANGER},
                    {"if": {"filter_query": '{complianceState} = "compliant"'},
                     "color": SUCCESS},
                ],
            ),
            link_text="Ver Todos",
        ),
    ])
