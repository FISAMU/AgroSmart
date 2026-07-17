import joblib
import os
import sys

MODEL_DIR = os.path.join("models", "diagnostic")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoder_diagnostic.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "model_diagnostic.pkl")
SCHEMA_PATH = os.path.join(MODEL_DIR, "irrigation_columns.pkl")

print('MODEL_DIR:', MODEL_DIR)
for p in [ENCODER_PATH, MODEL_PATH, SCHEMA_PATH]:
    print(p, 'exists:', os.path.exists(p))

try:
    schema = joblib.load(SCHEMA_PATH) if os.path.exists(SCHEMA_PATH) else {}
    categorical_cols = schema.get('categorical_cols', [])
    numeric_cols = schema.get('numeric_cols', [])
    print('categorical_cols:', categorical_cols)
    print('numeric_cols:', numeric_cols)
except Exception as e:
    print('Erreur lecture schema:', e)
    categorical_cols = []
    numeric_cols = []

# Construire un échantillon basé sur les colonnes attendues
sample = {}
for c in categorical_cols:
    if c.lower().startswith('soil'):
        sample[c] = 'Loamy'
    elif c.lower().startswith('crop'):
        sample[c] = 'Maize'
    elif c.lower().startswith('season'):
        sample[c] = 'Kharif'
    else:
        sample[c] = 'Unknown'
for c in numeric_cols:
    sample[c] = 1.0

print('Sample features prepared:', sample)

if not os.path.exists(ENCODER_PATH) or not os.path.exists(MODEL_PATH):
    print('Encoder ou modèle manquant — impossible de tester la prédiction.')
    sys.exit(0)

try:
    encoder = joblib.load(ENCODER_PATH)
    model = joblib.load(MODEL_PATH)
    print('Encoder et modèle chargés avec succès.')

    cat_vals = [sample[c] for c in categorical_cols]
    num_vals = [float(sample[c]) for c in numeric_cols]
    print('cat_vals:', cat_vals)
    print('num_vals:', num_vals)

    try:
        encoded = encoder.transform([cat_vals])[0].tolist()
        print('Encodage réussi. encoded length =', len(encoded))
    except Exception as e:
        print('Erreur encodage:', e)
        encoded = None

    if encoded is not None:
        row = encoded + num_vals
        try:
            pred = model.predict([row])
            print('Prediction OK:', pred)
        except Exception as e:
            print('Erreur prediction:', e)
except Exception as e:
    print('Erreur chargement encoder/model:', e)
