import streamlit as st
import os, random, string, smtplib, datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ui.theme import AUTH_CSS, STREAMLIT_HIDE, auth_visual_img_tag

from auth import (
    authenticate_user,
    save_reset_code,
    verify_reset_code,
    update_user_password,
)
from db.neon import ensure_schema, get_user_by_email

ensure_schema()

from config import CODE_EXPIRY_MINUTES

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


st.set_page_config(page_title="AgroSmart – Connexion", layout="wide", initial_sidebar_state="collapsed")
st.set_option("client.showSidebarNavigation", False)

# ── Navigation entrante ──
if "goto" in st.query_params:
    dest = st.query_params["goto"]
    if dest == "register":
        st.switch_page("pages/Inscription.py")

if st.session_state.get("reg_success"):
    st.toast(st.session_state["reg_success"], icon="✅")
    del st.session_state["reg_success"]


# ── Styles Streamlit ──
st.markdown(STREAMLIT_HIDE + """
<style>
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100vw !important; margin-top: 0 !important; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stApp"],
    section[data-testid="stMain"] > div, [data-testid="stVerticalBlock"] {
        margin: 0 !important; padding: 0 !important; background: #F7F4EE !important;
    }
    iframe { display: block !important; background: #F7F4EE; }
</style>
""", unsafe_allow_html=True)

auth_bg_img = auth_visual_img_tag()

# ══════════════════════════════════════
#  LOGIQUE RÉINITIALISATION MOT DE PASSE
# ══════════════════════════════════════
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_reset_email(to_email: str, code: str) -> bool:
    try:
        from config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "AgroSmart – Code de réinitialisation"
        msg["From"]    = f"AgroSmart <{EMAIL_ADDRESS}>"
        msg["To"]      = to_email

        html_body = f"""
        <div style="font-family:Poppins,sans-serif;max-width:480px;margin:auto;background:#f8fdf9;
                    border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.1)">
          <div style="background:#1a4a35;padding:32px 40px;text-align:center">
            <h1 style="color:#fff;font-size:1.6rem;margin:0;display:flex;align-items:center;justify-content:center;gap:8px">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l2 8h-4l2 8-6-6 6-10z"/>
              </svg>
              AgroSmart
            </h1>
            <p style="color:#9dccaa;margin:6px 0 0;font-size:.85rem">
              Réinitialisation de mot de passe
            </p>
          </div>
          <div style="padding:36px 40px">
            <p style="color:#2d4a35;font-size:.95rem;line-height:1.6">
              Bonjour,<br><br>
              Vous avez demandé la réinitialisation de votre mot de passe AgroSmart.<br>
              Voici votre code de vérification valable <strong>10 minutes</strong> :
            </p>
            <div style="text-align:center;margin:28px 0">
              <span style="font-size:2.4rem;font-weight:800;letter-spacing:12px;
                           color:#1a4a35;background:#e8f5eb;padding:16px 28px;
                           border-radius:12px;display:inline-block">
                {code}
              </span>
            </div>
            <p style="color:#666;font-size:.82rem;line-height:1.5">
              Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.<br>
              Votre mot de passe ne sera pas modifié.
            </p>
          </div>
          <div style="background:#f0f4f0;padding:16px;text-align:center">
            <p style="color:#aaa;font-size:.72rem;margin:0">
              © 2026 AgroSmart
            </p>
          </div>
        </div>
        """
        msg.attach(MIMEText(html_body, "html"))

        import time
        start_time = time.time()
        
        with open("login_debug.log", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] SMTP: Connexion à {SMTP_SERVER}:{SMTP_PORT}...\n")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            with open("login_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] SMTP: Connecté. ({time.time()-start_time:.2f}s). EHLO...\n")
            server.ehlo()
            
            with open("login_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] SMTP: STARTTLS... ({time.time()-start_time:.2f}s)\n")
            server.starttls()
            
            with open("login_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] SMTP: Login en cours... ({time.time()-start_time:.2f}s)\n")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            
            with open("login_debug.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] SMTP: Envoi à {to_email}... ({time.time()-start_time:.2f}s)\n")
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
            
        with open("login_debug.log", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] SMTP: Terminé avec succès ! Temps total : {time.time()-start_time:.2f}s\n")
        return True
    except Exception as e:
        import time
        with open("login_debug.log", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] SMTP ERROR: {e}\n")
        st.session_state["reset_error"] = str(e)
        return False

# ── Gestion des actions ──
action = st.query_params.get("action", "")

import time
with open("login_debug.log", "a") as f:
    f.write(f"[{time.strftime('%H:%M:%S')}] Connexion.py loaded. Action: '{action}', Session user: '{st.session_state.get('user', '')}'\n")

# ── Gestion des actions AJAX ──
action = st.query_params.get("action", "")

JS_BCAST = """<script>let p=window.parent;while(p){p.postMessage({msg}, '*');if(p===window.top)break;p=p.parent;}</script>"""

if action == "login_ajax":
    email = st.query_params.get("email", "").strip()
    pwd = st.query_params.get("pwd", "")
    try:
        user_id = authenticate_user(email, pwd)
        if user_id:
            msg = f"{{type: 'login_result', success: true, uid: '{user_id}'}}"
        else:
            msg = "{type: 'login_result', success: false, msg: 'Email ou mot de passe incorrect.'}"
    except Exception:
        msg = "{type: 'login_result', success: false, msg: 'Erreur lors de la connexion.'}"
    st.components.v1.html(JS_BCAST.replace("{msg}", msg))
    st.stop()

if action == "forgot_ajax":
    email_to = st.query_params.get("email", "").strip()

    try:
        user = get_user_by_email(email_to)
        if not user:
            st.components.v1.html(
                JS_BCAST.replace(
                    "{msg}",
                    "{type: 'forgot_result', success: false, msg: 'Aucun compte associé à cet email.'}",
                )
            )
            st.stop()

        code = generate_code()
        save_reset_code(email_to, code, CODE_EXPIRY_MINUTES)
        ok = send_reset_email(email_to, code)
        if ok:
            st.components.v1.html(JS_BCAST.replace("{msg}", "{type: 'forgot_result', success: true}"))
        else:
            st.components.v1.html(
                JS_BCAST.replace(
                    "{msg}",
                    "{type: 'forgot_result', success: false, msg: 'Erreur lors de l envoi du mail.'}",
                )
            )
    except Exception:
        st.components.v1.html(
            JS_BCAST.replace(
                "{msg}",
                "{type: 'forgot_result', success: false, msg: 'Erreur lors de la vérification.'}",
            )
        )
    st.stop()

if action == "verify_ajax":
    entered = st.query_params.get("code", "").strip()
    email_to = st.query_params.get("email", "").strip()
    if verify_reset_code(email_to, entered):
        st.components.v1.html(JS_BCAST.replace("{msg}", "{type: 'verify_result', success: true}"))
    else:
        st.components.v1.html(
            JS_BCAST.replace(
                "{msg}",
                "{type: 'verify_result', success: false, msg: 'Code incorrect ou expiré.'}",
            )
        )
    st.stop()

if action == "reset_ajax":
    pwd = st.query_params.get("pwd", "")
    email = st.query_params.get("email", "").strip()
    code = st.query_params.get("code", "").strip()

    if verify_reset_code(email, code):
        try:
            if update_user_password(email, pwd):
                st.components.v1.html(JS_BCAST.replace("{msg}", "{type: 'reset_result', success: true}"))
            else:
                st.components.v1.html(
                    JS_BCAST.replace(
                        "{msg}",
                        "{type: 'reset_result', success: false, msg: 'Erreur lors de la réinitialisation.'}",
                    )
                )
        except ValueError as e:
            st.components.v1.html(
                JS_BCAST.replace(
                    "{msg}",
                    f"{{type: 'reset_result', success: false, msg: '{str(e)}'}}",
                )
            )
    else:
        st.components.v1.html(
            JS_BCAST.replace(
                "{msg}",
                "{type: 'reset_result', success: false, msg: 'Session invalide ou expirée.'}",
            )
        )
    st.stop()

if action == "login_success":
    uid = st.query_params.get("uid", "").strip()
    if uid:
        st.session_state["user"] = uid
        st.session_state["show_success"] = "Connexion réussie ! Bienvenue sur AgroSmart."
        with open("login_debug.log", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] Login success registered. User ID: {uid}\n")
    st.query_params.clear()
    st.rerun()



login_error     = st.session_state.get("login_error", "")
if "login_error" in st.session_state: del st.session_state["login_error"]

# Redirection si connecté
if st.session_state.get("user"):
    with open("login_debug.log", "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] Switching page to Tableau_de_bord.py\n")
    st.switch_page("pages/Tableau_de_bord.py")


html_code = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{AUTH_CSS}
</style>
</head>
<body>

<div class="auth-shell">
  <div class="auth-visual">
    {auth_bg_img}
    <div class="auth-visual-content">
      <div class="brand">Agro<span>Smart</span></div>
      <p>Pilotez vos cultures avec des données capteurs en temps réel et des recommandations IA.</p>
      <div class="chips">
        <span class="chip">IoT</span>
        <span class="chip">Diagnostic sol</span>
        <span class="chip">Irrigation</span>
      </div>
    </div>
  </div>
  <div class="auth-panel">
      <h1>Connexion</h1>
      <p class="subtitle">Accédez à votre tableau de bord agricole</p>
      <div class="field-group">
        <label for="email">Adresse Email</label>
        <div class="input-wrap">
          <span class="icon-left">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
            </svg>
          </span>
          <input id="email" type="email" placeholder="exemple@email.com" autocomplete="email" required>
        </div>
      </div>
      <div class="field-group">
        <label for="password">Mot de passe</label>
        <div class="input-wrap">
          <span class="icon-left">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zM9 6c0-1.66 1.34-3 3-3s3 1.34 3 3v2H9V6zm3 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>
            </svg>
          </span>
          <input id="password" type="password" placeholder="••••••••" required>
          <span class="icon-right" id="toggle-pwd-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
            </svg>
          </span>

        </div>
      </div>
      <div class="options">
        <label><input type="checkbox" id="remember"> Se souvenir de moi</label>
        <a id="forgot-link" href="javascript:void(0);" onclick="openForgot()">Mot de passe oublié ?</a>
      </div>
      <button class="btn-primary" id="login-btn" onclick="handleLogin()">Se connecter</button>

      <div id="feedback"></div>
      <p class="auth-footer">Vous n'avez pas de compte ?
        <a href="/Inscription">Créez-en un</a>
      </p>
  </div>
</div>

<!-- ══ MODAL MOT DE PASSE OUBLIÉ ══ -->
<div class="modal-backdrop" id="modalBackdrop">
  <div class="modal">
    <h2 style="display:flex;align-items:center;gap:8px">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
      Mot de passe oublié
    </h2>

    <!-- Étape 1 : saisir l'email -->
    <div class="modal-step active" id="step1">
      <p>Entrez votre adresse email pour recevoir un code de vérification.</p>
      <div class="input-wrap" style="margin:0">
        <input id="resetEmail" type="email" placeholder="exemple@email.com">
      </div>
      <div class="modal-feedback" id="fb1"></div>
      <button class="modal-btn" id="send-code-btn" onclick="sendCode()">📨 Envoyer le code</button>
      <button class="modal-btn secondary" id="close-modal-btn" onclick="closeModal()">Annuler</button>

    </div>

    <!-- Étape 2 : saisir le code reçu -->
    <div class="modal-step" id="step2">
      <p id="step2Msg">Un code à 6 chiffres a été envoyé à <strong id="sentTo"></strong></p>
      <input id="codeInput" type="text" maxlength="6" placeholder="000000" inputmode="numeric">
      <div class="modal-feedback" id="fb2"></div>
      <button class="modal-btn" id="verify-code-btn" onclick="verifyCode()">✅ Vérifier le code</button>
      <button class="modal-btn secondary" id="back-step1-btn" onclick="goStep(1)">← Retour</button>

    </div>

    <!-- Étape 3 : nouveau mot de passe -->
    <div class="modal-step" id="step3">
      <p>Code vérifié ✅ Entrez votre nouveau mot de passe.</p>
      <div class="input-wrap" style="margin:0;letter-spacing:normal">
        <input id="newPwd" type="password" placeholder="Nouveau mot de passe" style="letter-spacing:normal;font-size:.9rem;font-weight:400">
      </div>
      <div class="input-wrap" style="margin:0;letter-spacing:normal">
        <input id="confirmPwd" type="password" placeholder="Confirmer le mot de passe" style="letter-spacing:normal;font-size:.9rem;font-weight:400">
      </div>
      <div class="modal-feedback" id="fb3"></div>
      <button class="modal-btn" id="reset-pwd-btn" onclick="resetPassword()">💾 Enregistrer</button>

    </div>

    <!-- Étape 4 : succès -->
    <div class="modal-step" id="step4">
      <p style="font-size:1.8rem;text-align:center">✅</p>
      <p>Votre mot de passe a été réinitialisé avec succès !</p>
      <button class="modal-btn" id="close-modal-success-btn" onclick="closeModal()">Retour à la connexion</button>

    </div>
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


  window.addEventListener('load', () => {{
    if (LOGIN_ERROR) {{
      const fb = document.getElementById('feedback');
      fb.style.color = '#f08080';
      fb.textContent = LOGIN_ERROR;
    }}
  }});

  // Écoute des retours AJAX
  window.addEventListener('message', function(e) {{
      if (e.data.type === 'login_result') {{
          document.getElementById('login-btn').disabled = false;
          const fb = document.getElementById('feedback');
          if (e.data.success) {{
              fb.style.color = '#7ed997'; fb.textContent = 'Connexion réussie ! Redirection...';
              const url = '/Connexion?action=login_success&uid=' + encodeURIComponent(e.data.uid);
              window.postMessage({{type: 'navigate', url: url}}, '*');
          }} else {{
              fb.style.color = '#f08080'; fb.textContent = e.data.msg;
          }}
      }}
      if (e.data.type === 'forgot_result') {{
          document.getElementById('send-code-btn').disabled = false;
          const fb = document.getElementById('fb1');
          if (e.data.success) {{
              const email = document.getElementById('resetEmail').value.trim();
              document.getElementById('sentTo').textContent = email;
              goStep(2);
          }} else {{
              fb.style.color = '#f08080'; fb.textContent = e.data.msg;
          }}
      }}
      if (e.data.type === 'verify_result') {{
          document.getElementById('verify-code-btn').disabled = false;
          const fb = document.getElementById('fb2');
          if (e.data.success) {{
              goStep(3);
          }} else {{
              fb.style.color = '#f08080'; fb.textContent = e.data.msg;
          }}
      }}
      if (e.data.type === 'reset_result') {{
          document.getElementById('reset-pwd-btn').disabled = false;
          const fb = document.getElementById('fb3');
          if (e.data.success) {{
              goStep(4);
          }} else {{
              fb.style.color = '#f08080'; fb.textContent = e.data.msg;
          }}
      }}
  }});

  function togglePwd() {{
    const p = document.getElementById('password');
    p.type = p.type === 'password' ? 'text' : 'password';
  }}

  function handleLogin() {{
    const email = document.getElementById('email').value.trim();
    const pwd   = document.getElementById('password').value;
    const fb    = document.getElementById('feedback');
    const btn   = document.getElementById('login-btn');
    if (!email || !pwd) {{
      fb.style.color = '#f08080'; fb.textContent = 'Veuillez remplir tous les champs.'; return;
    }}
    fb.style.color = '#a4b4ab'; fb.textContent = 'Vérification en cours...';
    btn.disabled = true;
    callAjax('login_ajax', {{ email: email, pwd: pwd }});
  }}

  function openForgot() {{
    document.getElementById('modalBackdrop').classList.add('open');
    goStep(1);
  }}

  function closeModal() {{
    document.getElementById('modalBackdrop').classList.remove('open');
  }}
  function goStep(n) {{
    document.querySelectorAll('.modal-step').forEach(s => s.classList.remove('active'));
    document.getElementById('step' + n).classList.add('active');
  }}

  function callAjax(action, params) {{
    const iframe = document.createElement('iframe');
    let url = new URL(window.parent.location.origin + window.parent.location.pathname);
    url.searchParams.set('action', action);
    for (const key in params) {{
        url.searchParams.set(key, params[key]);
    }}
    iframe.src = url.toString();
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.position = 'absolute';
    iframe.style.visibility = 'hidden';
    iframe.style.border = 'none';
    document.body.appendChild(iframe);
    
    // Nettoyage après 20 secondes
    setTimeout(() => iframe.remove(), 20000);
  }}

  function sendCode() {{
    const email = document.getElementById('resetEmail').value.trim();
    const fb    = document.getElementById('fb1');
    const btn   = document.getElementById('send-code-btn');
    if (!email || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) {{
      fb.style.color='#f08080'; fb.textContent='Email invalide.'; return;
    }}
    fb.style.color='#7ed997'; fb.textContent='Envoi en cours… Veuillez patienter.';
    btn.disabled = true;
    callAjax('forgot_ajax', {{ email: email }});
  }}

  function verifyCode() {{
    const code = document.getElementById('codeInput').value.trim();
    const email = document.getElementById('resetEmail').value.trim();
    const fb   = document.getElementById('fb2');
    const btn  = document.getElementById('verify-code-btn');
    if (code.length !== 6) {{
      fb.style.color='#f08080'; fb.textContent='Entrez le code à 6 chiffres.'; return;
    }}
    fb.style.color='#7ed997'; fb.textContent='Vérification…';
    btn.disabled = true;
    callAjax('verify_ajax', {{ code: code, email: email }});
  }}

  function resetPassword() {{
    const p1 = document.getElementById('newPwd').value;
    const p2 = document.getElementById('confirmPwd').value;
    const email = document.getElementById('resetEmail').value.trim();
    const code = document.getElementById('codeInput').value.trim();
    const fb = document.getElementById('fb3');
    const btn = document.getElementById('reset-pwd-btn');
    if (p1.length < 6) {{ fb.style.color='#f08080'; fb.textContent='Minimum 6 caractères.'; return; }}
    if (p1 !== p2)     {{ fb.style.color='#f08080'; fb.textContent='Les mots de passe ne correspondent pas.'; return; }}
    
    fb.style.color='#7ed997'; fb.textContent='Mise à jour en cours…';
    if (btn) btn.disabled = true;
    callAjax('reset_ajax', {{ pwd: p1, email: email, code: code }});
  }}
</script>

</body>
</html>
"""

st.components.v1.html(html_code, height=700, scrolling=False)