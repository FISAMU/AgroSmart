# logic/irrigation.py
import joblib
import os
from firebase_admin import firestore

MODEL_DIR = os.path.join("models", "irrigation")
MODEL_PATH = os.path.join(MODEL_DIR, "model_irrigation.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoder_irrigation.pkl")

MODEL_CROP_TYPES = [
    "BANANA", "BEAN", "CABBAGE", "CITRUS", "COTTON", "MAIZE", "MELON",
    "MUSTARD", "ONION", "POTATO", "RICE", "SOYABEAN", "SUGARCANE",
    "TOMATO", "WHEAT"
]
SOIL_TYPE_OPTIONS = ["DRY", "HUMID", "WET"]
REGION_OPTIONS = ["DESERT", "HUMID", "SEMI ARID", "SEMI HUMID"]
WEATHER_OPTIONS = ["NORMAL", "RAINY", "SUNNY", "WINDY"]


def predire_quantite_eau_expert(nom_culture, etat_diagnostic):
    """
    Calcul classique basé sur les règles Firestore.
    """
    try:
        db = firestore.client()
        doc = db.collection("cultures_ref").document(nom_culture).get()
    except Exception:
        return 0.0

    if not doc.exists:
        return 0.0

    ref = doc.to_dict()
    besoin_base = ref.get("besoin_eau_base", 10.0)

    if etat_diagnostic == "DEFICIT_HYDRIQUE":
        return round(besoin_base * 1.5, 2)
    return round(besoin_base, 2)


def _normalize_crop_type(nom_culture):
    if not nom_culture:
        return "MAIZE"
    culture = str(nom_culture).strip().upper()
    alias = {
        "CORN": "MAIZE",
        "MAÏS": "MAIZE",
        "SUGAR CANE": "SUGARCANE",
        "SOYA": "SOYABEAN",
        "SOYA BEAN": "SOYABEAN",
    }
    return alias.get(culture, culture if culture in MODEL_CROP_TYPES else "MAIZE")


def predire_quantite_eau_ia(crop_type, soil_type, region, temp_avg, weather_condition):
    """
    Utilise le modèle d'irrigation entraîné dans models/irrigation.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        return predire_quantite_eau_expert(crop_type, "DEFICIT_HYDRIQUE")

    try:
        encoder = joblib.load(ENCODER_PATH)
        model = joblib.load(MODEL_PATH)
    except Exception:
        return predire_quantite_eau_expert(crop_type, "DEFICIT_HYDRIQUE")

    crop_type_norm = _normalize_crop_type(crop_type)
    soil_type_norm = str(soil_type).strip().upper() if soil_type else "HUMID"
    region_norm = str(region).strip().upper() if region else "HUMID"
    weather_norm = str(weather_condition).strip().upper() if weather_condition else "NORMAL"

    if soil_type_norm not in SOIL_TYPE_OPTIONS:
        soil_type_norm = "HUMID"
    if region_norm not in REGION_OPTIONS:
        region_norm = "HUMID"
    if weather_norm not in WEATHER_OPTIONS:
        weather_norm = "NORMAL"

    try:
        encoded_crop = encoder["CROP TYPE"].transform([crop_type_norm])[0]
        encoded_soil = encoder["SOIL TYPE"].transform([soil_type_norm])[0]
        encoded_region = encoder["REGION"].transform([region_norm])[0]
        encoded_weather = encoder["WEATHER CONDITION"].transform([weather_norm])[0]

        features = [[encoded_crop, encoded_soil, encoded_region, float(temp_avg), encoded_weather]]
        quantite = model.predict(features)
        return round(float(quantite[0]), 2)
    except Exception:
        return predire_quantite_eau_expert(crop_type, "DEFICIT_HYDRIQUE")
