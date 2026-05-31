import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices
from pages.components import (
    kpi_card, chart_card, page_header, section_title,
    apply_dark, PALETTE, TABLE_KWARGS, BG_CARD, BORDER,
)


def layout() -> html.Div:
    df = get_devices()

    total         = len(df)
    platforms     = df["operatingSystem"].nunique() if "operatingSystem" in df.columns else 0
    manufacturers = df["manufacturer"].nunique()    if "manufacturer"    in df.columns else 0

    # ── Gráfico: distribuição por plataforma ──────────────────
    platform_counts = df["operatingSystem"].value_counts().reset_index()
    platform_counts.columns = ["Plataforma", "Total"]
    fig_platform = apply_dark(px.pie(
        platform_counts, names="Plataforma", values="Total",
        title="Distribuição por Plataforma",
        color_discrete_sequence=PALETTE,
        hole=0.45,
    ))
    fig_platform.update_traces(textposition="inside", textinfo="percent+label")
    fig_platform.update_layout(showlegend=True)

    # ── Gráfico: versões de SO (top 15) ───────────────────────
    if "osVersion" in df.columns:
        os_df = (
            df.groupby(["operatingSystem", "osVersion"])
            .size().reset_index(name="Total")
            .sort_values("Total", ascending=False).head(15)
        )
        fig_os = apply_dark(px.bar(
            os_df, x="Total", y="osVersion", color="operatingSystem",
            orientation="h", title="Versões de SO — Top 15",
            labels={"osVersion": "Versão", "operatingSystem": "Plataforma", "Total": "Dispositivos"},
            color_discrete_sequence=PALETTE,
        ))
        fig_os.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig_os = apply_dark(go.Figure())

    # ── Gráfico: top 10 fabricantes ───────────────────────────
    if "manufacturer" in df.columns:
        mfr_df = (
            df[df["manufacturer"].notna() & (df["manufacturer"] != "")]
            ["manufacturer"].value_counts().head(10).reset_index()
        )
        mfr_df.columns = ["Fabricante", "Dispositivos"]
        fig_mfr = apply_dark(px.bar(
            mfr_df, x="Dispositivos", y="Fabricante", orientation="h",
            title="Top 10 Fabricantes",
            color="Dispositivos",
            color_continuous_scale=[[0, "#1c2128"], [1, "#58a6ff"]],
        ))
        fig_mfr.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig_mfr = apply_dark(go.Figure())

    # ── Gráfico: tipo de propriedade ──────────────────────────
    if "managedDeviceOwnerType" in df.columns:
        owner_df = df["managedDeviceOwnerType"].value_counts().reset_index()
        owner_df.columns = ["Tipo", "Total"]
        fig_owner = apply_dark(px.pie(
            owner_df, names="Tipo", values="Total",
            title="Corporativo vs. Pessoal (BYOD)",
            color_discrete_sequence=["#58a6ff", "#7d8590"],
            hole=0.45,
        ))
        fig_owner.update_traces(textposition="inside", textinfo="percent+label")
    else:
        fig_owner = apply_dark(go.Figure())

    # ── Tabela de dispositivos ────────────────────────────────
    table_cols = [
        "deviceName", "operatingSystem", "osVersion", "userDisplayName",
        "complianceState", "managementState", "manufacturer", "model",
        "deviceCategoryDisplayName",
    ]
    table_cols = [c for c in table_cols if c in df.columns]
    table_df   = df[table_cols].copy()

    return html.Div([
        page_header("Inventário de Dispositivos", "bi-box-seam"),

        dbc.Row([
            dbc.Col(kpi_card("Total de Dispositivos", total,         "primary", "bi-laptop"),   md=4),
            dbc.Col(kpi_card("Plataformas",           platforms,     "info",    "bi-grid"),      md=4),
            dbc.Col(kpi_card("Fabricantes",           manufacturers, "success", "bi-building"),  md=4),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(chart_card(dcc.Graph(figure=fig_platform)), md=4),
            dbc.Col(chart_card(dcc.Graph(figure=fig_os)),       md=8),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(chart_card(dcc.Graph(figure=fig_mfr)),   md=8),
            dbc.Col(chart_card(dcc.Graph(figure=fig_owner)), md=4),
        ], className="mb-4"),

        section_title("Todos os Dispositivos"),
        dbc.Card(
            dbc.CardBody(
                dash_table.DataTable(
                    data=table_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in table_df.columns],
                    **TABLE_KWARGS,
                    style_data_conditional=[
                        {"if": {"filter_query": '{complianceState} = "noncompliant"'},
                         "backgroundColor": "rgba(248,81,73,0.08)", "color": "#f85149"},
                    ],
                ),
            ),
            style={"backgroundColor": BG_CARD, "border": f"1px solid {BORDER}", "borderRadius": "8px"},
        ),
    ])
