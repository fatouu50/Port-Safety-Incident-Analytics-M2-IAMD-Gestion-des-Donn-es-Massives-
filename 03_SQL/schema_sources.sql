-- =====================================================================
-- Projet 11 : Port Safety & Incident Analytics
-- Modèle relationnel source (SQLite)
-- 3 tables de référence : locations, workers_synthetic, equipment
-- 2 tables d'événements : incidents, safety_observations
-- =====================================================================

PRAGMA foreign_keys = ON;

-- On supprime d'abord les tables qui contiennent des clés étrangères,
-- sinon SQLite refuse de supprimer les tables de référence.
DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS safety_observations;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS workers_synthetic;
DROP TABLE IF EXISTS equipment;

-- ---------------------------------------------------------------------
-- Tables de référence
-- ---------------------------------------------------------------------

-- Zones du port (25 zones)
CREATE TABLE locations (
    location_id TEXT PRIMARY KEY,                                   -- LOC001
    area_type   TEXT NOT NULL
                CHECK (area_type IN ('BERTH', 'GATE', 'RAIL', 'WORKSHOP', 'YARD')),
    area_name   TEXT NOT NULL                                       -- AREA_01
);

-- Travailleurs synthétiques (aucune donnée personnelle réelle)
CREATE TABLE workers_synthetic (
    worker_id TEXT PRIMARY KEY,                                     -- W0001
    role      TEXT NOT NULL
              CHECK (role IN ('SUPERVISOR', 'OPERATOR', 'TECHNICIAN', 'DRIVER')),
    shift     TEXT NOT NULL
              CHECK (shift IN ('A', 'B', 'C'))
);

-- Engins de manutention
CREATE TABLE equipment (
    equipment_id   TEXT PRIMARY KEY,                                -- CHE01
    equipment_type TEXT NOT NULL
                   CHECK (equipment_type IN ('RMG', 'RTG', 'TT', 'FL', 'RS')),
    home_area      TEXT          -- code Yxx : ne correspond à aucune location_id
);

-- ---------------------------------------------------------------------
-- Tables d'événements
-- ---------------------------------------------------------------------

-- Incidents : 1 ligne = 1 incident
CREATE TABLE incidents (
    incident_id   TEXT PRIMARY KEY,                                 -- INC000001
    incident_ts   TEXT NOT NULL,                                    -- 'AAAA-MM-JJ HH:MM:SS'
    location_id   TEXT NOT NULL REFERENCES locations(location_id),
    equipment_id  TEXT NOT NULL REFERENCES equipment(equipment_id),
    severity      TEXT NOT NULL
                  CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    incident_type TEXT NOT NULL
                  CHECK (incident_type IN ('COLLISION', 'EQUIPMENT', 'FALL', 'NEAR_MISS', 'PPE', 'SPILL')),
    worker_id     TEXT NOT NULL REFERENCES workers_synthetic(worker_id)
);

-- Observations de sécurité : 1 ligne = 1 observation
CREATE TABLE safety_observations (
    observation_id   INTEGER PRIMARY KEY,
    observation_ts   TEXT NOT NULL,
    location_id      TEXT NOT NULL REFERENCES locations(location_id),
    observation_type TEXT NOT NULL
                     CHECK (observation_type IN ('SAFE', 'UNSAFE', 'NEAR_MISS')),
    reported_by_role TEXT NOT NULL
                     CHECK (reported_by_role IN ('OPERATOR', 'SUPERVISOR', 'HSE'))
);

-- ---------------------------------------------------------------------
-- Index sur les colonnes de jointure et de filtre (cours S2)
-- ---------------------------------------------------------------------
CREATE INDEX idx_inc_location ON incidents(location_id);
CREATE INDEX idx_inc_worker   ON incidents(worker_id);
CREATE INDEX idx_inc_ts       ON incidents(incident_ts);
CREATE INDEX idx_obs_location ON safety_observations(location_id);
CREATE INDEX idx_obs_ts       ON safety_observations(observation_ts);