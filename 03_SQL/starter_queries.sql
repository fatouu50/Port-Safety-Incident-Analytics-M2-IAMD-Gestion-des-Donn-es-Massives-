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


-- ---------------------------------------------------------------------
-- TODO 3 : au moins 2 requêtes GROUP BY qui calculent des KPI
-- ---------------------------------------------------------------------

-- Q05 : KPI1, incidents par mois (dont graves et near-miss)
SELECT strftime('%Y-%m', incident_ts) AS mois,
       COUNT(*) AS nb_incidents,
       SUM(CASE WHEN severity IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) AS nb_graves,
       SUM(CASE WHEN incident_type = 'NEAR_MISS' THEN 1 ELSE 0 END) AS nb_near_miss
FROM incidents
GROUP BY mois
ORDER BY mois;

-- Q05 bis : KPI1, moyenne mensuelle sur les mois complets (octobre exclu, il s'arrête au 28)
SELECT ROUND(AVG(nb_incidents), 1) AS moyenne_incidents_par_mois
FROM (SELECT strftime('%Y-%m', incident_ts) AS mois, COUNT(*) AS nb_incidents
      FROM incidents
      GROUP BY mois)
WHERE mois < '2026-10';

-- Q06 : KPI2, répartition des incidents par gravité
SELECT severity,
       COUNT(*) AS nb_incidents,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM incidents), 1) AS pct
FROM incidents
GROUP BY severity
ORDER BY CASE severity WHEN 'LOW' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'HIGH' THEN 3 ELSE 4 END;

-- Q07 : KPI4, near-miss dans les deux sources
SELECT 'incidents' AS source, COUNT(*) AS nb_near_miss
FROM incidents WHERE incident_type = 'NEAR_MISS'
UNION ALL
SELECT 'safety_observations', COUNT(*)
FROM safety_observations WHERE observation_type = 'NEAR_MISS';

-- Q08 : KPI6, taux d'incidents par rôle et par équipe
-- (incidents du groupe / nombre de travailleurs du groupe)
SELECT w.role, w.shift,
       COUNT(DISTINCT w.worker_id) AS nb_travailleurs,
       COUNT(i.incident_id)        AS nb_incidents,
       ROUND(1.0 * COUNT(i.incident_id) / COUNT(DISTINCT w.worker_id), 2) AS incidents_par_travailleur
FROM workers_synthetic w
LEFT JOIN incidents i ON i.worker_id = w.worker_id
GROUP BY w.role, w.shift
ORDER BY incidents_par_travailleur DESC;


-- ---------------------------------------------------------------------
-- TODO 4 : sous-requête et CTE
-- ---------------------------------------------------------------------

-- Q09 : SOUS-REQUÊTE, zones qui dépassent la moyenne d'incidents par zone
SELECT l.location_id, l.area_type, COUNT(*) AS nb_incidents
FROM incidents i
JOIN locations l ON l.location_id = i.location_id
GROUP BY l.location_id, l.area_type
HAVING COUNT(*) > (SELECT AVG(n)
                   FROM (SELECT COUNT(*) AS n FROM incidents GROUP BY location_id))
ORDER BY nb_incidents DESC;

-- Q10 : CTE + RANK, type d'incident le plus récurrent dans chaque type de zone
WITH par_zone_type AS (
    SELECT l.area_type, i.incident_type, COUNT(*) AS nb
    FROM incidents i
    JOIN locations l ON l.location_id = i.location_id
    GROUP BY l.area_type, i.incident_type
),
classement AS (
    SELECT area_type, incident_type, nb,
           RANK() OVER (PARTITION BY area_type ORDER BY nb DESC) AS rang,
           ROUND(100.0 * nb / SUM(nb) OVER (PARTITION BY area_type), 1) AS pct_dans_la_zone
    FROM par_zone_type
)
SELECT area_type, incident_type AS type_le_plus_recurrent, nb, pct_dans_la_zone
FROM classement
WHERE rang = 1
ORDER BY nb DESC;

-- Q11 : CTE + LAG, variation du nombre d'incidents d'un mois à l'autre
WITH mensuel AS (
    SELECT strftime('%Y-%m', incident_ts) AS mois, COUNT(*) AS nb
    FROM incidents
    GROUP BY mois
)
SELECT mois, nb,
       LAG(nb) OVER (ORDER BY mois) AS nb_mois_precedent,
       ROUND(100.0 * (nb - LAG(nb) OVER (ORDER BY mois)) / LAG(nb) OVER (ORDER BY mois), 1) AS variation_pct
FROM mensuel
ORDER BY mois;

-- Q12 : CTE, observations UNSAFE face aux incidents graves, par zone
WITH obs AS (
    SELECT location_id,
           COUNT(*) AS nb_observations,
           SUM(CASE WHEN observation_type = 'UNSAFE' THEN 1 ELSE 0 END) AS nb_unsafe
    FROM safety_observations
    GROUP BY location_id
),
inc AS (
    SELECT location_id,
           COUNT(*) AS nb_incidents,
           SUM(CASE WHEN severity IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) AS nb_graves
    FROM incidents
    GROUP BY location_id
)
SELECT l.location_id, l.area_type, o.nb_observations, o.nb_unsafe,
       ROUND(100.0 * o.nb_unsafe / o.nb_observations, 1) AS pct_unsafe,
       i.nb_incidents, i.nb_graves
FROM locations l
JOIN obs o ON o.location_id = l.location_id
JOIN inc i ON i.location_id = l.location_id
ORDER BY i.nb_graves DESC, pct_unsafe DESC;


-- ---------------------------------------------------------------------
-- TODO 5 : grain du Data Warehouse et unicité des sources
-- Grain choisi : 1 ligne de fact_incident = 1 incident (incident_id)
--                1 ligne de fact_safety_observation = 1 observation (observation_id)
-- ---------------------------------------------------------------------

-- Q13 : l'identifiant est-il unique ? (nb_lignes doit être égal à nb_cles)
SELECT 'incidents' AS table_name,
       COUNT(*) AS nb_lignes,
       COUNT(DISTINCT incident_id) AS nb_cles,
       COUNT(*) - COUNT(DISTINCT incident_id) AS doublons
FROM incidents
UNION ALL
SELECT 'safety_observations',
       COUNT(*),
       COUNT(DISTINCT observation_id),
       COUNT(*) - COUNT(DISTINCT observation_id)
FROM safety_observations;

-- Q14 : doublons métier, même événement saisi deux fois sous deux identifiants
SELECT incident_ts, location_id, worker_id, incident_type, COUNT(*) AS nb
FROM incidents
GROUP BY incident_ts, location_id, worker_id, incident_type
HAVING COUNT(*) > 1;

-- Q15 : plan d'exécution, colonne indexée (location_id) : SQLite utilise l'index
EXPLAIN QUERY PLAN
SELECT COUNT(*) FROM incidents WHERE location_id = 'LOC015';

-- Q15 bis : plan d'exécution, colonne sans index (equipment_id) : SQLite lit toute la table
EXPLAIN QUERY PLAN
SELECT COUNT(*) FROM incidents WHERE equipment_id = 'CHE15';