from datetime import datetime, timezone, timedelta
import pandas as pd
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
    now = datetime.now(tz=timezone.utc)

    # Inactive devices (no sync > 30 days)
    if "lastSyncDateTime" in df.columns:
        cutoff_30 = now - timedelta(days=30)
        inactive_df = df[df["lastSyncDateTime"] < cutoff_30].copy()
        inactive_df["dias_sem_sync"] = (now - inactive_df["lastSyncDateTime"]).dt.days.astype(int)
        inactive_count = len(inactive_df)
    else:
        inactive_df = pd.DataFrame()
        inactive_count = 0

    # New enrollments this week
    if "enrolledDateTime" in df.columns:
        new_this_week = len(df[df["enrolledDateTime"] >= (now - timedelta(days=7))])
    else:
        new_this_week = 0

    # Enrollment timeline (last 90 days, by week)
    if "enrolledDateTime" in df.columns:
        recent = df[df["enrolledDateTime"] >= (now - timedelta(days=90))].copy()
        recent["semana"] = recent["enrolledDateTime"].dt.to_period("W").dt.start_time
        timeline = recent.groupby("semana").size().reset_index(name="Enrollments")
        timeline["semana"] = timeline["semana"].dt.strftime("%Y-%m-%d")
        fig_enroll = px.bar(
            timeline, x="semana", y="Enrollments",
            title="Novos Enrollments — Últimos 90 dias",
            labels={"semana": "Semana"},
            color_discrete_sequence=["#0d6efd"],
        )
        fig_enroll.update_layout(margin=dict(t=50, b=10))
    else:
        fig_enroll = go.Figure()

    # Top users by device count
    if "userDisplayName" in df.columns:
        top_users = (
            df[df["userDisplayName"].notna()]
            .groupby("userDisplayName").size()
            .sort_values(ascending=False).head(10).reset_index()
        )
        top_users.columns = ["Usuário", "Dispositivos"]
        fig_users = px.bar(
            top_users, x="Dispositivos", y="Usuário", orientation="h",
            title="Top 10 Usuários por Dispositivos",
            color="Dispositivos", color_continuous_scale="Teal",
        )
        fig_users.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=50, b=10))
    else:
        fig_users = go.Figure()

    # Platform trend (last 90 days enrollments by OS)
    if "enrolledDateTime" in df.columns and "operatingSystem" in df.columns:
        plat_recent = df[df["enrolledDateTime"] >= (now - timedelta(days=90))].copy()
        plat_recent["semana"] = plat_recent["enrolledDateTime"].dt.to_period("W").dt.start_time
        plat_trend = plat_recent.groupby(["semana", "operatingSystem"]).size().reset_index(name="Count")
        plat_trend["semana"] = plat_trend["semana"].dt.strftime("%Y-%m-%d")
        fig_plat_trend = px.line(
            plat_trend, x="semana", y="Count", color="operatingSystem",
            title="Enrollments por Plataforma — Últimos 90 dias",
            labels={"semana": "Semana", "operatingSystem": "Plataforma"},
            color_discrete_sequence=px.colors.qualitative.Set2,
            markers=True,
        )
        fig_plat_trend.update_layout(margin=dict(t=50, b=10))
    else:
        fig_plat_trend = go.Figure()

    # Inactive table
    inactive_table_df = pd.DataFrame()
    if not inactive_df.empty:
        cols = ["deviceName", "operatingSystem", "userDisplayName", "lastSyncDateTime", "dias_sem_sync", "complianceState"]
        cols = [c for c in cols if c in inactive_df.columns]
        inactive_table_df = inactive_df[cols].copy()
        if "lastSyncDateTime" in inactive_table_df.columns:
            inactive_table_df["lastSyncDateTime"] = inactive_table_df["lastSyncDateTime"].dt.strftime("%Y-%m-%d")
        if "dias_sem_sync" in inactive_table_df.columns:
            inactive_table_df = inactive_table_df.sort_values("dias_sem_sync", ascending=False)

    return html.Div([
        html.H4("Operacional", className="mb-4 fw-bold"),

        dbc.Row([
            dbc.Col(_kpi("Total de Dispositivos", len(df), "primary"), md=3),
            dbc.Col(_kpi("Inativos (> 30 dias)", inactive_count, "warning"), md=3),
            dbc.Col(_kpi("Novos Esta Semana", new_this_week, "success"), md=3),
            dbc.Col(_kpi("Plataformas Ativas", df["operatingSystem"].nunique() if "operatingSystem" in df.columns else 0, "info"), md=3),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_enroll), md=7),
            dbc.Col(dcc.Graph(figure=fig_users), md=5),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_plat_trend), md=12),
        ], className="mb-4"),

        html.H5(f"Dispositivos Inativos ({inactive_count})", className="mb-3 fw-semibold text-warning"),
        dash_table.DataTable(
            data=inactive_table_df.to_dict("records") if not inactive_table_df.empty else [],
            columns=[{"name": c, "id": c} for c in inactive_table_df.columns] if not inactive_table_df.empty else [],
            sort_action="native",
            filter_action="native",
            page_size=15,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px", "fontSize": "13px"},
            style_header={"backgroundColor": "#343a40", "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": "{dias_sem_sync} > 90"}, "backgroundColor": "#f8d7da"},
                {"if": {"filter_query": "{dias_sem_sync} > 60 && {dias_sem_sync} <= 90"}, "backgroundColor": "#fff3cd"},
            ],
        ),
    ])
