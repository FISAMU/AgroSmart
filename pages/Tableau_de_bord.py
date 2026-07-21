import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from logic import diagnostic, irrigation
from db.neon import (
    ensure_schema,
    get_user,
    list_culture_names,
    get_sensor_readings,
    set_config,
)

from ui.theme import (
    STREAMLIT_DASHBOARD,
    render_dashboard_sidebar,
    COLORS,
    SVG,
)

ensure_schema()

CHART_POINTS = 60
LIVE_REFRESH_SECONDS = 10


def _load_sensor_data(user_id: str):
    """Charge uniquement les données capteurs (sans requête utilisateur)."""
    current_temp, current_hum, current_ph = "--", "--", "--"
    df, latest = pd.DataFrame(), None
    readings = get_sensor_readings(user_id, limit=CHART_POINTS)
    if readings:
        df = pd.DataFrame(readings)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        latest = df.iloc[-1]
        current_temp = f"{latest.get('temperature', latest.get('temp', '--'))} °C"
        current_hum = f"{latest.get('humidite', latest.get('humidity', '--'))} %"
        current_ph = str(latest.get("ph", "--"))
    return current_temp, current_hum, current_ph, df, latest


def _load_dashboard_user(user_id: str) -> tuple[str, str]:
    if st.session_state.get("dash_user_id") != user_id:
        st.session_state.dash_user_id = user_id
        st.session_state.pop("dash_user_name", None)
    if "dash_user_name" not in st.session_state:
        u_data = get_user(user_id)
        name = u_data.get("prenom", "Agriculteur").capitalize() if u_data else "Agriculteur"
        st.session_state.dash_user_name = name
    user_name = st.session_state.dash_user_name
    return user_name, user_name[0].upper()


def render_dashboard_header(user_name: str, user_initial: str, has_data: bool) -> None:
    """En-tête statique — ne clignote pas à chaque refresh."""
    head_left, head_right = st.columns([2.5, 1])
    with head_left:
        st.markdown(f'<p class="dash-page-title">Bonjour, {user_name}</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="dash-page-caption">Suivi en temps réel de vos paramètres agricoles</p>',
            unsafe_allow_html=True,
        )
    with head_right:
        live = "En direct" if has_data else "En attente capteurs"
        st.markdown(
            f'<div class="dash-live-badge"><span class="dash-live-dot"></span>{live}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="text-align:right;font-size:0.82rem;color:{COLORS["text_body"]};margin-top:6px;">'
            f'{user_initial} · {user_name}</div>',
            unsafe_allow_html=True,
        )


@st.fragment(run_every=LIVE_REFRESH_SECONDS)
def render_live_metrics(user_id: str) -> None:
    """Met à jour uniquement métriques + graphique (sans recharger l'en-tête)."""
    try:
        current_temp, current_hum, current_ph, df, _ = _load_sensor_data(user_id)
    except Exception as e:
        st.error(f"Erreur : {e}")
        return

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Température", current_temp, help="Sol · capteur IoT")
    with m2:
        st.metric("Humidité", current_hum, help="Taux d'humidité du sol")
    with m3:
        st.metric("pH Sol", current_ph, help="Acidité · alcalinité")

    if not df.empty:
        fig, last_ts = build_live_chart(df)
        last_label = last_ts.strftime("%H:%M:%S") if last_ts is not None else "—"
        st.markdown(
            f"""
            <div class="dash-chart-card">
              <div class="dash-live-badge" style="justify-content:flex-start;margin-bottom:0.75rem;">
                {SVG["chart"]} Évolution des paramètres
                <span style="margin-left:auto;">Live · MAJ {last_label}</span>
              </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            key="live_chart",
            config={"displayModeBar": False, "staticPlot": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Lancez le simulateur IoT (`python iot_simulator.py`) pour voir les graphiques en direct.")


def render_dashboard_page(user_id: str) -> None:
    user_name, user_initial = _load_dashboard_user(user_id)
    _, _, _, df, _ = _load_sensor_data(user_id)
    render_dashboard_header(user_name, user_initial, not df.empty)
    render_live_metrics(user_id)


def _series(df: pd.DataFrame, *candidates: str) -> pd.Series:
    for name in candidates:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(dtype=float)


def build_live_chart(df: pd.DataFrame):
    """Graphique multi-séries temps réel (température, humidité, pH)."""
    chart_df = df.sort_values("timestamp").tail(CHART_POINTS).copy()
    temp = _series(chart_df, "temperature", "temp", "Temperature_C")
    hum = _series(chart_df, "humidite", "humidity", "Humidity")
    ph = _series(chart_df, "ph", "Soil_pH")
    times = chart_df["timestamp"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=times, y=temp, name="Température (°C)",
            mode="lines+markers",
            line=dict(color="#C2410C", width=2.5),
            marker=dict(size=5),
            hovertemplate="%{y:.2f} °C<extra>Température</extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=times, y=hum, name="Humidité (%)",
            mode="lines+markers",
            line=dict(color="#0369A1", width=2.5),
            marker=dict(size=5),
            hovertemplate="%{y:.2f} %<extra>Humidité</extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=times, y=ph, name="pH sol",
            mode="lines+markers",
            line=dict(color=COLORS["forest"], width=2.5, dash="dot"),
            marker=dict(size=5),
            hovertemplate="%{y:.2f}<extra>pH sol</extra>",
        ),
        secondary_y=True,
    )

    last_ts = times.iloc[-1] if not times.empty else None
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Plus Jakarta Sans, Segoe UI, sans-serif",
        font_color=COLORS["text_dark"],
        margin=dict(l=8, r=8, t=16, b=8),
        height=360,
        hovermode="x unified",
        uirevision="agrosmart-live",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
        xaxis=dict(
            gridcolor="rgba(27,67,50,0.08)",
            showline=False,
            rangeslider=dict(visible=True, thickness=0.06),
            type="date",
        ),
    )
    fig.update_yaxes(
        title_text="Temp. / Humidité",
        gridcolor="rgba(27,67,50,0.08)",
        showline=False,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="pH",
        gridcolor="rgba(27,67,50,0.04)",
        showline=False,
        secondary_y=True,
    )
    return fig, last_ts


st.set_page_config(page_title="AgroSmart - Dashboard", layout="wide", initial_sidebar_state="expanded")
st.set_option("client.showSidebarNavigation", False)
st.markdown(STREAMLIT_DASHBOARD, unsafe_allow_html=True)

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


def afficher_diagnostic_espace(latest):
    st.subheader("Analyse de santé du sol")
    noms_cultures = list_culture_names()
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

def afficher_irrigation_espace(latest):
    st.subheader("Gestion de l'irrigation")
    selected_crop = st.session_state.get("selected_crop")
    noms_cultures = list_culture_names()

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
set_config("active_user_id", user_id)

if "active_interface" not in st.session_state:
    st.session_state.active_interface = "Tableau de bord"

with st.sidebar:
    render_dashboard_sidebar(st.session_state.active_interface)

# 4. Récupération des données pour les sous-pages
user_name, user_initial = "Agriculteur", "A"
current_temp, current_hum, current_ph = "--", "--", "--"
df, latest = pd.DataFrame(), None

try:
    u_data = get_user(user_id)
    if u_data:
        user_name = u_data.get("prenom", "Agriculteur").capitalize()
        user_initial = user_name[0].upper()

    readings = get_sensor_readings(user_id, limit=CHART_POINTS)
    if readings:
        df = pd.DataFrame(readings)
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
    st.markdown(f'<p class="page-title">{st.session_state.active_interface}</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Configurez les paramètres et lancez l\'analyse.</p>', unsafe_allow_html=True)
    # Appeler les interfaces même si 'latest' est None : la fonction utilise des valeurs par défaut
    if st.session_state.active_interface == "Diagnostic pédologique":
        if latest is None:
            st.warning("Données capteurs indisponibles. Utilisation de valeurs par défaut pour le diagnostic.")
        afficher_diagnostic_espace(latest)
    elif st.session_state.active_interface == "Irrigation":
        if latest is None:
            st.warning("Données capteurs indisponibles. Utilisation de valeurs par défaut pour l'irrigation.")
        afficher_irrigation_espace(latest)
    elif st.session_state.active_interface == "Paramètres":
        st.info("Interface Paramètres")
    st.stop()

# 5. Tableau de bord — composants natifs (texte net) + fragment live
render_dashboard_page(user_id)