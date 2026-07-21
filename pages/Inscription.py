import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import register_user
from ui.theme import AUTH_CSS, STREAMLIT_HIDE, auth_visual_img_tag
st.set_page_config(page_title="AgroSmart – Inscription", layout="wide", initial_sidebar_state="collapsed")
st.set_option("client.showSidebarNavigation", False)

st.markdown(STREAMLIT_HIDE + """
<style>
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100vw !important; }
    .stApp { background: #F7F4EE !important; }
</style>
""", unsafe_allow_html=True)

# (Le pont de navigation est intégré dans le bloc HTML plus bas)

action = st.query_params.get("action", "")
if action == "register":
    nom = st.query_params.get("nom", ""); prenom = st.query_params.get("prenom", "")
    sexe = st.query_params.get("sexe", ""); tel = st.query_params.get("tel", "")
    email = st.query_params.get("email", ""); pwd = st.query_params.get("password", "")
    if email and pwd:
        try:
            register_user(nom, prenom, sexe, tel, email, pwd)
            st.session_state["reg_success"] = "Compte créé avec succès ! Connectez-vous maintenant."
            st.query_params.clear()
            st.switch_page("pages/Connexion.py")
        except Exception as e: st.session_state["reg_error"] = str(e)
    st.query_params.clear(); st.rerun()

# Pas de redirection automatique — l'utilisateur doit se connecter manuellement
reg_error = st.session_state.get("reg_error", "")

auth_bg_img = auth_visual_img_tag()

html_code = f"""
<style>{AUTH_CSS}</style>
<div class="auth-shell">
<div class="auth-visual">
{auth_bg_img}
<div class="auth-visual-content">
<div class="brand">Agro<span>Smart</span></div>
<p>Rejoignez la communauté des agriculteurs connectés en RDC.</p>
<div class="chips"><span class="chip">Gratuit</span><span class="chip">IoT</span><span class="chip">IA</span></div>
</div>
</div>
<div class="auth-panel">
<h1>Inscription</h1>
<p class="subtitle">Créez votre compte agriculteur</p>
<div class="auth-row">
<div class="field-group"><label>Nom</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></span><input type="text" id="nom" placeholder="Nom" required></div></div>
<div class="field-group"><label>Prénom</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></span><input type="text" id="prenom" placeholder="Prénom" required></div></div>
</div>
<div class="auth-row">
<div class="field-group"><label>Sexe</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></span><select id="sexe" required><option value="">--</option><option value="homme">Homme</option><option value="femme">Femme</option></select></div></div>
<div class="field-group"><label>Téléphone</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6.62 10.79c1.44 2.83 3.76 5.15 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg></span><input type="tel" id="tel" placeholder="+243..." required></div></div>
</div>
<div class="field-group"><label>Email</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg></span><input type="email" id="email" placeholder="exemple@mail.com" required></div></div>
<div class="field-group"><label>Mot de passe</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2z"/></svg></span><input type="password" id="pwd" placeholder="••••••••" required><span class="icon-right" onclick="toggleVis('pwd')"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg></span></div></div>
<div class="field-group"><label>Confirmer</label><div class="input-wrap"><span class="icon-left"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10z"/></svg></span><input type="password" id="conf" placeholder="••••••••" required><span class="icon-right" onclick="toggleVis('conf')"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg></span></div></div>
<button class="btn-primary" id="reg-btn" onclick="handleReg()">S'inscrire</button>
<div id="fb" class="auth-feedback"></div>
<p class="auth-footer">Déjà un compte ? <a href="/Connexion">Connectez-vous</a></p>
</div>
</div>
<script>
// Pont de navigation intégré
if (!window.hasAgroSmartBridge) {{
    window.hasAgroSmartBridge = true;
    window.addEventListener('message', function(event) {{
        if (event.data && event.data.type === 'navigate') {{
            window.location.href = event.data.url;
        }}
    }});
}}

function toggleVis(id){{
    const i = document.getElementById(id);
    i.type = i.type === 'password' ? 'text' : 'password';
}}

function handleReg(){{
    const n = document.getElementById('nom').value;
    const p = document.getElementById('prenom').value;
    const s = document.getElementById('sexe').value;
    const t = document.getElementById('tel').value;
    const e = document.getElementById('email').value;
    const w = document.getElementById('pwd').value;
    const c = document.getElementById('conf').value;
    const fb = document.getElementById('fb');
    
    if(!n||!p||!e||!w||!c){{fb.textContent="Tous les champs sont requis"; return;}}
    if(w!==c){{fb.textContent="Les mots de passe ne correspondent pas"; return;}}
    
    fb.style.color='#7ed997';
    fb.textContent='Inscription réussie ! Redirection...';
    
    const url = '/Inscription?action=register&nom='+encodeURIComponent(n)+'&prenom='+encodeURIComponent(p)+'&sexe='+encodeURIComponent(s)+'&tel='+encodeURIComponent(t)+'&email='+encodeURIComponent(e)+'&password='+encodeURIComponent(w);
    window.postMessage({{type: 'navigate', url: url}}, '*');
}}

// Affichage de l'erreur au chargement
const regError = "{reg_error}";
if (regError) {{
    const fb = document.getElementById('fb');
    if (fb) {{
        fb.textContent = regError;
        fb.style.color = '#f08080';
    }}
}}
</script>
"""
st.components.v1.html(html_code, height=720, scrolling=False)