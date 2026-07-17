import os
os.environ.setdefault("GOOGLE_CLOUD_DISABLE_GRPC", "true")
os.environ.setdefault("GRPC_DNS_RESOLVER", "ares")

import firebase_admin
from firebase_admin import credentials, firestore
import random
import time
from datetime import datetime

# 1. Configuration

def init_firestore_client():
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        client = firestore.client()
        print("✅ Simulateur prêt et connecté.")
        return client
    except Exception as e:
        print(f"❌ Erreur de connexion Firestore : {e}")
        return None

# variable globale de connexion Firestore
db = init_firestore_client()

def executer_simulation():
    print("🚀 Attente d'un utilisateur sur le Dashboard...")
    
    try:
        while True:
            global db
            if db is None:
                db = init_firestore_client()
                if db is None:
                    print("⏳ Nouvelle tentative de connexion dans 10 secondes...")
                    time.sleep(10)
                    continue

            try:
                # Récupération automatique de l'utilisateur qui navigue sur le site
                config_doc = db.collection("config").document("simulator").get()
                
                if config_doc.exists:
                    user_id = config_doc.to_dict().get("active_user_id")
                    
                    if user_id:
                        soil_ph = round(random.uniform(5.5, 7.8), 2)
                        humidity = round(random.uniform(20.0, 65.0), 2)
                        temperature = round(random.uniform(24.0, 32.0), 2)
                        soil_type_model = random.choice(["DRY", "HUMID", "WET"])
                        region_model = random.choice(["DESERT", "HUMID", "SEMI ARID", "SEMI HUMID"])
                        weather_condition = random.choice(["NORMAL", "RAINY", "SUNNY", "WINDY"])
                        temp_avg = round(temperature + random.uniform(-1.5, 1.5), 2)

                        donnees = {
                            "timestamp": datetime.now(),
                            "ph": soil_ph,
                            "Soil_pH": soil_ph,
                            "humidite": humidity,
                            "Humidity": humidity,
                            "temperature": temperature,
                            "Temperature_C": temperature,
                            "TEMP_AVG": temp_avg,
                            "unite": "Celsius",
                            "Soil_Type": random.choice(["Clay", "Loamy", "Sandy", "Silt"]),
                            "SOIL TYPE": soil_type_model,
                            "Crop_Type": random.choice(["Cotton", "Maize", "Potato", "Rice", "Sugarcane", "Wheat"]),
                            "Crop_Growth_Stage": random.choice(["Sowing", "Vegetative", "Flowering", "Harvest"]),
                            "Season": random.choice(["Kharif", "Rabi", "Zaid"]),
                            "Irrigation_Type": random.choice(["Canal", "Drip", "Rainfed", "Sprinkler"]),
                            "Water_Source": random.choice(["Groundwater", "Rainwater", "Reservoir", "River"]),
                            "Mulching_Used": random.choice(["No", "Yes"]),
                            "Region": random.choice(["Central", "East", "North", "South", "West"]),
                            "REGION": region_model,
                            "WEATHER CONDITION": weather_condition,
                            "Soil_Moisture": round(random.uniform(15.0, 70.0), 2),
                            "Organic_Carbon": round(random.uniform(0.5, 3.5), 2),
                            "Electrical_Conductivity": round(random.uniform(0.2, 2.5), 2),
                            "Rainfall_mm": round(random.uniform(0.0, 25.0), 2),
                            "Sunlight_Hours": round(random.uniform(4.0, 12.0), 2),
                            "Wind_Speed_kmh": round(random.uniform(0.5, 15.0), 2),
                            "Field_Area_hectare": round(random.uniform(0.25, 5.0), 2),
                            "Previous_Irrigation_mm": round(random.uniform(0.0, 20.0), 2),
                        }

                        # Envoi au bon utilisateur
                        db.collection("users").document(user_id).collection("donnees_capteurs").add(donnees)
                        
                        print(f"📡 [OK] Données envoyées vers {user_id[:8]}... | Temp: {donnees['temperature']}°C")
                    else:
                        print("⏳ Aucun utilisateur n'est actuellement sur le Dashboard.")
                else:
                    print("⏳ En attente de signal du Dashboard (connectez-vous)...")
            except Exception as e:
                print(f"❌ Erreur Firestore pendant la simulation : {e}")
                db = None

            time.sleep(10)

    except KeyboardInterrupt:
        print("\n⏹️ Simulation stoppée.")

if __name__ == "__main__":
    executer_simulation()