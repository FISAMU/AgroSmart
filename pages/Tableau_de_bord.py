import streamlit as st
import base64
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from logic import diagnostic, irrigation # Importation de tes modules

# 1. Actualisation automatique (10 secondes) — sera activée seulement sur le Tableau de bord
# (évite les rechargements continus sur les pages Diagnostic / Irrigation)

# 2. Configuration de la page
st.set_page_config(page_title="AgroSmart - Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Initialisation Firebase
if not firebase_admin._apps:
    base_path = os.path.dirname(os.path.dirname(__file__))
    key_path = os.path.join(base_path, "serviceAccountKey.json")
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)

db = firestore.client()

# --- FONCTIONS D'ESPACES (AJOUTS) ---

def _get_latest_value(latest, keys, default=None):
    if latest is None:
        return default
    for key in keys:
        if key in latest and pd.notna(latest.get(key)):
            return latest.get(key)
    return default


def _choice_index(value, choices):
    try:
        return choices.index(value)
    except ValueError:
        return 0


def afficher_diagnostic_espace(db, latest):
    st.subheader("Analyse de santé du sol")
    cultures_docs = db.collection("cultures_ref").stream()
    noms_cultures = [doc.id for doc in cultures_docs]
    culture = st.selectbox("Sélectionnez votre culture :", noms_cultures)
    st.session_state["selected_crop"] = culture

    # Options adaptées au cas de Kinshasa / RDC (libellés pour l'utilisateur)
    soil_type_options = ["Argileux", "Loameux", "Sableux", "Limon"]
    growth_stage_options = ["Semis", "Végétatif", "Floraison", "Récolte"]
    season_options = ["Saison des pluies", "Saison sèche"]
    mulching_options = ["No", "Yes"]
    # Liste de communes/secteurs représentatifs de Kinshasa
    region_options = [
        "Gombe", "Lingwala", "Kintambo", "Bandalungwa", "Kasa-Vubu",
        "Kalamu", "Ngiri-Ngiri", "Bumbu", "Ngaliema", "Lemba",
        "Selembao", "Masina", "N'djili", "Mont-Ngafula", "Kimbanseke"
    ]

    soil_type = st.selectbox(
        "Type de sol",
        soil_type_options,
        index=_choice_index(_get_latest_value(latest, ["Soil_Type"], "Loamy"), soil_type_options)
    )
    st.session_state["selected_soil_type"] = soil_type
    growth_stage = st.selectbox(
        "Stade de croissance",
        growth_stage_options,
        index=_choice_index(_get_latest_value(latest, ["Crop_Growth_Stage"], "Vegetative"), growth_stage_options)
    )
    season = st.selectbox(
        "Saison",
        season_options,
        index=_choice_index(_get_latest_value(latest, ["Season"], "Kharif"), season_options)
    )
    mulching_used = st.selectbox(
        "Paillage utilisé",
        mulching_options,
        index=_choice_index(_get_latest_value(latest, ["Mulching_Used"], "No"), mulching_options)
    )
    region = st.selectbox(
        "Région",
        region_options,
        index=_choice_index(_get_latest_value(latest, ["Region"], "Central"), region_options)
    )

    irrigation_type = st.session_state.get(
        "selected_irrigation_type",
        _get_latest_value(latest, ["Irrigation_Type"], "Drip")
    )
    water_source = st.session_state.get(
        "selected_water_source",
        _get_latest_value(latest, ["Water_Source"], "Groundwater")
    )

    soil_ph = float(_get_latest_value(latest, ["ph", "Soil_pH"], 6.5))
    humidity = float(_get_latest_value(latest, ["humidite", "Humidity"], 35.0))
    temperature = float(_get_latest_value(latest, ["temperature", "Temperature_C"], 25.0))

    with st.form("diagnostic_form"):
        st.markdown("### Paramètres environnementaux")
        soil_moisture = st.number_input(
            "Humidité du sol (%)",
            value=float(_get_latest_value(latest, ["Soil_Moisture"], 35.0)),
            format="%.2f"
        )
        organic_carbon = st.number_input(
            "Carbone organique (%)",
            value=float(_get_latest_value(latest, ["Organic_Carbon"], 1.5)),
            format="%.2f"
        )
        electrical_conductivity = st.number_input(
            "Conductivité électrique (dS/m)",
            value=float(_get_latest_value(latest, ["Electrical_Conductivity"], 0.7)),
            format="%.2f"
        )
        rainfall = st.number_input(
            "Précipitations (mm)",
            value=float(_get_latest_value(latest, ["Rainfall_mm"], 2.0)),
            format="%.2f"
        )
        sunlight = st.number_input(
            "Heures de soleil",
            value=float(_get_latest_value(latest, ["Sunlight_Hours"], 8.0)),
            format="%.2f"
        )
        wind_speed = st.number_input(
            "Vent (km/h)",
            value=float(_get_latest_value(latest, ["Wind_Speed_kmh"], 5.0)),
            format="%.2f"
        )
        field_area = st.number_input(
            "Surface du champ (hectares)",
            value=float(_get_latest_value(latest, ["Field_Area_hectare"], 1.0)),
            format="%.2f"
        )
        previous_irrigation = st.number_input(
            "Irrigation précédente (mm)",
            value=float(_get_latest_value(latest, ["Previous_Irrigation_mm"], 0.0)),
            format="%.2f"
        )

        submitted = st.form_submit_button("Lancer le diagnostic")

    if submitted:
        st.info("Diagnostic lancé...")
        try:
            features = {
                "Soil_Type": soil_type,
                "Crop_Type": culture,
                "Crop_Growth_Stage": growth_stage,
                "Season": season,
                "Irrigation_Type": irrigation_type,
                "Water_Source": water_source,
                "Mulching_Used": mulching_used,
                "Region": region,
                "Soil_pH": soil_ph,
                "Soil_Moisture": soil_moisture,
                "Organic_Carbon": organic_carbon,
                "Electrical_Conductivity": electrical_conductivity,
                "Temperature_C": temperature,
                "Humidity": humidity,
                "Rainfall_mm": rainfall,
                "Sunlight_Hours": sunlight,
                "Wind_Speed_kmh": wind_speed,
                "Field_Area_hectare": field_area,
                "Previous_Irrigation_mm": previous_irrigation,
            }
            # Traduire certaines valeurs utilisateur vers les catégories attendues
            soil_map = {"Argileux": "Clay", "Loameux": "Loamy", "Sableux": "Sandy", "Limon": "Silt"}
            stage_map = {"Semis": "Sowing", "Végétatif": "Vegetative", "Floraison": "Flowering", "Récolte": "Harvest"}
            season_map = {"Saison des pluies": "Kharif", "Saison sèche": "Rabi"}

            features_for_model = features.copy()
            features_for_model["Type_Sol"] = soil_map.get(soil_type, soil_type)
            features_for_model["Stade_Croissance"] = stage_map.get(growth_stage, growth_stage)
            features_for_model["Saison"] = season_map.get(season, season)

            result = diagnostic.run_diagnostic(features_for_model)
            etat_ia = result.get("etat_ia")
            etat_ia_explanation = result.get("etat_ia_explanation", "")
            irrigation_factors = result.get("irrigation_factors", {})
            etat_expert = diagnostic.obtenir_etat_sol(soil_ph, humidity, culture)

            col_ia, col_expert = st.columns(2)
            with col_ia:
                st.subheader("Résultat IA")
                st.write(etat_ia)
                if etat_ia_explanation:
                    st.caption(etat_ia_explanation)
            with col_expert:
                st.subheader("Résultat expert")
                st.markdown(f"{etat_expert}")

            st.markdown("### Facteurs calculés pour l'irrigation")
            st.json(irrigation_factors)

            st.markdown("### Entrées envoyées au modèle (après mapping)")
            st.json(features_for_model)
            st.session_state["diagnostic_submitted"] = True
        except Exception as e:
            # Affiche l'exception complète pour debug côté UI
            st.error("Erreur lors du diagnostic. Voir détails ci-dessous.")
            st.exception(e)

    if st.session_state.get("diagnostic_submitted", False):
        if st.button("Passer à l'irrigation", use_container_width=True):
            st.session_state.active_interface = "Irrigation"
            st.session_state["diagnostic_submitted"] = False
            st.rerun()

def afficher_irrigation_espace(db, latest):
    st.subheader("Gestion de l'irrigation")
    selected_crop = st.session_state.get("selected_crop")
    cultures_docs = db.collection("cultures_ref").stream()
    noms_cultures = [doc.id for doc in cultures_docs]

    if selected_crop:
        culture = selected_crop
        st.markdown(f"**Culture sélectionnée dans le diagnostic :** {culture}")
        if st.button("Modifier la culture pour l'irrigation"):
            selected_crop = None
            st.session_state.pop("selected_crop", None)
            st.rerun()
    else:
        culture = st.selectbox("Culture concernée :", noms_cultures)

    soil_type_options = {
        "Sec": "DRY",
        "Humide": "HUMID",
        "Très humide": "WET",
    }
    region_options = {
        "Désert": "DESERT",
        "Semi aride": "SEMI ARID",
        "Semi humide": "SEMI HUMID",
        "Humide": "HUMID",
    }
    weather_options = {
        "Normal": "NORMAL",
        "Pluvieux": "RAINY",
        "Ensoleillé": "SUNNY",
        "Venteux": "WINDY",
    }

    session_soil_type = st.session_state.get("selected_soil_type")
    diagnostic_soil_to_irrigation = {
        "Argileux": "Humide",
        "Loameux": "Humide",
        "Sableux": "Sec",
        "Limon": "Humide",
    }
    chosen_soil_default = diagnostic_soil_to_irrigation.get(session_soil_type, "Humide")

    sensor_soil_type = _get_latest_value(latest, ["SOIL TYPE", "Soil_Type"], None)
    sensor_region = _get_latest_value(latest, ["REGION", "Region"], None)
    sensor_weather = _get_latest_value(latest, ["WEATHER CONDITION"], None)
    sensor_temp_avg = _get_latest_value(latest, ["TEMP_AVG", "Temperature_C", "temperature"], 25.0)

    sensor_available = bool(sensor_soil_type and sensor_region and sensor_weather)

    if sensor_available:
        st.success("Données capteur disponibles pour l'irrigation")
        st.markdown("### Valeurs capteur utilisées")
        st.json({
            "Type_Culture": culture,
            "Type_Sol": sensor_soil_type,
            "REGION": sensor_region,
            "Temperature_Moyenne": float(sensor_temp_avg),
            "Condition_Meteo": sensor_weather,
        })

    use_sensor = st.checkbox(
        "Utiliser les données capteur pour la prédiction",
        value=sensor_available,
        help="Si les données capteurs sont disponibles, elles seront envoyées au modèle d'irrigation."
    )

    reverse_soil = {v: k for k, v in soil_type_options.items()}
    reverse_region = {v: k for k, v in region_options.items()}
    reverse_weather = {v: k for k, v in weather_options.items()}

    chosen_soil = st.selectbox(
        "Type de sol :",
        list(soil_type_options.keys()),
        index=list(soil_type_options.keys()).index(chosen_soil_default) if chosen_soil_default in soil_type_options else 1
    )
    chosen_region = st.selectbox(
        "Région climatique :",
        list(region_options.keys()),
        index=list(region_options.keys()).index(reverse_region.get(sensor_region, "Humide")) if sensor_region in reverse_region else 1
    )
    chosen_weather = st.selectbox(
        "Condition météo :",
        list(weather_options.keys()),
        index=list(weather_options.keys()).index(reverse_weather.get(sensor_weather, "Normal")) if sensor_weather in reverse_weather else 0
    )

    irrigation_type_options = ["Canal", "Drip", "Rainfed", "Sprinkler"]
    water_source_options = ["Groundwater", "Rainwater", "Reservoir", "River"]
    chosen_irrigation_type = st.selectbox(
        "Type d'irrigation :",
        irrigation_type_options,
        index=irrigation_type_options.index(st.session_state.get("selected_irrigation_type", "Drip")) if st.session_state.get("selected_irrigation_type") in irrigation_type_options else 0
    )
    chosen_water_source = st.selectbox(
        "Source d'eau :",
        water_source_options,
        index=water_source_options.index(st.session_state.get("selected_water_source", "Groundwater")) if st.session_state.get("selected_water_source") in water_source_options else 0
    )
    st.session_state["selected_irrigation_type"] = chosen_irrigation_type
    st.session_state["selected_water_source"] = chosen_water_source

    temp_avg = st.number_input(
        "Température moyenne (°C)",
        value=float(sensor_temp_avg or 25.0),
        format="%.1f"
    )

    if st.button("Calculer la dose d'eau"):
        if use_sensor and sensor_available:
            soil_code = str(sensor_soil_type).strip().upper()
            region_code = str(sensor_region).strip().upper()
            weather_code = str(sensor_weather).strip().upper()
            temp_avg_val = float(sensor_temp_avg)
        else:
            soil_code = soil_type_options[chosen_soil]
            region_code = region_options[chosen_region]
            weather_code = weather_options[chosen_weather]
            temp_avg_val = float(temp_avg)

        dose = irrigation.predire_quantite_eau_ia(
            culture,
            soil_code,
            region_code,
            temp_avg_val,
            weather_code,
        )

        st.success(f"Dose recommandée pour {culture} : {dose} Litres")
        st.markdown("### Paramètres utilisés pour le modèle d'irrigation")
        st.json({
            "Type_Culture": culture,
            "Type_Sol": soil_code,
            "Region": region_code,
            "Temperature_Moyenne": temp_avg_val,
            "Condition_Meteo": weather_code,
            "Type_Irrigation": chosen_irrigation_type,
            "Source_Eau": chosen_water_source,
            "Source_Donnees": "Capteur" if use_sensor and sensor_available else "Manuel",
        })

# 3. Vérification de la connexion
if not st.session_state.get("user"):
    st.warning("Veuillez vous connecter pour accéder au tableau de bord.")
    st.switch_page("pages/Connexion.py")
    st.stop()

user_id = st.session_state.get("user")
db.collection("config").document("simulator").set({"active_user_id": user_id})

if "active_interface" not in st.session_state:
    st.session_state.active_interface = "Tableau de bord"

# Activer l'auto-refresh uniquement quand on est sur le Tableau de bord
if st.session_state.active_interface == "Tableau de bord":
    st_autorefresh(interval=10000, key="datarefresh")

with st.container():
    with st.popover("☰ Menu"):
        if st.button("📊 Tableau de bord", use_container_width=True):
            st.session_state.active_interface = "Tableau de bord"; st.rerun()
        if st.button("🌱 Diagnostic pédologique", use_container_width=True):
            st.session_state.active_interface = "Diagnostic pédologique"; st.rerun()
        if st.button("💧 Irrigation", use_container_width=True):
            st.session_state.active_interface = "Irrigation"; st.rerun()
        if st.button("⚙️ Paramètres", use_container_width=True):
            st.session_state.active_interface = "Paramètres"; st.rerun()

# 4. Récupération des données (Placement ici pour avoir 'latest' dispo partout)
user_name, user_initial = "Agriculteur", "A"
current_temp, current_hum, current_ph = "--", "--", "--"
df, latest = pd.DataFrame(), None

try:
    u_doc = db.collection("users").document(user_id).get()
    if u_doc.exists:
        u_data = u_doc.to_dict()
        user_name = u_data.get("prenom", "Agriculteur").capitalize()
        user_initial = user_name[0].upper()
    query = db.collection("users").document(user_id).collection("donnees_capteurs").order_by("timestamp", direction="DESCENDING").limit(30).get()
    if query:
        data_list = [d.to_dict() for d in query]
        df = pd.DataFrame(data_list)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values("timestamp")
        latest = df.iloc[-1]
        current_temp = f"{latest.get('temperature', latest.get('temp', '--'))} °C"
        current_hum = f"{latest.get('humidite', latest.get('humidity', '--'))} %"
        current_ph = str(latest.get('ph', '--'))
except Exception as e:
    st.error(f"Erreur : {e}")

# Navigation logic
if st.session_state.active_interface != "Tableau de bord":
    st.markdown(f"<h1 style='color: #7ed997;'>{st.session_state.active_interface}</h1>", unsafe_allow_html=True)
    # Appeler les interfaces même si 'latest' est None : la fonction utilise des valeurs par défaut
    if st.session_state.active_interface == "Diagnostic pédologique":
        if latest is None:
            st.warning("Données capteurs indisponibles. Utilisation de valeurs par défaut pour le diagnostic.")
        afficher_diagnostic_espace(db, latest)
    elif st.session_state.active_interface == "Irrigation":
        if latest is None:
            st.warning("Données capteurs indisponibles. Utilisation de valeurs par défaut pour l'irrigation.")
        afficher_irrigation_espace(db, latest)
    elif st.session_state.active_interface == "Paramètres":
        st.info("Interface Paramètres")
    if st.button("⬅️ Retour au Tableau de bord"):
        st.session_state.active_interface = "Tableau de bord"; st.rerun()
    st.stop()

# 5. Dashboard Design
st.markdown("<style>#MainMenu, header, footer {visibility: hidden !important;} [data-testid='stSidebar'] {display: none !important;} .stApp {background-color: #0f1a14;}</style>", unsafe_allow_html=True)

html_dashboard = f"""
<div style="font-family: 'Poppins', sans-serif; color: white;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="font-size: 1.8rem; color: #7ed997;">Bonjour, {user_name} 👋</h1>
        <div style="background: rgba(255,255,255,0.05); padding: 5px 15px; border-radius: 20px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 30px; background: #7ed997; border-radius: 50%; color: #0f1a14; display: flex; align-items: center; justify-content: center; font-weight: bold;">{user_initial}</div>
            <span>{user_name}</span>
        </div>
    </div>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(126, 217, 151, 0.2); border-radius: 15px; padding: 20px; text-align: center;">
            <span style="color:#a4b4ab;">🌡️ Température</span><div style="font-size: 1.5rem; font-weight: bold; color: #7ed997;">{current_temp}</div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(126, 217, 151, 0.2); border-radius: 15px; padding: 20px; text-align: center;">
            <span style="color:#a4b4ab;">💧 Humidité</span><div style="font-size: 1.5rem; font-weight: bold; color: #7ed997;">{current_hum}</div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(126, 217, 151, 0.2); border-radius: 15px; padding: 20px; text-align: center;">
            <span style="color:#a4b4ab;">🧪 pH Sol</span><div style="font-size: 1.5rem; font-weight: bold; color: #7ed997;">{current_ph}</div>
        </div>
    </div>
</div>
"""
st.components.v1.html(html_dashboard, height=200)

if not df.empty:
    st.write("---")
    st.subheader("📈 Évolution des paramètres")
    fig = px.line(df, x="timestamp", y=[c for c in ['temperature', 'humidite', 'temp', 'humidity'] if c in df.columns], template="plotly_dark", color_discrete_sequence=["#7ed997", "#3d85c6"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Lancez le simulateur pour voir les graphiques.")