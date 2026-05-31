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

NAV_LINKS = [
    ("Inventário",  "/inventory",   "bi-box-seam"),
    ("Operacional", "/operational", "bi-activity"),
    ("Segurança",   "/security",    "bi-shield-check"),
]

sidebar = html.Div([
    # ── Logo ──────────────────────────────────────────────────
    html.Div([
        html.Div(
            html.I(className="bi bi-shield-lock-fill",
                   style={"color": "#58a6ff", "fontSize": "1.3rem"}),
            style={
                "backgroundColor": "rgba(88,166,255,0.12)",
                "borderRadius": "8px",
                "width": "40px", "height": "40px",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "marginRight": "12px", "flexShrink": "0",
            }
        ),
        html.Div([
            html.Div("Intune", style={
                "color": "#e6edf3", "fontWeight": "700",
                "fontSize": "1rem", "lineHeight": "1.2",
            }),
            html.Div("Device Dashboard", style={
                "color": "#7d8590", "fontSize": "0.7rem",
            }),
        ]),
    ], className="d-flex align-items-center",
       style={"padding": "20px 16px", "borderBottom": "1px solid #30363d"}),

    # ── Navegação ─────────────────────────────────────────────
    html.Div([
        html.P("NAVEGAÇÃO", style={
            "color": "#7d8590", "fontSize": "10px",
            "letterSpacing": "0.1em", "fontWeight": "600",
            "marginBottom": "8px", "paddingLeft": "12px",
        }),
        html.Div([
            dbc.NavLink(
                [
                    html.I(className=f"bi {icon}",
                           style={"marginRight": "10px", "fontSize": "1rem"}),
                    html.Span(label),
                ],
                href=href,
                active="exact",
                style={"borderRadius": "6px", "padding": "9px 12px",
                       "marginBottom": "2px", "color": "#8892a4"},
            )
            for label, href, icon in NAV_LINKS
        ]),
    ], style={"padding": "16px 8px", "flexGrow": 1}),

    # ── Rodapé ────────────────────────────────────────────────
    html.Div([
        html.Hr(style={"borderColor": "#30363d", "margin": "0 0 12px 0"}),
        html.Div([
            html.I(className="bi bi-arrow-clockwise me-2",
                   style={"color": "#7d8590"}),
            html.Span("Atualiza a cada 5 min",
                      style={"color": "#7d8590", "fontSize": "11px"}),
        ], className="d-flex align-items-center"),
    ], style={"padding": "0 16px 20px 16px"}),

], style={
    "width": "230px",
    "minHeight": "100vh",
    "backgroundColor": "#0d1117",
    "borderRight": "1px solid #30363d",
    "flexShrink": "0",
    "display": "flex",
    "flexDirection": "column",
})

app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    html.Div([
        sidebar,
        html.Div(
            id="page-content",
            style={
                "flexGrow": 1,
                "backgroundColor": "#0d1117",
                "padding": "28px 32px",
                "minHeight": "100vh",
                "overflowX": "hidden",
            }
        ),
    ], style={"display": "flex", "minHeight": "100vh"}),
], fluid=True, className="p-0", style={"backgroundColor": "#0d1117"})


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
                   style={"fontSize": "3rem", "color": "#7d8590"}),
            html.H4("Página não encontrada",
                    style={"color": "#7d8590", "marginTop": "16px"}),
            dbc.Button(
                [html.I(className="bi bi-house me-2"), "Ir para Inventário"],
                href="/inventory", color="primary", className="mt-3",
            ),
        ], className="text-center mt-5"),
    ])


if __name__ == "__main__":
    app.run(debug=False, port=8050)
