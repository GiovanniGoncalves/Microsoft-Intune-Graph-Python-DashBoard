import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
from data.cache import get_inventory


def _kpi(title: str, value, color: str = "primary") -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted small"),
            html.H2(str(value), className=f"text-{color} fw-bold mb-0"),
        ]),
        className="shadow-sm text-center h-100",
    )


def layout() -> html.Div:
    df = get_inventory()

    android = df[df["OS"].str.contains("Android", case=False, na=False)].copy()

    total = len(android)
    with_loja = android[android["loja"].notna()]
    without_loja = android[android["loja"].isna()]
    lojas_count = android["loja"].nunique()

    # Devices per store bar chart
    store_dist = with_loja["loja"].value_counts().reset_index()
    store_dist.columns = ["Loja", "Dispositivos"]
    fig_stores = px.bar(
        store_dist, x="Loja", y="Dispositivos",
        title=f"Dispositivos por Loja ({len(store_dist)} lojas)",
        color="Dispositivos", color_continuous_scale="Blues",
    )
    fig_stores.update_layout(
        xaxis_tickangle=-45, margin=dict(t=50, b=80),
        xaxis={"categoryorder": "total descending"},
    )

    # Top 20 lojas horizontal bar
    top20 = store_dist.head(20)
    fig_top20 = px.bar(
        top20, x="Dispositivos", y="Loja", orientation="h",
        title="Top 20 Lojas por Quantidade",
        color="Dispositivos", color_continuous_scale="Teal",
    )
    fig_top20.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50, b=10))

    # Compliance by store (top 15)
    if "Compliance" in android.columns:
        comp_store = (
            with_loja.groupby(["loja", "Compliance"])
            .size().reset_index(name="Total")
        )
        top15_lojas = store_dist.head(15)["Loja"].tolist()
        comp_store_top = comp_store[comp_store["loja"].isin(top15_lojas)]
        fig_compliance = px.bar(
            comp_store_top, x="loja", y="Total", color="Compliance",
            title="Compliance por Loja (Top 15)", barmode="stack",
            color_discrete_map={
                "Compliant": "#198754", "Noncompliant": "#dc3545",
                "InGracePeriod": "#ffc107", "Unknown": "#6c757d",
            },
        )
        fig_compliance.update_layout(xaxis_tickangle=-45, margin=dict(t=50, b=80))
    else:
        fig_compliance = go.Figure()

    # Table: devices without store match
    no_loja_cols = ["Device name", "OS", "WiFiIPv4Address", "Serial number", "Primary user UPN"]
    no_loja_cols = [c for c in no_loja_cols if c in without_loja.columns]
    no_loja_table = without_loja[no_loja_cols].copy() if not without_loja.empty else pd.DataFrame()

    # Full store detail table
    detail_cols = ["Device name", "loja", "WiFiIPv4Address", "OS", "Compliance",
                   "Last check-in", "Serial number", "Primary user UPN", "Model", "Manufacturer"]
    detail_cols = [c for c in detail_cols if c in android.columns]
    detail_df = with_loja[detail_cols].copy()
    if "Last check-in" in detail_df.columns:
        detail_df["Last check-in"] = pd.to_datetime(
            detail_df["Last check-in"], errors="coerce", utc=True
        ).dt.strftime("%Y-%m-%d")

    return html.Div([
        html.H4("Localização por Loja", className="mb-4 fw-bold"),

        dbc.Row([
            dbc.Col(_kpi("Total Android", total, "primary"), md=3),
            dbc.Col(_kpi("Lojas Identificadas", lojas_count, "success"), md=3),
            dbc.Col(_kpi("Com Loja", len(with_loja), "info"), md=3),
            dbc.Col(_kpi("Sem Loja (IP fora range)", len(without_loja), "warning"), md=3),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_top20), md=6),
            dbc.Col(dcc.Graph(figure=fig_compliance), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_stores), md=12),
        ], className="mb-4"),

        html.H5("Detalhamento por Loja", className="mb-3 fw-semibold"),
        dash_table.DataTable(
            data=detail_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in detail_df.columns],
            filter_action="native",
            sort_action="native",
            page_size=20,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px", "fontSize": "13px"},
            style_header={"backgroundColor": "#343a40", "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": '{ComplianceState} = "Noncompliant"'},
                 "backgroundColor": "#f8d7da"},
            ],
        ),

        html.H5(f"Devices Sem Loja Identificada ({len(no_loja_table)})",
                className="mb-3 mt-4 fw-semibold text-warning"),
        dash_table.DataTable(
            data=no_loja_table.to_dict("records") if not no_loja_table.empty else [],
            columns=[{"name": c, "id": c} for c in no_loja_table.columns],
            sort_action="native",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px", "fontSize": "13px"},
            style_header={"backgroundColor": "#343a40", "color": "white", "fontWeight": "bold"},
        ),
    ])
