-- =====================================================================
-- Projet 11 : Port Safety & Incident Analytics
-- Requêtes SQL sur la base source project_11_sources.db
-- (créée par build_source_db.py)
-- =====================================================================

-- Liste des tables de la base
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;

-- ---------------------------------------------------------------------
-- TODO 1 : volume de chaque table source
-- ---------------------------------------------------------------------

-- Q01 : nombre de lignes de chaque table
SELECT 'locations' AS table_name, COUNT(*) AS nb_lignes FROM locations
UNION ALL SELECT 'workers_synthetic', COUNT(*) FROM workers_synthetic
UNION ALL SELECT 'equipment', COUNT(*) FROM equipment
UNION ALL SELECT 'incidents', COUNT(*) FROM incidents
UNION ALL SELECT 'safety_observations', COUNT(*) FROM safety_observations;

-- Q01 bis : période couverte par les événements
SELECT 'incidents' AS table_name, MIN(incident_ts) AS debut, MAX(incident_ts) AS fin FROM incidents
UNION ALL
SELECT 'safety_observations', MIN(observation_ts), MAX(observation_ts) FROM safety_observations;