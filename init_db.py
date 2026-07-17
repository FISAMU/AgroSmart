import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import os

# 1. Initialisation de Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def charger_cultures_en_batch(fichier_csv):
    """
    Lit le CSV et envoie les données dans Firestore par lots de 500 (max autorisé par batch).
    """
    if not os.path.exists(fichier_csv):
        print(f"Erreur : Le fichier {fichier_csv} est introuvable.")
        return

    df = pd.read_csv(fichier_csv)
    
    # On utilise un batch pour être efficace
    batch = db.batch()
    compteur = 0
    total_batchs = 1

    print(f"Début de l'envoi de {len(df)} cultures...")

    for index, row in df.iterrows():
        # Création de la référence du document (utilisation du nom comme ID)
        doc_ref = db.collection("cultures_ref").document(str(row['nom']))
        
        # Données à envoyer
        data = {
            "ph_min": float(row['ph_min']),
            "ph_max": float(row['ph_max']),
            "hum_min": float(row['hum_min']),
            "besoin_eau_base": float(row['besoin_eau_base'])
        }
        
        batch.set(doc_ref, data)
        compteur += 1
        
        # Firestore limite les batchs à 500 opérations
        if compteur == 499:
            batch.commit()
            print(f"Batch {total_batchs} envoyé.")
            batch = db.batch()
            total_batchs += 1
            compteur = 0

    # Envoyer le dernier lot
    batch.commit()
    print("✅ Succès : Toutes les cultures ont été synchronisées avec Firebase.")

if __name__ == "__main__":
    charger_cultures_en_batch("cultures.csv")