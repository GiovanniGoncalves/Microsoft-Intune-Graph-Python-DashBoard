import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices


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
    platforms = df["operatingSystem"].nunique() if "operatingSystem" in df.columns else 0
    manufacturers = df["manufacturer"].nunique() if "manufacturer" in df.columns else 0

    # Platform pie
    platform_counts = df["operatingSystem"].value_counts().reset_index()
    platform_counts.columns = ["Plataforma", "Total"]
    fig_platform = px.pie(
        platform_counts, names="Plataforma", values="Total",
        title="Distribuição por Plataforma",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    fig_platform.update_traces(textposition="inside", textinfo="percent+label")
    fig_platform.update_layout(showlegend=True, margin=dict(t=50, b=10))

    # OS Version bar (top 15)
    if "osVersion" in df.columns:
        os_df = df.groupby(["operatingSystem", "osVersion"]).size().reset_index(name="Total")
        os_df = os_df.sort_values("Total", ascending=False).head(15)
        fig_os = px.bar(
            os_df, x="Total", y="osVersion", color="operatingSystem",
            orientation="h", title="Versões de SO (Top 15)",
            labels={"osVersion": "Versão", "operatingSystem": "Plataforma", "Total": "Dispositivos"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_os.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50, b=10))
    else:
        fig_os = go.Figure()

    # Manufacturer bar (top 10)
    if "manufacturer" in df.columns:
        mfr_df = (
            df[df["manufacturer"].notna() & (df["manufacturer"] != "")]
            ["manufacturer"].value_counts().head(10).reset_index()
        )
        mfr_df.columns = ["Fabricante", "Dispositivos"]
        fig_mfr = px.bar(
            mfr_df, x="Dispositivos", y="Fabricante", orientation="h",
            title="Top 10 Fabricantes", color="Dispositivos",
            color_continuous_scale="Blues",
        )
        fig_mfr.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50, b=10))
    else:
        fig_mfr = go.Figure()

    # Ownership type distribution
    if "managedDeviceOwnerType" in df.columns:
        owner_df = df["managedDeviceOwnerType"].value_counts().reset_index()
        owner_df.columns = ["Tipo", "Total"]
        fig_owner = px.pie(
            owner_df, names="Tipo", values="Total",
            title="Corporativo vs. Pessoal (BYOD)",
            color_discrete_sequence=["#0d6efd", "#6c757d"],
            hole=0.4,
        )
        fig_owner.update_traces(textposition="inside", textinfo="percent+label")
        fig_owner.update_layout(showlegend=True, margin=dict(t=50, b=10))
    else:
        fig_owner = go.Figure()

    # Device table
    table_cols = ["deviceName", "operatingSystem", "osVersion", "userDisplayName", "complianceState", "managementState", "manufacturer", "model", "deviceCategoryDisplayName"]
    table_cols = [c for c in table_cols if c in df.columns]
    table_df = df[table_cols].copy()

    return html.Div([
        html.H4("Inventário de Dispositivos", className="mb-4 fw-bold"),

        dbc.Row([
            dbc.Col(_kpi("Total de Dispositivos", total, "primary"), md=4),
            dbc.Col(_kpi("Plataformas", platforms, "info"), md=4),
            dbc.Col(_kpi("Fabricantes", manufacturers, "success"), md=4),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_platform), md=4),
            dbc.Col(dcc.Graph(figure=fig_os), md=8),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_mfr), md=8),
            dbc.Col(dcc.Graph(figure=fig_owner), md=4),
        ], className="mb-4"),

        html.H5("Todos os Dispositivos", className="mb-3 fw-semibold"),
        dash_table.DataTable(
            data=table_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in table_df.columns],
            filter_action="native",
            sort_action="native",
            page_size=20,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px", "fontSize": "13px"},
            style_header={"backgroundColor": "#343a40", "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": '{complianceState} = "noncompliant"'}, "backgroundColor": "#fff3cd"},
            ],
        ),
    ])
