import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "Intune Dashboard"

NAV_LINKS = [
    ("Inventário", "/inventory", "bi-box-seam"),
    ("Operacional", "/operational", "bi-activity"),
    ("Segurança", "/security", "bi-shield-check"),
    ("Lojas", "/stores", "bi-shop"),
]

sidebar = html.Div([
    html.Div([
        html.H5("Intune", className="fw-bold text-white mb-0"),
        html.Small("Device Dashboard", className="text-white-50"),
    ], className="py-3 px-3 mb-2 border-bottom border-secondary"),
    dbc.Nav(
        [
            dbc.NavLink(label, href=href, active="exact",
                        className="text-white-50 py-2 px-3 rounded")
            for label, href, _ in NAV_LINKS
        ],
        vertical=True,
        pills=True,
    ),
    html.Div([
        html.Small("Dados atualizados a cada 5 min", className="text-secondary"),
    ], className="position-absolute bottom-0 pb-3 px-3"),
], className="bg-dark min-vh-100 py-2 position-relative", style={"width": "220px"})

app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    html.Div([
        sidebar,
        html.Div(id="page-content", className="p-4 flex-grow-1 overflow-auto"),
    ], className="d-flex"),
], fluid=True, className="p-0")


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: str):
    from pages import inventory, operational, security, stores
    if pathname in ("/", "/inventory"):
        return inventory.layout()
    if pathname == "/operational":
        return operational.layout()
    if pathname == "/security":
        return security.layout()
    if pathname == "/stores":
        return stores.layout()
    return html.Div([
        html.H4("Página não encontrada", className="text-muted mt-5 text-center"),
        dbc.Button("Ir para Inventário", href="/inventory", color="primary", className="d-block mx-auto mt-3"),
    ])


if __name__ == "__main__":
    app.run(debug=True, port=8050)
