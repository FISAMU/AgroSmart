import os

from db.neon import ensure_schema, list_culture_names
from sklearn.preprocessing import LabelEncoder
import joblib


def creer_et_sauvegarder_encodeur():
    ensure_schema()
    print("Récupération des noms de cultures depuis Neon...")

    liste_noms = list_culture_names()
    if not liste_noms:
        print("Erreur : Aucune culture trouvée. Lancez d'abord: python init_db.py")
        return

    print(f"{len(liste_noms)} cultures trouvées. Entraînement de l'encodeur...")

    le = LabelEncoder()
    le.fit(liste_noms)

    if not os.path.exists("models"):
        os.makedirs("models")

    joblib.dump(le, "models/culture_encoder.pkl")
    print("Succès ! L'encodeur est sauvegardé dans 'models/culture_encoder.pkl'.")
    print(f"Il gère maintenant {len(le.classes_)} cultures.")


if __name__ == "__main__":
    creer_et_sauvegarder_encodeur()
