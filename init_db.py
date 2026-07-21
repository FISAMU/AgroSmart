import os

import pandas as pd

from db.neon import bulk_upsert_cultures, ensure_schema


def charger_cultures_en_batch(fichier_csv: str) -> None:
    if not os.path.exists(fichier_csv):
        print(f"Erreur : Le fichier {fichier_csv} est introuvable.")
        return

    ensure_schema()
    df = pd.read_csv(fichier_csv)

    rows = [
        (
            str(row["nom"]),
            float(row["ph_min"]),
            float(row["ph_max"]),
            float(row["hum_min"]),
            float(row["besoin_eau_base"]),
        )
        for _, row in df.iterrows()
    ]

    print(f"Début de l'envoi de {len(rows)} cultures vers Neon...")
    bulk_upsert_cultures(rows)
    print("Succès : Toutes les cultures ont été synchronisées avec Neon PostgreSQL.")


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    charger_cultures_en_batch(os.path.join(base_dir, "cultures.csv"))
