"""Página Aplicativos — versionamento e adoção dos apps rastreados.

Catálogo (cards por app) no topo + drill de distribuição de versões ao
selecionar um app. Cobre os apps configurados em TRACKED_APPS.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc

from data.cache import get_stores_master
from data.app_inventory import TRACKED_APPS, _version_key
from pages.components import (
    kpi_card, page_header, apply_theme, TABLE_KWARGS,
    PRIMARY, SUCCESS, WARNING, DANGER, MUTED, TEXT, BG_CARD, BORDER,
)

APP_LABELS = list(TRACKED_APPS.values())
LABEL_TO_PKG = {v: k for k, v in TRACKED_APPS.items()}
PUBLISHER = "C&A Modas SA"


def _app_stats(df: pd.DataFrame, label: str) -> dict:
    ver_col, status_col = f"{label}_version", f"{label}_status"
    installed = df[df[ver_col].notna()] if ver_col in df.columns else df.iloc[0:0]
    total = len(installed)
    atual = int((df[status_col] == "Atualizado").sum()) if status_col in df.columns else 0
    desat = int((df[status_col] == "Desatualizado").sum()) if status_col in df.columns else 0
    pct = round(atual / total * 100) if total else 0
    latest = None
    if total and status_col in installed.columns:
        latest_rows = installed[installed[status_col] == "Atualizado"][ver_col].dropna()
        latest = latest_rows.iloc[0] if not latest_rows.empty else None
    n_versions = installed[ver_col].nunique() if total else 0
    return {
        "label": label, "total": total, "atual": atual, "desat": desat,
        "pct": pct, "latest": latest, "n_versions": n_versions,
    }


def _app_catalog_card(s: dict) -> dbc.Card:
    pct_color = SUCCESS if s["pct"] >= 80 else (WARNING if s["pct"] >= 50 else DANGER)
    return dbc.Card(dbc.CardBody([
        html.Div([
            html.Div([
                html.I(className="bi bi-google-play",
                       style={"color": "#10b981", "fontSize": "1.4rem", "marginRight": "10px"}),
                html.Div([
                    html.H6(s["label"], className="mb-0 fw-semibold",
                            style={"color": TEXT, "fontSize": "15px"}),
                    html.Small(PUBLISHER, style={"color": MUTED, "fontSize": "11px"}),
                ]),
            ], className="d-flex align-items-center"),
        ], className="mb-3"),

        html.Div([
            html.Span("Versão atual", style={"color": MUTED, "fontSize": "11px"}),
            html.Div(s["latest"] or "—", style={
                "color": TEXT, "fontSize": "13px", "fontWeight": "600",
                "fontFamily": "monospace",
            }),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                html.Div(str(s["total"]), style={"color": TEXT, "fontSize": "1.3rem", "fontWeight": "700"}),
                html.Small("Instalações", style={"color": MUTED, "fontSize": "11px"}),
            ], xs=6),
            dbc.Col([
                html.Div(f"{s['pct']}%", style={"color": pct_color, "fontSize": "1.3rem", "fontWeight": "700"}),
                html.Small("Atualizado", style={"color": MUTED, "fontSize": "11px"}),
            ], xs=6),
        ], className="mb-2"),

        # Barra de progresso
        html.Div(html.Div(style={
            "width": f"{s['pct']}%", "height": "6px",
            "backgroundColor": pct_color, "borderRadius": "3px",
        }), style={
            "width": "100%", "height": "6px", "backgroundColor": "#eef0f3",
            "borderRadius": "3px", "overflow": "hidden",
        }),
    ]), style={
        "backgroundColor": BG_CARD, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
    }, className="h-100")


def layout() -> html.Div:
    df = get_stores_master()
    stats = [_app_stats(df, lbl) for lbl in APP_LABELS]

    total_installs = sum(s["total"] for s in stats)
    total_atual = sum(s["atual"] for s in stats)
    total_desat = sum(s["desat"] for s in stats)
    pct_geral = f"{round(total_atual / total_installs * 100)}%" if total_installs else "—"

    kpis = dbc.Row([
        dbc.Col(kpi_card("Apps Monitorados", len(APP_LABELS), "primary",
                         icon="bi-app-indicator", subtitle="Aplicativos rastreados"), md=3),
        dbc.Col(kpi_card("Total de Instalações", total_installs, "info",
                         icon="bi-download", subtitle="Somando os 3 apps"), md=3),
        dbc.Col(kpi_card("% Atualizado Geral", pct_geral, "success",
                         icon="bi-check-circle", subtitle=f"{total_atual} instalações"), md=3),
        dbc.Col(kpi_card("Desatualizados", total_desat, "danger",
                         icon="bi-exclamation-triangle", subtitle="Precisam atualizar"), md=3),
    ], className="g-3 mb-4")

    catalog = dbc.Row(
        [dbc.Col(_app_catalog_card(s), md=4) for s in stats],
        className="g-3 mb-4",
    )

    drill = dbc.Card(dbc.CardBody([
        html.Div([
            html.H6("Distribuição de Versões", className="mb-0 fw-semibold",
                    style={"color": TEXT, "fontSize": "14px"}),
            html.Div(
                dcc.Dropdown(
                    id="apps-select", options=[{"label": l, "value": l} for l in APP_LABELS],
                    value=APP_LABELS[0], clearable=False,
                    style={"width": "220px", "fontSize": "13px"},
                ),
            ),
        ], className="d-flex justify-content-between align-items-center mb-3"),
        html.Div(id="apps-drill-content"),
    ]), style={
        "backgroundColor": BG_CARD, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
    })

    return html.Div([
        page_header("Aplicativos", "Versionamento e adoção dos apps gerenciados"),
        kpis,
        html.P("Catálogo de Apps", className="fw-semibold mb-3",
               style={"color": TEXT, "fontSize": "14px"}),
        catalog,
        drill,
    ])


@callback(
    Output("apps-drill-content", "children"),
    Input("apps-select", "value"),
)
def update_drill(label):
    label = label or APP_LABELS[0]
    df = get_stores_master()
    ver_col, status_col = f"{label}_version", f"{label}_status"

    installed = df[df[ver_col].notna()].copy()
    if installed.empty:
        return html.Div("Sem instalações detectadas para este app.",
                        style={"color": MUTED, "padding": "20px"})

    # Distribuição por versão
    dist = installed.groupby(ver_col).size().reset_index(name="Dispositivos")
    dist["vkey"] = dist[ver_col].apply(_version_key)
    dist = dist.sort_values("vkey")
    latest = dist.iloc[-1][ver_col]
    dist["Status"] = dist[ver_col].apply(lambda v: "Atualizado" if v == latest else "Desatualizado")
    dist["%"] = (dist["Dispositivos"] / dist["Dispositivos"].sum() * 100).round(1)

    fig = apply_theme(px.bar(
        dist, x=ver_col, y="Dispositivos", color="Status",
        color_discrete_map={"Atualizado": SUCCESS, "Desatualizado": DANGER},
        labels={ver_col: "Versão"},
        text="Dispositivos",
    ))
    fig.update_layout(height=320, xaxis_tickangle=-30, legend_title=None)
    fig.update_traces(textposition="outside")

    table_df = dist[[ver_col, "Dispositivos", "%", "Status"]].rename(columns={ver_col: "Versão"})
    table_df = table_df.sort_values("Dispositivos", ascending=False)

    table = dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_df.columns],
        **TABLE_KWARGS,
        style_data_conditional=[
            {"if": {"filter_query": '{Status} = "Atualizado"', "column_id": "Status"},
             "color": SUCCESS, "fontWeight": "600"},
            {"if": {"filter_query": '{Status} = "Desatualizado"', "column_id": "Status"},
             "color": DANGER, "fontWeight": "600"},
        ],
    )

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig, config={"displayModeBar": False}), md=7),
            dbc.Col([
                html.Small(f"Versão mais recente: ", style={"color": MUTED}),
                html.Span(latest, style={"fontFamily": "monospace", "fontWeight": "600", "color": TEXT}),
                html.Div(table, className="mt-2"),
            ], md=5),
        ]),
    ])
