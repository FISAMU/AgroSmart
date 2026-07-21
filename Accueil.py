import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ui.theme import ACCUEIL_CSS, STREAMLIT_HIDE, accueil_slides_html

st.set_page_config(page_title="AgroSmart", layout="wide", initial_sidebar_state="collapsed")
st.set_option("client.showSidebarNavigation", False)
if st.session_state.get("show_success"):
    st.toast(st.session_state["show_success"], icon="✅")
    del st.session_state["show_success"]

if st.query_params.get("action") == "logout":
    st.session_state["user"] = None
    st.query_params.clear()
    st.rerun()

st.markdown(STREAMLIT_HIDE + """
<style>
    .stApp { background: #0B1610 !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# Diaporama — images embarquées (pas de URLs externes dans l'iframe)
slides_html = accueil_slides_html()

# Définition des boutons selon l'état de connexion
if not st.session_state.get("user"):
    buttons_html = """
    <a href="/Connexion" target="_self" class="btn-link btn-primary">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline; margin-right:6px;">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
        Se connecter
    </a>
    <a href="/Inscription" target="_self" class="btn-link btn-secondary">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline; margin-right:6px;">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
            <line x1="12" y1="12" x2="12" y2="18"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
        Créer un compte
    </a>
    """
else:
    buttons_html = """
    <a href="/Tableau_de_bord" target="_self" class="btn-link btn-primary">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline; margin-right:6px;">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        Tableau de bord
    </a>
    <a href="/?action=logout" target="_self" class="btn-link btn-danger">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline; margin-right:6px;">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        Déconnexion
    </a>
    """

# 4. Design agritech 2026 — hero split + cartes glanceables
design_final = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{ACCUEIL_CSS}
        .stApp-hook {{ display:none; }}
        .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    </style>
</head>
<body>
    <div class="hero" id="slideshow-container">
        {slides_html}
        <div class="hero-overlay"></div>
        <div class="hero-grid">
            <div class="hero-copy">
                <div class="eyebrow">🌱 AgroSmart · IoT · IA</div>
                <h1>Agriculture<br><span>intelligente</span></h1>
                <p class="lead">Optimisez l'irrigation et diagnostiquez la santé de vos sols en temps réel grâce aux capteurs IoT et à l'intelligence artificielle.</p>
                <div class="feature-row">
                    <div class="feature-pill"><span class="dot"></span>Capteurs IoT</div>
                    <div class="feature-pill"><span class="dot"></span>Machine Learning</div>
                    <div class="feature-pill"><span class="dot"></span>Irrigation</div>
                    <div class="feature-pill"><span class="dot"></span>Diagnostic sol</div>
                </div>
            </div>
            <div class="hero-card">
                <div class="card-icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                        <path d="M12 22V12M12 12C12 12 8 8 8 4a4 4 0 0 1 8 0c0 4-4 8-4 8z"/>
                        <path d="M12 18c-3 0-5 2-5 4"/>
                        <path d="M12 18c3 0 5 2 5 4"/>
                    </svg>
                </div>
                <h2>AgroSmart</h2>
                <p>Votre plateforme de pilotage agricole — décisions claires, données en direct.</p>
                {buttons_html}
                <div class="hero-footer">© 2026 AgroSmart · RDC</div>
            </div>
        </div>
    </div>
    <script>
        let current = 0;
        const slides = () => document.querySelectorAll('.slide');
        setInterval(() => {{
            const s = slides();
            if (!s.length) return;
            s[current].classList.remove('active');
            current = (current + 1) % s.length;
            s[current].classList.add('active');
        }}, 6000);
    </script>
</body>
</html>
"""

st.components.v1.html(design_final, height=780, scrolling=False)