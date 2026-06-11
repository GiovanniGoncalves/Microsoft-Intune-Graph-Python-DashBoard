from datetime import datetime, timezone, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
from data.cache import get_devices
from pages.components import (
    kpi_card, chart_card, table_card, page_header,
    apply_theme, PALETTE, TABLE_KWARGS,
    PRIMARY, SUCCESS, WARNING, DANGER, MUTED, TEXT, TEXT_SOFT, BORDER,
)


def layout() -> html.Div:
    df  = get_devices()
    now = datetime.now(tz=timezone.utc)

    # ── Métricas ──────────────────────────────────────────────
    if "lastSyncDateTime" in df.columns:
        inactive_df    = df[df["lastSyncDateTime"] < now - timedelta(days=30)].copy()
        inactive_df["dias_sem_sync"] = (now - inactive_df["lastSyncDateTime"]).dt.days.astype(int)
        inactive_count = len(inactive_df)
    else:
        inactive_df    = pd.DataFrame()
        inactive_count = 0

    new_this_week = (
        len(df[df["enrolledDateTime"] >= now - timedelta(days=7)])
        if "enrolledDateTime" in df.columns else 0
    )
    active_platforms = df["operatingSystem"].nunique() if "operatingSystem" in df.columns else 0

    # ── Gráfico: timeline de enrollments ─────────────────────
    if "enrolledDateTime" in df.columns:
        recent = df[df["enrolledDateTime"] >= now - timedelta(days=90)].copy()
        recent["semana"] = recent["enrolledDateTime"].dt.to_period("W").dt.start_time
        timeline = recent.groupby("semana").size().reset_index(name="Enrollments")
        timeline["semana"] = timeline["semana"].dt.strftime("%d/%m")

        fig_enroll = apply_theme(go.Figure())
        fig_enroll.add_trace(go.Scatter(
            x=timeline["semana"], y=timeline["Enrollments"],
            mode="lines",
            fill="tozeroy",
            fillcolor=f"rgba(37,99,235,0.08)",
            line=dict(color=PRIMARY, width=2.5),
            hovertemplate="%{x}: %{y} enrollments<extra></extra>",
        ))
        fig_enroll.update_layout(
            height=260,
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f3f4f6"),
        )
    else:
        fig_enroll = apply_theme(go.Figure())

    # ── Gráfico: top usuários ─────────────────────────────────
    if "userDisplayName" in df.columns:
        top_users = (
            df[df["userDisplayName"].notna()]
            .groupby("userDisplayName").size()
            .sort_values(ascending=False).head(8).reset_index()
        )
        top_users.columns = ["Usuário", "Dispositivos"]
        fig_users = apply_theme(px.bar(
            top_users, x="Dispositivos", y="Usuário", orientation="h",
            color="Dispositivos",
            color_continuous_scale=[[0, "#dbeafe"], [1, PRIMARY]],
        ))
        fig_users.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=260,
        )
    else:
        fig_users = apply_theme(go.Figure())

    # ── Gráfico: tendência por plataforma ─────────────────────
    if "enrolledDateTime" in df.columns and "operatingSystem" in df.columns:
        plat_recent = df[df["enrolledDateTime"] >= now - timedelta(days=90)].copy()
        plat_recent["semana"] = plat_recent["enrolledDateTime"].dt.to_period("W").dt.start_time
        plat_trend  = plat_recent.groupby(["semana", "operatingSystem"]).size().reset_index(name="Count")
        plat_trend["semana"] = plat_trend["semana"].dt.strftime("%d/%m")

        fig_plat_trend = apply_theme(px.line(
            plat_trend, x="semana", y="Count", color="operatingSystem",
            labels={"semana": "", "operatingSystem": "Plataforma"},
            color_discrete_sequence=PALETTE,
            markers=True,
        ))
        fig_plat_trend.update_layout(height=280)
    else:
        fig_plat_trend = apply_theme(go.Figure())

    # ── Tabela de inativos ────────────────────────────────────
    inactive_table_df = pd.DataFrame()
    if not inactive_df.empty:
        cols = ["deviceName", "operatingSystem", "userDisplayName",
                "lastSyncDateTime", "dias_sem_sync", "complianceState"]
        cols = [c for c in cols if c in inactive_df.columns]
        inactive_table_df = inactive_df[cols].copy()
        if "lastSyncDateTime" in inactive_table_df.columns:
            inactive_table_df["lastSyncDateTime"] = (
                inactive_table_df["lastSyncDateTime"].dt.strftime("%d/%m/%Y")
            )
        if "dias_sem_sync" in inactive_table_df.columns:
            inactive_table_df = inactive_table_df.sort_values("dias_sem_sync", ascending=False)

    return html.Div([
        page_header(
            "Operacional",
            "Monitoramento de atividade e enrollments de dispositivos",
        ),

        # KPI Cards
        dbc.Row([
            dbc.Col(kpi_card(
                "Total de Dispositivos", len(df),
                color_key="primary", icon="bi-laptop",
                subtitle="Dispositivos gerenciados",
            ), md=3),
            dbc.Col(kpi_card(
                "Inativos (> 30 dias)", inactive_count,
                color_key="warning", icon="bi-clock-history",
                subtitle="Sem sincronização recente",
            ), md=3),
            dbc.Col(kpi_card(
                "Novos Esta Semana", new_this_week,
                color_key="success", icon="bi-plus-circle",
                subtitle="Enrollments nos últimos 7 dias",
            ), md=3),
            dbc.Col(kpi_card(
                "Plataformas Ativas", active_platforms,
                color_key="info", icon="bi-grid",
                subtitle="Sistemas operacionais em uso",
            ), md=3),
        ], className="mb-4 g-3"),

        # Gráficos linha 1
        dbc.Row([
            dbc.Col(
                chart_card(
                    "Novos Enrollments",
                    dcc.Graph(figure=fig_enroll, config={"displayModeBar": False}),
                    subtitle="Últimos 90 dias",
                ),
                md=7,
            ),
            dbc.Col(
                chart_card(
                    "Top 8 Usuários",
                    dcc.Graph(figure=fig_users, config={"displayModeBar": False}),
                    subtitle="Por quantidade de dispositivos",
                ),
                md=5,
            ),
        ], className="mb-4"),

        # Gráfico linha 2
        dbc.Row([
            dbc.Col(
                chart_card(
                    "Enrollments por Plataforma",
                    dcc.Graph(figure=fig_plat_trend, config={"displayModeBar": False}),
                    subtitle="Últimos 90 dias",
                ),
                md=12,
            ),
        ], className="mb-4"),

        # Tabela de inativos
        table_card(
            f"Dispositivos Inativos",
            dash_table.DataTable(
                data=inactive_table_df.to_dict("records") if not inactive_table_df.empty else [],
                columns=[{"name": c, "id": c} for c in inactive_table_df.columns] if not inactive_table_df.empty else [],
                **TABLE_KWARGS,
                style_data_conditional=[
                    {"if": {"filter_query": "{dias_sem_sync} > 90"},
                     "backgroundColor": "#fef2f2", "color": DANGER},
                    {"if": {"filter_query": "{dias_sem_sync} > 60 && {dias_sem_sync} <= 90"},
                     "backgroundColor": "#fffbeb", "color": WARNING},
                ],
            ),
            link_text=f"{inactive_count} dispositivos",
        ),
    ])
