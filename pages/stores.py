"""Página Lojas — visão operacional: filtros + tabela de coletores por loja.

Layout estilo Power BI melhorado: filtros em dropdown, KPIs dinâmicos e
tabela com status de versão dos apps (Atualizado / Desatualizado / Não instalado).
"""
import pandas as pd
from dash import dash_table, dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc

from data.cache import get_stores_master
from data.app_inventory import TRACKED_APPS
from pages.components import (
    kpi_card, page_header, TABLE_KWARGS,
    PRIMARY, SUCCESS, WARNING, DANGER, MUTED, TEXT, BG_CARD, BORDER,
)

APP_LABELS = list(TRACKED_APPS.values())
DEFAULT_APP = APP_LABELS[0]

# Colunas base sempre exibidas
BASE_COLS = {
    "loja": "Loja",
    "Serial number": "Serial",
    "Manufacturer": "Fabricante",
    "Model": "Modelo",
    "Device name": "Dispositivo",
    "WiFiIPv4Address": "IP Wi-Fi",
    "Last check-in": "Última Sincronização",
}


def _dropdown(id_, placeholder, options, value=None, clearable=True):
    return dcc.Dropdown(
        id=id_, placeholder=placeholder, options=options, value=value,
        clearable=clearable,
        style={"fontSize": "13px"},
    )


def _filter_label(text):
    return html.P(text, className="mb-1", style={
        "color": MUTED, "fontSize": "11px", "fontWeight": "600",
        "textTransform": "uppercase", "letterSpacing": "0.05em",
    })


def layout() -> html.Div:
    df = get_stores_master()

    lojas = sorted([x for x in df["loja"].dropna().unique()])
    modelos = sorted([x for x in df["Model"].dropna().unique()]) if "Model" in df.columns else []

    loja_opts = [{"label": l, "value": l} for l in lojas]
    modelo_opts = [{"label": m, "value": m} for m in modelos]
    app_opts = [{"label": a, "value": a} for a in APP_LABELS]
    status_opts = [
        {"label": "🟢 Atualizado", "value": "Atualizado"},
        {"label": "🔴 Desatualizado", "value": "Desatualizado"},
        {"label": "⚪ Não instalado", "value": "Não instalado"},
    ]

    filters_bar = dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([_filter_label("App"),
                     _dropdown("stores-app", "Selecione o app", app_opts,
                               value=DEFAULT_APP, clearable=False)], md=3),
            dbc.Col([_filter_label("Loja"),
                     _dropdown("stores-loja", "Todas as lojas", loja_opts)], md=3),
            dbc.Col([_filter_label("Status do App"),
                     _dropdown("stores-status", "Todos os status", status_opts)], md=3),
            dbc.Col([_filter_label("Modelo"),
                     _dropdown("stores-modelo", "Todos os modelos", modelo_opts)], md=3),
        ], className="g-3"),
    ]), style={
        "backgroundColor": BG_CARD, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
    }, className="mb-4")

    return html.Div([
        page_header(
            "Localização por Loja",
            "Coletores por loja e status de versão dos aplicativos",
        ),
        filters_bar,
        html.Div(id="stores-kpis", className="mb-4"),
        html.Div(id="stores-table-area"),
    ])


def _filter_df(app_label, loja, status, modelo):
    df = get_stores_master()
    if loja:
        df = df[df["loja"] == loja]
    if modelo and "Model" in df.columns:
        df = df[df["Model"] == modelo]
    status_col = f"{app_label}_status"
    if status and status_col in df.columns:
        df = df[df[status_col] == status]
    return df


@callback(
    Output("stores-kpis", "children"),
    Output("stores-table-area", "children"),
    Input("stores-app", "value"),
    Input("stores-loja", "value"),
    Input("stores-status", "value"),
    Input("stores-modelo", "value"),
)
def update_view(app_label, loja, status, modelo):
    app_label = app_label or DEFAULT_APP
    df = _filter_df(app_label, loja, status, modelo)

    status_col = f"{app_label}_status"
    ver_col = f"{app_label}_version"

    total = len(df)
    atualizados = int((df[status_col] == "Atualizado").sum()) if status_col in df.columns else 0
    desatualizados = int((df[status_col] == "Desatualizado").sum()) if status_col in df.columns else 0
    nao_inst = int((df[status_col] == "Não instalado").sum()) if status_col in df.columns else 0
    instalados = atualizados + desatualizados
    pct = f"{round(atualizados / instalados * 100)}%" if instalados else "—"

    kpis = dbc.Row([
        dbc.Col(kpi_card("Coletores (filtro)", total, "primary",
                         icon="bi-upc-scan", subtitle="Dispositivos exibidos"), md=3),
        dbc.Col(kpi_card(f"{app_label} Atualizado", atualizados, "success",
                         icon="bi-check-circle", subtitle=f"{pct} dos instalados"), md=3),
        dbc.Col(kpi_card("Desatualizado", desatualizados, "danger",
                         icon="bi-exclamation-triangle", subtitle="Precisa atualizar"), md=3),
        dbc.Col(kpi_card("Não Instalado", nao_inst, "warning",
                         icon="bi-dash-circle", subtitle="App ausente"), md=3),
    ], className="g-3")

    # Monta a tabela
    cols = list(BASE_COLS.keys())
    table_df = df[[c for c in cols if c in df.columns] +
                  [c for c in [ver_col, status_col] if c in df.columns]].copy()

    if "Last check-in" in table_df.columns:
        table_df["Last check-in"] = pd.to_datetime(
            table_df["Last check-in"], errors="coerce", utc=True
        ).dt.strftime("%d/%m/%Y")

    rename = dict(BASE_COLS)
    rename[ver_col] = "Versão"
    rename[status_col] = "Status"
    table_df = table_df.rename(columns=rename)
    table_df = table_df.sort_values("Loja", na_position="last")

    table = dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_df.columns],
        **TABLE_KWARGS,
        style_data_conditional=[
            {"if": {"filter_query": '{Status} = "Atualizado"', "column_id": "Status"},
             "color": SUCCESS, "fontWeight": "600"},
            {"if": {"filter_query": '{Status} = "Desatualizado"', "column_id": "Status"},
             "color": DANGER, "fontWeight": "600"},
            {"if": {"filter_query": '{Status} = "Não instalado"', "column_id": "Status"},
             "color": MUTED},
        ],
        export_format="csv",
    )

    table_card = dbc.Card(dbc.CardBody([
        html.Div([
            html.H6(f"Coletores — {app_label}", className="mb-0 fw-semibold",
                    style={"color": TEXT, "fontSize": "14px"}),
            html.Small(f"{total} dispositivos", style={"color": MUTED}),
        ], className="d-flex justify-content-between align-items-center mb-3"),
        table,
    ]), style={
        "backgroundColor": BG_CARD, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
    })

    return kpis, table_card
