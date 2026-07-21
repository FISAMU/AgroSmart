-- Schéma PostgreSQL AgroSmart (Neon)

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    sexe VARCHAR(20),
    tel VARCHAR(50),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS password_reset_codes (
    email VARCHAR(255) PRIMARY KEY,
    code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS cultures_ref (
    nom VARCHAR(100) PRIMARY KEY,
    ph_min DOUBLE PRECISION NOT NULL,
    ph_max DOUBLE PRECISION NOT NULL,
    hum_min DOUBLE PRECISION NOT NULL,
    besoin_eau_base DOUBLE PRECISION NOT NULL,
    hum_optimal DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS donnees_capteurs (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_donnees_capteurs_user_ts
    ON donnees_capteurs (user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS app_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
