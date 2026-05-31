from datetime import datetime, timezone, timedelta
import pandas as pd
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
    df  = get_devices()
    now = datetime.now(tz=timezone.utc)

    # ── Dispositivos inativos (> 30 dias sem sync) ────────────
    if "lastSyncDateTime" in df.columns:
        cutoff_30   = now - timedelta(days=30)
        inactive_df = df[df["lastSyncDateTime"] < cutoff_30].copy()
        inactive_df["dias_sem_sync"] = (now - inactive_df["lastSyncDateTime"]).dt.days.astype(int)
        inactive_count = len(inactive_df)
    else:
        inactive_df    = pd.DataFrame()
        inactive_count = 0

    # ── Novos enrollments esta semana ─────────────────────────
    if "enrolledDateTime" in df.columns:
        new_this_week = len(df[df["enrolledDateTime"] >= (now - timedelta(days=7))])
    else:
        new_this_week = 0

    # ── Gráfico: timeline de enrollments (90 dias) ────────────
    if "enrolledDateTime" in df.columns:
        recent = df[df["enrolledDateTime"] >= (now - timedelta(days=90))].copy()
        recent["semana"] = recent["enrolledDateTime"].dt.to_period("W").dt.start_time
        timeline = recent.groupby("semana").size().reset_index(name="Enrollments")
        timeline["semana"] = timeline["semana"].dt.strftime("%Y-%m-%d")
        fig_enroll = apply_dark(px.bar(
            timeline, x="semana", y="Enrollments",
            title="Novos Enrollments — Últimos 90 dias",
            labels={"semana": "Semana"},
            color_discrete_sequence=["#58a6ff"],
        ))
    else:
        fig_enroll = apply_dark(go.Figure())

    # ── Gráfico: top 10 usuários ──────────────────────────────
    if "userDisplayName" in df.columns:
        top_users = (
            df[df["userDisplayName"].notna()]
            .groupby("userDisplayName").size()
            .sort_values(ascending=False).head(10).reset_index()
        )
        top_users.columns = ["Usuário", "Dispositivos"]
        fig_users = apply_dark(px.bar(
            top_users, x="Dispositivos", y="Usuário", orientation="h",
            title="Top 10 Usuários por Dispositivos",
            color="Dispositivos",
            color_continuous_scale=[[0, "#1c2128"], [1, "#3fb950"]],
        ))
        fig_users.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig_users = apply_dark(go.Figure())

    # ── Gráfico: tendência por plataforma (90 dias) ───────────
    if "enrolledDateTime" in df.columns and "operatingSystem" in df.columns:
        plat_recent = df[df["enrolledDateTime"] >= (now - timedelta(days=90))].copy()
        plat_recent["semana"] = plat_recent["enrolledDateTime"].dt.to_period("W").dt.start_time
        plat_trend  = plat_recent.groupby(["semana", "operatingSystem"]).size().reset_index(name="Count")
        plat_trend["semana"] = plat_trend["semana"].dt.strftime("%Y-%m-%d")
        fig_plat_trend = apply_dark(px.line(
            plat_trend, x="semana", y="Count", color="operatingSystem",
            title="Enrollments por Plataforma — Últimos 90 dias",
            labels={"semana": "Semana", "operatingSystem": "Plataforma"},
            color_discrete_sequence=PALETTE,
            markers=True,
        ))
    else:
        fig_plat_trend = apply_dark(go.Figure())

    # ── Tabela de dispositivos inativos ───────────────────────
    inactive_table_df = pd.DataFrame()
    if not inactive_df.empty:
        cols = ["deviceName", "operatingSystem", "userDisplayName",
                "lastSyncDateTime", "dias_sem_sync", "complianceState"]
        cols = [c for c in cols if c in inactive_df.columns]
        inactive_table_df = inactive_df[cols].copy()
        if "lastSyncDateTime" in inactive_table_df.columns:
            inactive_table_df["lastSyncDateTime"] = (
                inactive_table_df["lastSyncDateTime"].dt.strftime("%Y-%m-%d")
            )
        if "dias_sem_sync" in inactive_table_df.columns:
            inactive_table_df = inactive_table_df.sort_values("dias_sem_sync", ascending=False)

    return html.Div([
        page_header("Operacional", "bi-activity"),

        dbc.Row([
            dbc.Col(kpi_card("Total de Dispositivos", len(df),        "primary", "bi-laptop"),       md=3),
            dbc.Col(kpi_card("Inativos (> 30 dias)",  inactive_count, "warning", "bi-clock-history"), md=3),
            dbc.Col(kpi_card("Novos Esta Semana",      new_this_week,  "success", "bi-plus-circle"),   md=3),
            dbc.Col(kpi_card(
                "Plataformas Ativas",
                df["operatingSystem"].nunique() if "operatingSystem" in df.columns else 0,
                "info", "bi-grid",
            ), md=3),
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col(chart_card(dcc.Graph(figure=fig_enroll)), md=7),
            dbc.Col(chart_card(dcc.Graph(figure=fig_users)),  md=5),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(chart_card(dcc.Graph(figure=fig_plat_trend)), md=12),
        ], className="mb-4"),

        section_title("Dispositivos Inativos", str(inactive_count), "warning"),
        dbc.Card(
            dbc.CardBody(
                dash_table.DataTable(
                    data=inactive_table_df.to_dict("records") if not inactive_table_df.empty else [],
                    columns=[{"name": c, "id": c} for c in inactive_table_df.columns] if not inactive_table_df.empty else [],
                    **TABLE_KWARGS,
                    style_data_conditional=[
                        {"if": {"filter_query": "{dias_sem_sync} > 90"},
                         "backgroundColor": "rgba(248,81,73,0.08)", "color": "#f85149"},
                        {"if": {"filter_query": "{dias_sem_sync} > 60 && {dias_sem_sync} <= 90"},
                         "backgroundColor": "rgba(210,153,34,0.08)", "color": "#d29922"},
                    ],
                ),
            ),
            style={"backgroundColor": BG_CARD, "border": f"1px solid {BORDER}", "borderRadius": "8px"},
        ),
    ])
