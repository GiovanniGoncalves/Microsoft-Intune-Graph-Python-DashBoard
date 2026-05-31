import os
import dash
import dash_auth
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

BI_ICONS_CDN = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, BI_ICONS_CDN],
    suppress_callback_exceptions=True,
)
app.title = "Intune Dashboard"
server = app.server  # necessário para o gunicorn

VALID_USERS = {
    os.getenv("DASHBOARD_USER", "admin"): os.getenv("DASHBOARD_PASSWORD", "changeme")
}
auth = dash_auth.BasicAuth(app, VALID_USERS)

# ── Seções e links da sidebar ──────────────────────────────────
NAV_SECTIONS = [
    ("VISÃO GERAL", [
        ("Inventário",  "/inventory",   "bi-speedometer2"),
    ]),
    ("OPERAÇÕES", [
        ("Operacional", "/operational", "bi-activity"),
        ("Segurança",   "/security",    "bi-shield-check"),
    ]),
]

BREADCRUMB_MAP = {
    "/inventory":   ("Visão Geral", "Inventário"),
    "/operational": ("Operações",   "Operacional"),
    "/security":    ("Operações",   "Segurança"),
}

# ── Sidebar ────────────────────────────────────────────────────
def build_sidebar():
    nav_items = []
    for section_label, links in NAV_SECTIONS:
        nav_items.append(
            html.P(section_label, style={
                "color": "#4b5280",
                "fontSize": "10px",
                "letterSpacing": "0.12em",
                "fontWeight": "700",
                "marginBottom": "6px",
                "marginTop": "18px",
                "paddingLeft": "14px",
            })
        )
        for label, href, icon in links:
            nav_items.append(
                dbc.NavLink(
                    [
                        html.I(className=f"bi {icon}",
                               style={"marginRight": "10px", "fontSize": "0.95rem"}),
                        html.Span(label, style={"fontSize": "13.5px"}),
                    ],
                    href=href,
                    active="exact",
                    style={"borderRadius": "8px", "padding": "9px 14px",
                           "marginBottom": "2px", "color": "#8b90b8"},
                )
            )

    return html.Div([
        # Logo
        html.Div([
            html.Div(
                html.I(className="bi bi-shield-lock-fill",
                       style={"color": "#ffffff", "fontSize": "1.1rem"}),
                style={
                    "backgroundColor": "#2563eb",
                    "borderRadius": "8px",
                    "width": "34px", "height": "34px",
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "center", "marginRight": "10px",
                    "flexShrink": "0",
                }
            ),
            html.Span("INTUNE", style={
                "color": "#ffffff",
                "fontWeight": "800",
                "fontSize": "1.05rem",
                "letterSpacing": "0.05em",
            }),
        ], className="d-flex align-items-center",
           style={"padding": "20px 16px 16px 16px",
                  "borderBottom": "1px solid #252840"}),

        # Navegação
        html.Div(nav_items, style={"padding": "8px 10px", "flexGrow": 1}),

        # Perfil do usuário
        html.Div([
            html.Hr(style={"borderColor": "#252840", "margin": "0 0 14px 0"}),
            html.Div([
                html.Div(
                    html.I(className="bi bi-person-circle",
                           style={"color": "#8b90b8", "fontSize": "1.6rem"}),
                    style={"marginRight": "10px", "flexShrink": "0"}
                ),
                html.Div([
                    html.Div(
                        os.getenv("DASHBOARD_USER", "admin").title(),
                        style={"color": "#e2e4f0", "fontSize": "13px",
                               "fontWeight": "600", "lineHeight": "1.2"}
                    ),
                    html.Div("Administrador", style={
                        "color": "#4b5280", "fontSize": "11px"
                    }),
                ]),
                html.I(className="bi bi-chevron-right ms-auto",
                       style={"color": "#4b5280", "fontSize": "0.75rem"}),
            ], className="d-flex align-items-center"),
        ], style={"padding": "0 16px 20px 16px"}),

    ], style={
        "width": "230px",
        "minHeight": "100vh",
        "backgroundColor": "#1a1d2e",
        "flexShrink": "0",
        "display": "flex",
        "flexDirection": "column",
        "position": "sticky",
        "top": "0",
        "height": "100vh",
        "overflowY": "auto",
    })


# ── Navbar superior ────────────────────────────────────────────
navbar = html.Div([
    # Breadcrumb
    html.Div(id="breadcrumb-area", style={"minWidth": 0}),

    # Ações
    html.Div([
        # Busca
        html.Div([
            html.I(className="bi bi-search",
                   style={"color": "#9ca3af", "fontSize": "0.85rem",
                          "position": "absolute", "left": "12px", "top": "50%",
                          "transform": "translateY(-50%)"}),
            dcc.Input(
                placeholder="Buscar dispositivos...",
                type="text",
                style={
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "8px",
                    "padding": "7px 12px 7px 34px",
                    "fontSize": "13px",
                    "color": "#374151",
                    "backgroundColor": "#f9fafb",
                    "outline": "none",
                    "width": "220px",
                }
            ),
        ], style={"position": "relative"}),

        # Ícones
        html.Button(
            html.I(className="bi bi-bell",
                   style={"fontSize": "1rem", "color": "#6b7280"}),
            style={
                "border": "1px solid #e5e7eb", "borderRadius": "8px",
                "padding": "7px 12px", "backgroundColor": "white",
                "cursor": "pointer",
            }
        ),

        # Botão Export
        html.Button(
            [
                html.I(className="bi bi-download me-2",
                       style={"fontSize": "0.85rem"}),
                "Exportar Dados",
            ],
            id="export-btn",
            n_clicks=0,
            style={
                "backgroundColor": "#2563eb",
                "color": "white",
                "border": "none",
                "borderRadius": "8px",
                "padding": "8px 16px",
                "fontSize": "13px",
                "fontWeight": "600",
                "cursor": "pointer",
                "display": "flex",
                "alignItems": "center",
            }
        ),
        dcc.Download(id="download-csv"),
    ], className="d-flex align-items-center gap-2"),

], className="d-flex justify-content-between align-items-center",
   style={
       "backgroundColor": "#ffffff",
       "borderBottom": "1px solid #e5e7eb",
       "padding": "12px 28px",
       "position": "sticky",
       "top": "0",
       "zIndex": "100",
   })

# ── Layout principal ───────────────────────────────────────────
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    html.Div([
        build_sidebar(),
        html.Div([
            navbar,
            html.Div(id="page-content", style={
                "backgroundColor": "#f5f7fa",
                "padding": "28px 32px",
                "flexGrow": 1,
                "minHeight": "calc(100vh - 57px)",
            }),
        ], style={"flexGrow": 1, "display": "flex", "flexDirection": "column", "minWidth": 0}),
    ], style={"display": "flex", "minHeight": "100vh"}),
], fluid=True, className="p-0")


# ── Callbacks ─────────────────────────────────────────────────
@app.callback(Output("breadcrumb-area", "children"), Input("url", "pathname"))
def update_breadcrumb(pathname):
    section, page = BREADCRUMB_MAP.get(pathname or "/inventory", ("Visão Geral", "Inventário"))
    return html.Div([
        html.Span(section, style={"color": "#9ca3af", "fontSize": "13px"}),
        html.I(className="bi bi-chevron-right mx-1",
               style={"color": "#d1d5db", "fontSize": "10px"}),
        html.Span(page, style={"color": "#111827", "fontSize": "13px", "fontWeight": "600"}),
    ], className="d-flex align-items-center")


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: str):
    from pages import inventory, operational, security
    if pathname in ("/", "/inventory"):
        return inventory.layout()
    if pathname == "/operational":
        return operational.layout()
    if pathname == "/security":
        return security.layout()
    return html.Div([
        html.Div([
            html.I(className="bi bi-exclamation-circle",
                   style={"fontSize": "3rem", "color": "#9ca3af"}),
            html.H4("Página não encontrada",
                    style={"color": "#6b7280", "marginTop": "16px"}),
            dbc.Button(
                [html.I(className="bi bi-house me-2"), "Ir para Inventário"],
                href="/inventory", color="primary", className="mt-3",
            ),
        ], className="text-center mt-5"),
    ])


@app.callback(
    Output("download-csv", "data"),
    Input("export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_data(n_clicks):
    from data.cache import get_devices
    df = get_devices()
    return dcc.send_data_frame(df.to_csv, "intune_devices.csv", index=False)


if __name__ == "__main__":
    app.run(debug=False, port=8050)
