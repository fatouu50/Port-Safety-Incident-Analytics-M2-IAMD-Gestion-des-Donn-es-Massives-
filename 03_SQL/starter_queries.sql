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


-- ---------------------------------------------------------------------
-- TODO 2 : au moins 3 jointures
-- ---------------------------------------------------------------------

-- Q02 : JOIN 1, incidents enrichis avec la zone, l'engin et le travailleur
SELECT i.incident_id, i.incident_ts, l.area_type, e.equipment_type,
       w.role, w.shift, i.incident_type, i.severity
FROM incidents i
JOIN locations l         ON l.location_id  = i.location_id
JOIN equipment e         ON e.equipment_id = i.equipment_id
JOIN workers_synthetic w ON w.worker_id    = i.worker_id
ORDER BY i.incident_ts
LIMIT 10;

-- Q02 bis : contrôle, la jointure ne doit pas multiplier les lignes
SELECT (SELECT COUNT(*) FROM incidents) AS avant_jointure,
       (SELECT COUNT(*)
        FROM incidents i
        JOIN locations l         ON l.location_id  = i.location_id
        JOIN equipment e         ON e.equipment_id = i.equipment_id
        JOIN workers_synthetic w ON w.worker_id    = i.worker_id) AS apres_jointure;

-- Q03 : JOIN 2, incidents et part d'incidents graves par type de zone
SELECT l.area_type,
       COUNT(*) AS nb_incidents,
       SUM(CASE WHEN i.severity IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) AS nb_graves,
       ROUND(100.0 * SUM(CASE WHEN i.severity IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_graves
FROM incidents i
JOIN locations l ON l.location_id = i.location_id
GROUP BY l.area_type
ORDER BY nb_incidents DESC;

-- Q04 : JOIN 3 (LEFT JOIN + IS NULL), recherche des clés orphelines
SELECT 'incidents.location_id' AS cle, COUNT(*) AS nb_orphelins
FROM incidents i LEFT JOIN locations l ON l.location_id = i.location_id
WHERE l.location_id IS NULL
UNION ALL
SELECT 'incidents.equipment_id', COUNT(*)
FROM incidents i LEFT JOIN equipment e ON e.equipment_id = i.equipment_id
WHERE e.equipment_id IS NULL
UNION ALL
SELECT 'incidents.worker_id', COUNT(*)
FROM incidents i LEFT JOIN workers_synthetic w ON w.worker_id = i.worker_id
WHERE w.worker_id IS NULL
UNION ALL
SELECT 'safety_observations.location_id', COUNT(*)
FROM safety_observations o LEFT JOIN locations l ON l.location_id = o.location_id
WHERE l.location_id IS NULL;