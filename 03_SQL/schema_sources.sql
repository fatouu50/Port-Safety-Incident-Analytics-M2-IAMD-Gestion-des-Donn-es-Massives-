-- SQLite starter schema generated for the student project
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS locations;
CREATE TABLE locations (
    location_id TEXT,
    area_type TEXT,
    area_name TEXT
);

DROP TABLE IF EXISTS workers_synthetic;
CREATE TABLE workers_synthetic (
    worker_id TEXT,
    role TEXT,
    shift TEXT
);

DROP TABLE IF EXISTS incidents;
CREATE TABLE incidents (
    incident_id TEXT,
    incident_ts TEXT,
    location_id TEXT,
    equipment_id TEXT,
    severity TEXT,
    incident_type TEXT,
    worker_id TEXT
);

DROP TABLE IF EXISTS safety_observations;
CREATE TABLE safety_observations (
    observation_id INTEGER,
    observation_ts TEXT,
    location_id TEXT,
    observation_type TEXT,
    reported_by_role TEXT
);

DROP TABLE IF EXISTS equipment;
CREATE TABLE equipment (
    equipment_id TEXT,
    equipment_type TEXT,
    home_area TEXT
);
