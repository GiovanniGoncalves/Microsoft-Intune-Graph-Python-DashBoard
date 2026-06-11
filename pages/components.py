from dash import html
import dash_bootstrap_components as dbc

# ── Paleta de cores (DORA light theme) ────────────────────────
PRIMARY   = "#2563eb"
SUCCESS   = "#10b981"
WARNING   = "#f59e0b"
DANGER    = "#ef4444"
INFO      = "#6366f1"
MUTED     = "#6b7280"
TEXT      = "#111827"
TEXT_SOFT = "#374151"
BG_CARD   = "#ffffff"
BG_MAIN   = "#f5f7fa"
BORDER    = "#e5e7eb"
SIDEBAR   = "#1a1d2e"

COLOR_MAP = {
    "primary": PRIMARY,
    "success": SUCCESS,
    "warning": WARNING,
    "danger":  DANGER,
    "info":    INFO,
}

PALETTE = [PRIMARY, SUCCESS, WARNING, INFO, "#a855f7", DANGER, "#f97316"]

# ── Tema Plotly (light) ────────────────────────────────────────
CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_SOFT, size=12),
    title_font=dict(color=TEXT, size=14),
    margin=dict(t=50, b=20, l=10, r=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SOFT)),
    xaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    yaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False),
)

# ── DataTable style ────────────────────────────────────────────
TABLE_KWARGS = dict(
    sort_action="native",
    filter_action="native",
    page_size=15,
    style_table={"overflowX": "auto"},
    style_cell={
        "textAlign": "left",
        "padding": "12px 16px",
        "fontSize": "13px",
        "backgroundColor": BG_CARD,
        "color": TEXT_SOFT,
        "border": "none",
        "borderBottom": f"1px solid {BORDER}",
        "fontFamily": "inherit",
    },
    style_header={
        "backgroundColor": "#f9fafb",
        "color": MUTED,
        "fontWeight": "600",
        "border": "none",
        "borderBottom": f"1px solid {BORDER}",
        "fontSize": "11px",
        "textTransform": "uppercase",
        "letterSpacing": "0.06em",
    },
)


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def apply_theme(fig):
    """Aplica o tema light ao figure do Plotly."""
    fig.update_layout(**CHART_LAYOUT)
    return fig


def kpi_card(title: str, value, color_key: str = "primary",
             icon: str = None, subtitle: str = None, delta: str = None,
             delta_positive: bool = True):
    color      = COLOR_MAP.get(color_key, PRIMARY)
    delta_color = SUCCESS if delta_positive else DANGER
    return dbc.Card([
        dbc.CardBody([
            # Título + menu
            html.Div([
                html.P(title, className="mb-0", style={
                    "color": MUTED, "fontSize": "13px", "fontWeight": "500",
                }),
                html.Div([
                    html.I(className=f"bi {icon}", style={"color": color, "fontSize": "1.1rem"})
                    if icon else html.Div(),
                    html.I(className="bi bi-three-dots ms-2",
                           style={"color": MUTED, "cursor": "pointer"}),
                ], className="d-flex align-items-center"),
            ], className="d-flex justify-content-between align-items-center mb-3"),

            # Valor + delta
            html.Div([
                html.H2(str(value), className="mb-0 me-2", style={
                    "color": TEXT, "fontSize": "1.9rem", "fontWeight": "700",
                }),
                html.Span(delta, style={
                    "backgroundColor": f"rgba({_hex_to_rgb(delta_color)},0.1)",
                    "color": delta_color,
                    "borderRadius": "20px",
                    "padding": "2px 8px",
                    "fontSize": "11px",
                    "fontWeight": "600",
                }) if delta else html.Div(),
            ], className="d-flex align-items-center mb-1"),

            # Subtítulo
            html.P(subtitle, className="mb-0", style={
                "color": MUTED, "fontSize": "12px",
            }) if subtitle else html.Div(),
        ]),
    ], style={
        "backgroundColor": BG_CARD,
        "border": f"1px solid {BORDER}",
        "borderRadius": "12px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
        "borderTop": f"3px solid {color}",
    }, className="h-100")


def chart_card(title: str, graph_element, subtitle: str = None):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H6(title, className="mb-0 fw-semibold",
                            style={"color": TEXT, "fontSize": "14px"}),
                    html.Small(subtitle, style={"color": MUTED}) if subtitle else html.Div(),
                ]),
                html.I(className="bi bi-three-dots",
                       style={"color": MUTED, "cursor": "pointer"}),
            ], className="d-flex justify-content-between align-items-center mb-3"),
            graph_element,
        ]),
    ], style={
        "backgroundColor": BG_CARD,
        "border": f"1px solid {BORDER}",
        "borderRadius": "12px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
    })


def table_card(title: str, table_element, link_text: str = "Ver Todos"):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H6(title, className="mb-0 fw-semibold",
                        style={"color": TEXT, "fontSize": "14px"}),
                html.A(link_text, href="#", style={
                    "color": PRIMARY, "fontSize": "13px",
                    "textDecoration": "none", "fontWeight": "500",
                }),
            ], className="d-flex justify-content-between align-items-center mb-0"),
            html.Hr(style={"borderColor": BORDER, "margin": "12px 0"}),
            table_element,
        ]),
    ], style={
        "backgroundColor": BG_CARD,
        "border": f"1px solid {BORDER}",
        "borderRadius": "12px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
    })


def page_header(title: str, subtitle: str = None):
    return html.Div([
        html.H4(title, className="mb-1 fw-bold", style={"color": TEXT}),
        html.P(subtitle, className="mb-0",
               style={"color": MUTED, "fontSize": "13px"}) if subtitle else html.Div(),
    ], className="mb-4")


def status_badge(text: str, color_key: str = "success"):
    color = COLOR_MAP.get(color_key, SUCCESS)
    return html.Span([
        html.I(className="bi bi-circle-fill me-1",
               style={"fontSize": "6px", "verticalAlign": "middle"}),
        text,
    ], style={
        "backgroundColor": f"rgba({_hex_to_rgb(color)},0.1)",
        "color": color,
        "borderRadius": "20px",
        "padding": "3px 10px",
        "fontSize": "12px",
        "fontWeight": "600",
    })


def section_title(title: str, badge_text: str = None,
                  badge_color: str = "danger", show_link: bool = False):
    color = COLOR_MAP.get(badge_color, DANGER)
    return html.Div([
        html.Div([
            html.H6(title, className="mb-0 fw-semibold me-2",
                    style={"color": TEXT, "fontSize": "14px"}),
            html.Span(badge_text, style={
                "backgroundColor": f"rgba({_hex_to_rgb(color)},0.1)",
                "color": color,
                "borderRadius": "20px",
                "padding": "2px 10px",
                "fontSize": "11px",
                "fontWeight": "600",
            }) if badge_text else html.Div(),
        ], className="d-flex align-items-center"),
        html.A("Ver Todos", href="#", style={
            "color": PRIMARY, "fontSize": "13px",
            "textDecoration": "none", "fontWeight": "500",
        }) if show_link else html.Div(),
    ], className="d-flex justify-content-between align-items-center mb-3")
