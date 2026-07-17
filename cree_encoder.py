import firebase_admin
from firebase_admin import credentials, firestore
from sklearn.preprocessing import LabelEncoder
import joblib
import os

def creer_et_sauvegarder_encodeur():
    # 1. Initialisation Firebase
    if not firebase_admin._apps:
        # Assure-toi que le nom du fichier clé est correct
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()

    print("🔄 Récupération des noms de cultures depuis Firebase...")
    
    # 2. Récupérer les noms des documents dans la collection 'cultures_ref'
    cultures_docs = db.collection("cultures_ref").stream()
    liste_noms = [doc.id for doc in cultures_docs]
    
    if not liste_noms:
        print("❌ Erreur : Aucune culture trouvée dans Firebase. Vérifie ta collection 'cultures_ref'.")
        return

    print(f"✅ {len(liste_noms)} cultures trouvées. Entraînement de l'encodeur...")

    # 3. Créer et entraîner l'encodeur
    le = LabelEncoder()
    le.fit(liste_noms)

    # 4. Créer le dossier models s'il n'existe pas
    if not os.path.exists('models'):
        os.makedirs('models')

    # 5. Sauvegarder l'encodeur
    joblib.dump(le, 'models/culture_encoder.pkl')
    
    print(f"🎉 Succès ! L'encodeur est sauvegardé dans 'models/culture_encoder.pkl'.")
    print(f"Il gère maintenant {len(le.classes_)} cultures.")

if __name__ == "__main__":
    creer_et_sauvegarder_encodeur()