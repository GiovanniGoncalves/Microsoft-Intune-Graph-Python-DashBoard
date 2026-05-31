from dash import dcc, html
import dash_bootstrap_components as dbc

# ── Paleta de cores ────────────────────────────────────────────
PRIMARY = "#58a6ff"
SUCCESS = "#3fb950"
WARNING = "#d29922"
DANGER  = "#f85149"
INFO    = "#79c0ff"
MUTED   = "#7d8590"
TEXT    = "#e6edf3"
BG_CARD = "#161b22"
BG_MAIN = "#0d1117"
BORDER  = "#30363d"

COLOR_MAP = {
    "primary": PRIMARY,
    "success": SUCCESS,
    "warning": WARNING,
    "danger":  DANGER,
    "info":    INFO,
}

PALETTE = [PRIMARY, SUCCESS, WARNING, INFO, "#a371f7", DANGER, "#ffa657"]

# ── Tema dark para Plotly ──────────────────────────────────────
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, size=12),
    title_font=dict(color=TEXT, size=14),
    margin=dict(t=50, b=20, l=10, r=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
)

# ── DataTable estilo dark ──────────────────────────────────────
TABLE_KWARGS = dict(
    sort_action="native",
    filter_action="native",
    page_size=20,
    style_table={
        "overflowX": "auto",
        "borderRadius": "8px",
        "border": f"1px solid {BORDER}",
    },
    style_cell={
        "textAlign": "left",
        "padding": "10px 14px",
        "fontSize": "13px",
        "backgroundColor": BG_CARD,
        "color": TEXT,
        "border": f"1px solid {BORDER}",
        "fontFamily": "inherit",
    },
    style_header={
        "backgroundColor": "#1c2128",
        "color": TEXT,
        "fontWeight": "600",
        "border": f"1px solid {BORDER}",
        "fontSize": "11px",
        "textTransform": "uppercase",
        "letterSpacing": "0.06em",
    },
)


def apply_dark(fig):
    """Aplica o tema dark ao figure do Plotly."""
    fig.update_layout(**CHART_LAYOUT)
    return fig


def kpi_card(title: str, value, color_key: str = "primary", icon: str = None):
    color = COLOR_MAP.get(color_key, PRIMARY)
    return dbc.Card(
        dbc.CardBody(
            html.Div([
                html.Div([
                    html.P(title.upper(), className="mb-1", style={
                        "color": MUTED,
                        "fontSize": "11px",
                        "letterSpacing": "0.07em",
                        "fontWeight": "600",
                    }),
                    html.H2(str(value), className="fw-bold mb-0", style={
                        "color": color,
                        "fontSize": "2rem",
                        "lineHeight": "1.1",
                    }),
                ]),
                html.Div(
                    html.I(className=f"bi {icon}", style={
                        "color": color,
                        "opacity": "0.18",
                        "fontSize": "2.5rem",
                    }),
                ) if icon else html.Div(),
            ], className="d-flex justify-content-between align-items-center"),
        ),
        style={
            "backgroundColor": BG_CARD,
            "border": "none",
            "borderLeft": f"4px solid {color}",
            "borderRadius": "8px",
            "boxShadow": "0 2px 12px rgba(0,0,0,0.4)",
        },
        className="h-100",
    )


def chart_card(graph_element):
    return dbc.Card(
        dbc.CardBody(graph_element, style={"padding": "8px"}),
        style={
            "backgroundColor": BG_CARD,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "boxShadow": "0 2px 12px rgba(0,0,0,0.3)",
        },
    )


def page_header(title: str, icon: str):
    return html.Div([
        html.Div(
            html.I(className=f"bi {icon}", style={"color": PRIMARY, "fontSize": "1.4rem"}),
            style={
                "backgroundColor": "rgba(88,166,255,0.1)",
                "borderRadius": "8px",
                "width": "44px",
                "height": "44px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "marginRight": "14px",
                "flexShrink": "0",
            }
        ),
        html.H4(title, className="mb-0 fw-bold", style={"color": TEXT}),
    ], className="d-flex align-items-center mb-4 pb-3",
       style={"borderBottom": f"1px solid {BORDER}"})


def section_title(title: str, badge_text: str = None, badge_color: str = "danger"):
    color = COLOR_MAP.get(badge_color, DANGER)
    return html.Div([
        html.H5(title, className="fw-semibold mb-0 me-2", style={"color": TEXT}),
        html.Span(badge_text, style={
            "color": color,
            "border": f"1px solid {color}",
            "borderRadius": "20px",
            "padding": "2px 10px",
            "fontSize": "12px",
            "fontWeight": "600",
            "backgroundColor": "rgba(0,0,0,0.2)",
        }) if badge_text else html.Div(),
    ], className="d-flex align-items-center mb-3")
