# logic/diagnostic.py
import joblib
import os
from firebase_admin import firestore

MODEL_DIR = os.path.join("models", "diagnostic")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoder_diagnostic.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "model_diagnostic.pkl")
SCHEMA_PATH = os.path.join(MODEL_DIR, "irrigation_columns.pkl")

def obtenir_etat_sol(ph_actuel, hum_actuelle, nom_culture):
    """
    Logique par défaut (système expert) utilisant Firestore.
    Retourne un conseil lisible par un non-expert.
    """
    try:
        db = firestore.client()
        doc = db.collection("cultures_ref").document(nom_culture).get()
    except Exception as e:
        return f"ERREUR_FIRESTORE:{e}"

    if not doc.exists:
        return "Culture inconnue. Vérifiez le nom de la culture ou ajoutez-la dans Firestore."

    ref = doc.to_dict()
    hum_min = ref.get("hum_min", 0)
    hum_optimal = ref.get("hum_optimal")
    ph_min = ref.get("ph_min", 0)
    ph_max = ref.get("ph_max", 14)

    conseils = []

    if hum_actuelle < hum_min:
        conseils.append(
            f"Humidité trop faible ({hum_actuelle}%). Arrosez modérément et gardez le sol humide, surtout si la culture est sensible."
        )
    elif hum_optimal is not None and hum_actuelle > hum_optimal:
        conseils.append(
            f"Humidité élevée ({hum_actuelle}%). Laissez le sol sécher un peu pour éviter le stress hydrique et le compactage."
        )
    else:
        conseils.append(
            f"Humidité correcte ({hum_actuelle}%). Continuez avec un arrosage régulier et contrôlez le sol tous les quelques jours."
        )

    if ph_actuel < ph_min:
        conseils.append(
            f"Le pH est acide ({ph_actuel}). Ajoutez du calcaire agricole ou de la cendre de bois pour remonter le pH vers la plage recommandée ({ph_min}-{ph_max})."
        )
    elif ph_actuel > ph_max:
        conseils.append(
            f"Le pH est alcalin ({ph_actuel}). Utilisez du soufre ou des matières organiques pour abaisser légèrement le pH vers {ph_min}-{ph_max}."
        )
    else:
        conseils.append(
            f"Le pH est bon ({ph_actuel}). Évitez les amendements trop acides ou trop alcalins et surveillez le sol régulièrement."
        )

    if hum_actuelle >= hum_min and ph_min <= ph_actuel <= ph_max:
        conseils.append(
            "Le sol est en bon état pour cette culture. Maintenez ces pratiques et observez l'évolution des plantes."
        )

    return " ".join(conseils)


def _load_diagnostic_schema():
    if os.path.exists(SCHEMA_PATH):
        schema = joblib.load(SCHEMA_PATH)
        if isinstance(schema, dict):
            return schema.get("categorical_cols", []), schema.get("numeric_cols", [])
    return [], []


def get_diagnostic_ia(features: dict):
    """
    Utilise le modèle de diagnostic entraîné dans models/diagnostic.
    Attends un dictionnaire avec les colonnes catégorielles et numériques nécessaires.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        return "MODELE_NON_DISPONIBLE"

    categorical_cols, numeric_cols = _load_diagnostic_schema()
    if not categorical_cols or not numeric_cols:
        return "SCHEMA_INDISPONIBLE"

    encoder = joblib.load(ENCODER_PATH)
    model = joblib.load(MODEL_PATH)

    categorical_values = []
    for col in categorical_cols:
        if col not in features:
            raise ValueError(f"Colonne manquante pour le diagnostic IA: {col}")
        categorical_values.append(features[col])

    numeric_values = []
    for col in numeric_cols:
        if col not in features:
            raise ValueError(f"Colonne manquante pour le diagnostic IA: {col}")
        numeric_values.append(float(features[col]))

    encoded = encoder.transform([categorical_values])[0].tolist()
    row = encoded + numeric_values
    prediction = model.predict([row])
    return prediction[0]


def explain_ia_state(state: str):
    mapping = {
        "LOW": "LOW : le modèle estime un risque d’insuffisance pour les conditions actuelles. Vérifiez l’humidité, le pH et les besoins en eau de la culture.",
        "MEDIUM": "MEDIUM : le modèle juge la situation moyenne. Surveillez le sol et ajustez l’irrigation si nécessaire.",
        "HIGH": "HIGH : le modèle détecte un fort besoin d’attention. Agissez rapidement pour éviter le stress hydrique ou un mauvais équilibre du sol.",
        "OPTIMAL": "OPTIMAL : les conditions sont bonnes selon le modèle. Maintenez vos pratiques actuelles.",
    }
    return mapping.get(str(state).upper(), f"{state} : explication non disponible.")


def run_diagnostic(features: dict):
    """
    Expose un diagnostic complet pour l'interface :
    - 'etat_ia' : sortie du modèle IA (ou message d'erreur si indisponible)
    - 'etat_ia_explanation' : explication lisible du résultat IA
    - 'irrigation_factors' : dict de facteurs que le futur modèle d'irrigation utilisera

    Le calcul des facteurs est une estimation heuristique basée sur les entrées
    fournies (type de sol, stade de croissance, météo, humidité...).
    """
    try:
        etat_ia = get_diagnostic_ia(features)
    except Exception as e:
        etat_ia = f"ERREUR_IA:{e}"

    etat_ia_explanation = explain_ia_state(etat_ia)

    soil_type = str(features.get("Soil_Type", "")).lower()
    soil_capacity_map = {
        "argileux": 0.35, "loameux": 0.25, "sableux": 0.10, "limon": 0.20,
        "clay": 0.35, "loamy": 0.25, "sandy": 0.10, "silt": 0.20
    }
    swc = soil_capacity_map.get(soil_type, 0.25)

    growth_stage = str(features.get("Crop_Growth_Stage", "")).lower()
    kc_map = {
        "sowing": 0.4, "vegetative": 0.7, "flowering": 1.0, "harvest": 0.6,
        "semis": 0.4, "végétatif": 0.7, "floraison": 1.0, "récolte": 0.6
    }
    kc = kc_map.get(growth_stage, 0.7)

    temp = float(features.get("Temperature_C", 25.0))
    sunlight = float(features.get("Sunlight_Hours", 8.0))
    rainfall = float(features.get("Rainfall_mm", 0.0))
    soil_moisture = float(features.get("Soil_Moisture", 0.0))
    previous_irrigation = float(features.get("Previous_Irrigation_mm", 0.0))
    field_area = float(features.get("Field_Area_hectare", 1.0))

    # Estimate de référence ET0 (heuristique simple, unité arbitraire proche du mm/jour)
    et0 = 0.6 * (temp / 25.0) * (sunlight / 8.0)

    # Besoin en eau de la culture (mm) - échelle heuristique
    crop_water_need_mm = kc * et0 * 5.0

    # Eau disponible dans la zone racinaire (mm) — racine effective ~0.3 m
    root_depth = 0.3
    available_water_mm = swc * 100.0 * root_depth

    soil_moisture_fraction = soil_moisture / 100.0
    water_already_mm = soil_moisture_fraction * available_water_mm

    recommended_mm = max(0.0, crop_water_need_mm - water_already_mm - rainfall - previous_irrigation)

    irrigation_factors = {
        "crop_coefficient": round(kc, 3),
        "soil_water_holding_capacity": round(swc, 3),
        "root_depth_m": round(root_depth, 2),
        "reference_et0": round(et0, 3),
        "crop_water_need_mm": round(crop_water_need_mm, 3),
        "available_water_mm": round(available_water_mm, 3),
        "water_already_mm": round(water_already_mm, 3),
        "recommended_irrigation_mm": round(recommended_mm, 3),
        "field_area_hectare": round(field_area, 3)
    }

    return {"etat_ia": etat_ia, "etat_ia_explanation": etat_ia_explanation, "irrigation_factors": irrigation_factors}