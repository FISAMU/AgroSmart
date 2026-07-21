"""Design system AgroSmart — agritech UI (design uniquement)."""

import base64
import functools
import os
import urllib.request

FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
)

COLORS = {
    "forest": "#1B4332",
    "green": "#2D6A4F",
    "mint": "#52B788",
    "lime": "#74C69D",
    "cream": "#F7F4EE",
    "dark": "#0B1610",
    "dark_card": "#14261E",
    "text_muted": "#8FA99A",
    "amber": "#F4A261",
    "sky": "#4CC9F0",
    "text_dark": "#1A2E24",
    "text_body": "#33483C",
    "border_light": "#E2EBE4",
    "card_bg": "#FFFFFF",
}

# ── Icônes SVG (dashboard) ──
SVG = {
    "logo": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22V12M12 12C12 12 8 8 8 4a4 4 0 0 1 8 0c0 4-4 8-4 8z"/></svg>',
    "dashboard": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>',
    "diagnostic": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>',
    "irrigation": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
    "settings": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
    "logout": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
    "temp": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>',
    "humidity": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
    "ph": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3h6v7a3 3 0 1 1-6 0V3z"/><line x1="9" y1="3" x2="15" y2="3"/><path d="M12 13v8"/><path d="M8 21h8"/></svg>',
    "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "live": '<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="8"/></svg>',
}

DASHBOARD_NAV = [
    ("Tableau de bord", "dashboard", SVG["dashboard"]),
    ("Diagnostic pédologique", "diagnostic", SVG["diagnostic"]),
    ("Irrigation", "irrigation", SVG["irrigation"]),
    ("Paramètres", "settings", SVG["settings"]),
]

STREAMLIT_HIDE = """
<style>
    #MainMenu, header, footer { visibility: hidden !important; height: 0 !important; }
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] { display: none !important; }
</style>
"""

STREAMLIT_DASHBOARD = f"""
<style>
    #MainMenu, header, footer, [data-testid="stFooter"] {{
        visibility: hidden !important; display: none !important; height: 0 !important;
    }}
    /* Pas de flou / assombrissement pendant l'actualisation Streamlit */
    .stApp, .stApp > div, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section.main,
    [data-testid="stAppViewContainer"] > section.main > div,
    [data-testid="stVerticalBlock"], [data-testid="stVerticalBlockBorderWrapper"] {{
        opacity: 1 !important;
        filter: none !important;
        backdrop-filter: none !important;
        transition: none !important;
    }}
    [data-testid="stStatusWidget"], [data-testid="stToolbar"], .stSpinner,
    div[data-testid="stNotificationContentInfo"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    /* Masquer la navigation Streamlit par défaut (lien bleu en haut) */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"],
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarNavLink"],
    [data-testid="stSidebar"] nav,
    [data-testid="stSidebar"] ul {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }}
    .stApp {{
        background: #FFFFFF !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    }}
    [data-testid="stAppViewContainer"] > .main {{
        background: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] {{
        display: block !important;
        background: linear-gradient(180deg, {COLORS["forest"]} 0%, {COLORS["dark"]} 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
        min-width: 260px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: transparent !important;
        padding-top: 0.5rem !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] h2 {{
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.12) !important;
        margin: 0.75rem 0 !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: #FFFFFF !important;
        opacity: 1 !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-align: left !important;
        padding: 0.6rem 0.85rem !important;
        box-shadow: none !important;
        justify-content: flex-start !important;
        filter: none !important;
        transform: none !important;
    }}
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span,
    [data-testid="stSidebar"] .stButton > button div {{
        color: #FFFFFF !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.12) !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: rgba(255,255,255,0.14) !important;
        border-color: rgba(116,198,157,0.45) !important;
    }}
    [data-testid="stSidebar"] .nav-icon {{
        display: flex; align-items: center; justify-content: center;
        color: {COLORS["lime"]}; min-width: 28px;
    }}
    .sidebar-brand h2 {{ color: #FFFFFF !important; }}
    .sidebar-brand p {{ color: rgba(255,255,255,0.75) !important; }}
    .block-container {{
        padding: 1.5rem 2rem 2rem !important;
        max-width: 1180px !important;
        background: #FFFFFF !important;
    }}
    .main h1, .main h2, .main h3, .main p, .main label, .main span {{
        color: {COLORS["text_dark"]};
        font-family: 'Segoe UI', system-ui, sans-serif !important;
    }}
    .dash-page-title {{
        color: {COLORS["forest"]} !important;
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }}
    .dash-page-caption {{
        color: {COLORS["text_body"]} !important;
        font-size: 0.9rem !important;
        margin-top: 0.25rem !important;
    }}
    div[data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid {COLORS["border_light"]};
        border-radius: 18px;
        padding: 0.85rem 1rem;
        box-shadow: 0 2px 12px rgba(27,67,50,0.05);
    }}
    div[data-testid="stMetric"] label {{
        color: {COLORS["text_body"]} !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {COLORS["forest"]} !important;
        font-weight: 800 !important;
        font-size: 1.85rem !important;
    }}
    .main .stButton > button {{
        background: linear-gradient(135deg, {COLORS["green"]}, {COLORS["mint"]}) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }}
    [data-testid="stFormSubmitButton"] > button {{ width: 100% !important; }}
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    div[data-baseweb="select"] > div {{
        background: #FFFFFF !important;
        border: 1px solid {COLORS["border_light"]} !important;
        border-radius: 12px !important;
        color: {COLORS["text_dark"]} !important;
    }}
    .stAlert {{ border-radius: 14px !important; }}
    .page-title {{
        color: {COLORS["forest"]} !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.25rem !important;
    }}
    .page-subtitle {{
        color: {COLORS["text_body"]} !important;
        font-size: 0.9rem !important;
        margin-bottom: 1.5rem !important;
    }}
    .dash-chart-card {{
        background: {COLORS["card_bg"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: 20px;
        padding: 1rem 1rem 0.5rem;
        margin-top: 1.25rem;
        box-shadow: 0 4px 24px rgba(27,67,50,0.06);
    }}
    .dash-live-badge {{
        font-size: 0.82rem; font-weight: 600; color: {COLORS["green"]};
        display: flex; align-items: center; gap: 6px; justify-content: flex-end;
    }}
    .dash-live-dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {COLORS["mint"]}; display: inline-block;
    }}
</style>
"""

# Paysage agricole — champs dorés au coucher du soleil (Unsplash)
AUTH_BG_FALLBACK = (
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef"
    "?auto=format&fit=crop&w=1400&h=900&q=85"
)


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_image_data_uri(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext or "jpeg"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


@functools.lru_cache(maxsize=4)
def _fetch_fallback_data_uri(fallback_url: str) -> str:
    request = urllib.request.Request(
        fallback_url,
        headers={"User-Agent": "AgroSmart/1.0"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        encoded = base64.b64encode(response.read()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def resolve_auth_bg_src() -> str:
    """Image locale en data URI, sinon téléchargement du fallback embarqué."""
    root = _project_root()
    for relative in ("farm_bg.jpg", os.path.join("assets", "auth_bg.jpg")):
        path = os.path.join(root, relative)
        if os.path.isfile(path):
            return _read_image_data_uri(path)
    try:
        return _fetch_fallback_data_uri(AUTH_BG_FALLBACK)
    except OSError:
        return AUTH_BG_FALLBACK


def auth_visual_img_tag(src: str | None = None) -> str:
    """Balise img fiable pour le panneau visuel auth (iframe Streamlit)."""
    image_src = src or resolve_auth_bg_src()
    safe_src = image_src.replace('"', "&quot;")
    return f'<img class="auth-visual-bg" src="{safe_src}" alt="" decoding="async" />'


ACCUEIL_BG_URLS = (
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1600&q=80",
)


@functools.lru_cache(maxsize=8)
def _fetch_image_data_uri(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "AgroSmart/1.0"})
    with urllib.request.urlopen(request, timeout=12) as response:
        encoded = base64.b64encode(response.read()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


@functools.lru_cache(maxsize=1)
def accueil_slide_srcs() -> tuple[str, ...]:
    """Images embarquées pour le diaporama d'accueil (fiable dans iframe Streamlit)."""
    slides: list[str] = []
    root = _project_root()
    local = os.path.join(root, "farm_bg.jpg")
    if os.path.isfile(local):
        slides.append(_read_image_data_uri(local))
    for url in ACCUEIL_BG_URLS:
        if len(slides) >= 4:
            break
        try:
            slides.append(_fetch_image_data_uri(url))
        except OSError:
            continue
    if not slides:
        slides.append(resolve_auth_bg_src())
    return tuple(slides)


def accueil_slides_html() -> str:
    slides = accueil_slide_srcs()
    return "\n".join(
        f'<img class="slide{" active" if i == 0 else ""}" src="{src.replace(chr(34), "&quot;")}" alt="" />'
        for i, src in enumerate(slides)
    )

AUTH_CSS = f"""
@import url('{FONT_URL}');
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; width: 100%; }}
body {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: {COLORS["cream"]};
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
}}
.auth-shell {{
    display: flex; width: min(920px, 100%); min-height: 580px;
    border-radius: 28px; overflow: hidden;
    box-shadow: 0 32px 80px rgba(27, 67, 50, 0.22);
    border: 1px solid rgba(255,255,255,0.55);
}}
.auth-visual {{
    flex: 1.15; position: relative; overflow: hidden;
    min-height: 580px;
    background: {COLORS["forest"]};
}}
.auth-visual-bg {{
    position: absolute; inset: 0; z-index: 0;
    width: 100%; height: 100%;
    object-fit: cover; object-position: center center;
    pointer-events: none;
}}
.auth-visual::before {{
    content: ''; position: absolute; inset: 0; z-index: 1;
    background: linear-gradient(
        180deg,
        rgba(11, 22, 16, 0.08) 0%,
        rgba(11, 22, 16, 0.12) 45%,
        rgba(11, 22, 16, 0.42) 100%
    );
}}
.auth-visual::after {{
    content: ''; position: absolute; inset: 0; z-index: 1;
    background: linear-gradient(to top, rgba(11, 22, 16, 0.58) 0%, transparent 42%);
}}
.auth-visual-content {{
    position: absolute; inset: 0; z-index: 2;
    display: flex; flex-direction: column; justify-content: flex-end;
    padding: 40px 36px; color: white;
}}
.auth-visual-content .brand {{
    font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;
    margin-bottom: 10px; text-shadow: 0 2px 12px rgba(0,0,0,0.4);
}}
.auth-visual-content .brand span {{ color: {COLORS["lime"]}; }}
.auth-visual-content p {{
    font-size: 0.88rem; line-height: 1.6; max-width: 300px;
    color: rgba(255,255,255,0.92);
    text-shadow: 0 1px 8px rgba(0,0,0,0.35);
}}
.auth-visual .chips {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px;
}}
.auth-visual .chip {{
    font-size: 0.68rem; padding: 6px 14px; border-radius: 999px;
    background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.28);
    backdrop-filter: blur(10px);
    text-shadow: 0 1px 4px rgba(0,0,0,0.2);
}}
.auth-panel {{
    width: 400px; background: white; padding: 44px 36px;
    display: flex; flex-direction: column; justify-content: center; gap: 16px;
}}
.auth-panel h1 {{
    font-size: 1.65rem; font-weight: 800; color: {COLORS["forest"]};
    letter-spacing: -0.03em; text-align: center;
}}
.auth-panel .subtitle {{
    text-align: center; font-size: 0.82rem; color: #6B7C72; margin-top: -8px;
}}
.field-group {{ display: flex; flex-direction: column; gap: 6px; }}
.field-group label {{
    font-size: 0.78rem; font-weight: 600; color: {COLORS["green"]};
}}
.input-wrap {{ position: relative; display: flex; align-items: center; }}
.input-wrap input, .input-wrap select {{
    width: 100%; padding: 12px 14px 12px 40px;
    background: {COLORS["cream"]}; border: 1.5px solid #E2EBE4;
    border-radius: 12px; font-size: 0.88rem; font-family: inherit;
    color: {COLORS["forest"]}; outline: none; transition: border 0.2s, box-shadow 0.2s;
}}
.input-wrap input:focus, .input-wrap select:focus {{
    border-color: {COLORS["mint"]};
    box-shadow: 0 0 0 4px rgba(82, 183, 136, 0.15);
}}
.icon-left {{
    position: absolute; left: 12px; color: {COLORS["mint"]};
    display: flex; pointer-events: none;
}}
.icon-right {{
    position: absolute; right: 12px; color: #8FA99A;
    cursor: pointer; display: flex;
}}
.auth-row {{ display: flex; gap: 12px; }}
.auth-row .field-group {{ flex: 1; }}
.btn-primary {{
    width: 100%; padding: 14px; border: none; border-radius: 14px;
    background: linear-gradient(135deg, {COLORS["forest"]}, {COLORS["mint"]});
    color: white; font-family: inherit; font-size: 0.95rem; font-weight: 700;
    cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 12px 28px rgba(45, 106, 79, 0.35);
}}
.btn-primary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 16px 36px rgba(45, 106, 79, 0.45);
}}
.auth-footer {{
    text-align: center; font-size: 0.78rem; color: #6B7C72;
}}
.auth-footer a {{ color: {COLORS["green"]}; font-weight: 600; text-decoration: none; }}
.auth-footer a:hover {{ text-decoration: underline; }}
.auth-feedback {{
    text-align: center; font-size: 0.8rem; min-height: 18px;
}}
.options {{
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.76rem;
}}
.options label {{ display: flex; align-items: center; gap: 6px; color: #4A5F54; cursor: pointer; }}
#forgot-link {{ color: {COLORS["green"]}; text-decoration: none; font-weight: 600; cursor: pointer; }}
#forgot-link:hover {{ text-decoration: underline; }}

/* Modal réinitialisation */
.modal-backdrop {{
    display:none; position:fixed; inset:0;
    background:rgba(11,22,16,0.7); backdrop-filter:blur(8px);
    z-index:100; align-items:center; justify-content:center;
}}
.modal-backdrop.open {{ display:flex; }}
.modal {{
    background:white; border-radius:24px; padding:36px 32px;
    width:min(380px, 92vw); display:flex; flex-direction:column; gap:16px;
    box-shadow:0 32px 80px rgba(27,67,50,0.25);
    border:1px solid #E2EBE4; animation:popIn 0.3s ease both;
}}
@keyframes popIn {{
    from {{ opacity:0; transform:scale(0.92) translateY(16px); }}
    to {{ opacity:1; transform:scale(1) translateY(0); }}
}}
.modal h2 {{ color:{COLORS["forest"]}; font-size:1.15rem; font-weight:800; text-align:center; }}
.modal p {{ color:#6B7C72; font-size:0.82rem; text-align:center; line-height:1.5; }}
.modal input {{
    width:100%; padding:12px 16px; background:{COLORS["cream"]};
    border:1.5px solid #E2EBE4; border-radius:12px;
    font-size:1.1rem; font-family:inherit; color:{COLORS["forest"]};
    outline:none; text-align:center; letter-spacing:6px; font-weight:700;
}}
.modal input:focus {{ border-color:{COLORS["mint"]}; box-shadow:0 0 0 4px rgba(82,183,136,0.15); }}
.modal-btn {{
    width:100%; padding:13px; border:none; border-radius:12px;
    background:linear-gradient(135deg,{COLORS["forest"]},{COLORS["mint"]});
    color:white; font-family:inherit; font-size:0.9rem; font-weight:700; cursor:pointer;
}}
.modal-btn.secondary {{
    background:transparent; color:{COLORS["green"]};
    border:1.5px solid #E2EBE4;
}}
.modal-feedback {{ text-align:center; font-size:0.82rem; min-height:16px; color:#E76F51; }}
.modal-step {{ display:none; flex-direction:column; gap:14px; }}
.modal-step.active {{ display:flex; }}
#feedback {{ text-align:center; font-size:0.82rem; min-height:18px; color:#E76F51; }}
"""

def auth_bg_style(bg_url: str) -> str:
    """Conservé pour compatibilité — préférer auth_visual_img_tag()."""
    if bg_url and "url(" in bg_url:
        return f"background-image:{bg_url};"
    return f'background-image:url("{AUTH_BG_FALLBACK}");'

ACCUEIL_CSS = f"""
@import url('{FONT_URL}');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body, html {{ height: 100%; font-family: 'Plus Jakarta Sans', sans-serif; overflow: hidden; }}

.hero {{
    position: relative; height: 100vh; width: 100%; overflow: hidden;
    background: {COLORS["dark"]};
}}
.slide {{
    position: absolute; inset: 0; z-index: 0;
    width: 100%; height: 100%; object-fit: cover; object-position: center;
    opacity: 0; transition: opacity 1.8s ease-in-out; transform: scale(1.04);
    pointer-events: none;
}}
.slide.active {{ opacity: 1; transform: scale(1); transition: opacity 1.8s, transform 8s ease-out; }}
.hero-overlay {{
    position: absolute; inset: 0; z-index: 2;
    background: linear-gradient(115deg,
        rgba(11,22,16,0.92) 0%,
        rgba(11,22,16,0.65) 42%,
        rgba(27,67,50,0.35) 100%);
}}
.hero-grid {{
    position: relative; z-index: 10; height: 100%;
    display: grid; grid-template-columns: 1.2fr 1fr;
    align-items: center; gap: 40px;
    padding: 48px clamp(24px, 6vw, 80px);
    max-width: 1280px; margin: 0 auto;
}}
.hero-copy {{ color: white; animation: fadeUp 1s ease-out; }}
.hero-copy .eyebrow {{
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: {COLORS["lime"]};
    background: rgba(116, 198, 157, 0.12); border: 1px solid rgba(116, 198, 157, 0.3);
    padding: 6px 14px; border-radius: 999px; margin-bottom: 20px;
}}
.hero-copy h1 {{
    font-size: clamp(2.4rem, 5vw, 3.8rem); font-weight: 800;
    line-height: 1.05; letter-spacing: -0.04em; margin-bottom: 16px;
}}
.hero-copy h1 span {{ color: {COLORS["lime"]}; }}
.hero-copy .lead {{
    font-size: 1rem; line-height: 1.65; color: rgba(255,255,255,0.82);
    max-width: 520px; margin-bottom: 28px;
}}
.feature-row {{
    display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 32px;
}}
.feature-pill {{
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px; border-radius: 14px;
    background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12);
    font-size: 0.78rem; font-weight: 500; color: rgba(255,255,255,0.9);
}}
.feature-pill .dot {{
    width: 8px; height: 8px; border-radius: 50%; background: {COLORS["mint"]};
}}
.hero-card {{
    background: rgba(255,255,255,0.08); backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.15); border-radius: 28px;
    padding: 36px 32px; color: white;
    box-shadow: 0 40px 80px rgba(0,0,0,0.35);
    animation: fadeUp 1s ease-out 0.15s both;
}}
.hero-card .card-icon {{
    width: 56px; height: 56px; border-radius: 16px;
    background: linear-gradient(135deg, {COLORS["mint"]}, {COLORS["lime"]});
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 20px; color: {COLORS["forest"]};
}}
.hero-card h2 {{ font-size: 1.35rem; font-weight: 700; margin-bottom: 8px; }}
.hero-card p {{ font-size: 0.85rem; opacity: 0.85; line-height: 1.5; margin-bottom: 24px; }}
.btn-link {{
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; padding: 14px 20px; margin-bottom: 12px;
    border-radius: 14px; font-size: 0.95rem; font-weight: 700;
    text-decoration: none; transition: transform 0.2s, box-shadow 0.2s;
}}
.btn-primary {{
    background: linear-gradient(135deg, {COLORS["mint"]}, {COLORS["lime"]});
    color: {COLORS["forest"]}; box-shadow: 0 12px 32px rgba(82, 183, 136, 0.4);
}}
.btn-secondary {{
    background: rgba(255,255,255,0.08); color: white;
    border: 1.5px solid rgba(255,255,255,0.25);
}}
.btn-danger {{
    background: rgba(244, 162, 97, 0.2); color: #FFD6A5;
    border: 1.5px solid rgba(244, 162, 97, 0.4);
}}
.btn-link:hover {{ transform: translateY(-2px); }}
.hero-footer {{ font-size: 0.68rem; opacity: 0.5; text-align: center; margin-top: 16px; }}
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@media (max-width: 900px) {{
    .hero-grid {{ grid-template-columns: 1fr; padding: 32px 24px; overflow-y: auto; }}
    body, html {{ overflow: auto; }}
}}
"""

def render_dashboard_sidebar(active_interface: str) -> None:
    """Sidebar de navigation — dashboard uniquement."""
    import streamlit as st

    st.markdown(
        f"""
        <div class="sidebar-brand" style="display:flex;align-items:center;gap:10px;padding:0 0.25rem 0.5rem;">
            <div class="logo" style="width:40px;height:40px;border-radius:12px;background:rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center;color:{COLORS['lime']};">{SVG["logo"]}</div>
            <div>
                <h2 style="font-size:1.1rem;font-weight:800;margin:0;color:#fff;">AgroSmart</h2>
                <p style="font-size:0.72rem;margin:0;color:rgba(255,255,255,0.75);text-transform:uppercase;letter-spacing:0.04em;">Pilotage agricole</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    for label, key, icon in DASHBOARD_NAV:
        icon_col, btn_col = st.columns([1, 7], gap="small", vertical_alignment="center")
        with icon_col:
            st.markdown(f'<div class="nav-icon">{icon}</div>', unsafe_allow_html=True)
        with btn_col:
            is_active = active_interface == label
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_interface = label
                st.rerun()
    st.markdown("---")
    _, logout_col = st.columns([1, 7], gap="small", vertical_alignment="center")
    with logout_col:
        if st.button("Déconnexion", key="nav_logout", use_container_width=True):
            st.session_state["user"] = None
            st.switch_page("Accueil.py")


def dashboard_html(user_name, user_initial, current_temp, current_hum, current_ph, has_data):
    live = "En direct" if has_data else "En attente capteurs"
    live_color = COLORS["mint"] if has_data else COLORS["amber"]
    return f"""
<div class="dash-root" style="font-family:'Plus Jakarta Sans','Segoe UI',system-ui,sans-serif;color:{COLORS['text_dark']};width:100%;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px;flex-wrap:wrap;gap:16px;">
    <div>
      <div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{COLORS['green']};margin-bottom:8px;display:flex;align-items:center;gap:6px;">
        <span style="width:8px;height:8px;border-radius:50%;background:{COLORS['mint']};display:inline-block;"></span>
        AgroSmart
      </div>
      <h1 style="font-size:clamp(1.5rem,3vw,2rem);font-weight:800;letter-spacing:-0.02em;color:{COLORS['forest']};margin:0 0 4px 0;line-height:1.15;">Bonjour, {user_name}</h1>
      <p style="font-size:0.9rem;color:{COLORS['text_body']};margin:0;font-weight:500;">Suivi en temps réel de vos paramètres agricoles</p>
    </div>
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:8px;padding:9px 16px;border-radius:999px;background:#F7F4EE;border:1px solid {COLORS['border_light']};">
        <span style="width:9px;height:9px;border-radius:50%;background:{live_color};display:inline-block;"></span>
        <span style="font-size:0.85rem;font-weight:600;color:{COLORS['text_dark']};">{live}</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;padding:7px 16px 7px 7px;border-radius:999px;background:#F7F4EE;border:1px solid {COLORS['border_light']};">
        <div style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,{COLORS['green']},{COLORS['mint']});color:white;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.95rem;">{user_initial}</div>
        <span style="font-weight:600;font-size:0.95rem;color:{COLORS['text_dark']};">{user_name}</span>
      </div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
    <div style="background:{COLORS['card_bg']};border:1px solid rgba(244,162,97,0.35);border-radius:22px;padding:24px 22px;box-shadow:0 4px 20px rgba(27,67,50,0.06);">
      <div style="display:flex;align-items:center;gap:8px;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:{COLORS['text_body']};margin-bottom:10px;">
        <span style="color:#C2410C;">{SVG['temp']}</span> Température
      </div>
      <div style="font-size:2.1rem;font-weight:800;color:#C2410C;line-height:1.1;">{current_temp}</div>
      <div style="font-size:0.75rem;color:{COLORS['text_body']};margin-top:8px;font-weight:500;">Sol · capteur IoT</div>
    </div>
    <div style="background:{COLORS['card_bg']};border:1px solid rgba(76,201,240,0.35);border-radius:22px;padding:24px 22px;box-shadow:0 4px 20px rgba(27,67,50,0.06);">
      <div style="display:flex;align-items:center;gap:8px;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:{COLORS['text_body']};margin-bottom:10px;">
        <span style="color:#0369A1;">{SVG['humidity']}</span> Humidité
      </div>
      <div style="font-size:2.1rem;font-weight:800;color:#0369A1;line-height:1.1;">{current_hum}</div>
      <div style="font-size:0.75rem;color:{COLORS['text_body']};margin-top:8px;font-weight:500;">Taux d'humidité du sol</div>
    </div>
    <div style="background:{COLORS['card_bg']};border:1px solid rgba(82,183,136,0.4);border-radius:22px;padding:24px 22px;box-shadow:0 4px 20px rgba(27,67,50,0.06);">
      <div style="display:flex;align-items:center;gap:8px;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:{COLORS['text_body']};margin-bottom:10px;">
        <span style="color:{COLORS['forest']};">{SVG['ph']}</span> pH Sol
      </div>
      <div style="font-size:2.1rem;font-weight:800;color:{COLORS['forest']};line-height:1.1;">{current_ph}</div>
      <div style="font-size:0.75rem;color:{COLORS['text_body']};margin-top:8px;font-weight:500;">Acidité · alcalinité</div>
    </div>
  </div>
</div>
"""

PLOTLY_COLORS = [COLORS["mint"], COLORS["sky"], COLORS["amber"]]
