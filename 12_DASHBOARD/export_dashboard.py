"""
Projet 11 : exporter les tables du Data Warehouse pour le dashboard Power BI.
Exporte les 7 tables MART et dq_results en CSV dans 12_DASHBOARD/data.
Aucun worker_id n'est exporté : le script s'arrête si une colonne en contient un.
Pas de tables CORE (fact_*, dim_*) : le dashboard lit uniquement les MART.
Lancement depuis la racine du projet :  python 12_DASHBOARD/export_dashboard.py
(le pipeline 04_ETL/etl_pipeline.py doit avoir été lancé avant)
"""
import sqlite3
from pathlib import Path

import pandas as pd

DOSSIER_DASHBOARD = Path(__file__).resolve().parent
BASE = DOSSIER_DASHBOARD.parent / "04_ETL" / "project_11_dwh.db"
DOSSIER_SORTIE = DOSSIER_DASHBOARD / "data"

TABLES = [
    "mart_incidents_month",
    "mart_severity_distribution",
    "mart_incidents_by_area",
    "mart_near_miss",
    "mart_recurring_incident_type",
    "mart_incident_rate_shift_role",
    "mart_kpi_summary",
    "dq_results",
]

if not BASE.exists():
    raise SystemExit(f"Base introuvable : {BASE}. Lancer d'abord python 04_ETL/etl_pipeline.py")

DOSSIER_SORTIE.mkdir(exist_ok=True)

# Lecture seule : l'export ne peut pas modifier la base
con = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)

for table in TABLES:
    df = pd.read_sql_query(f"SELECT * FROM {table}", con)

    # Garde-fou : aucun identifiant de travailleur
    interdites = [c for c in df.columns if "worker" in c.lower()]
    if interdites:
        raise SystemExit(f"{table} contient {interdites} : export annulé")

    df.to_csv(DOSSIER_SORTIE / f"{table}.csv", index=False, encoding="utf-8")
    print(f"{table}.csv : {len(df)} lignes, {len(df.columns)} colonnes")

con.close()
print(f"\n{len(TABLES)} fichiers écrits dans {DOSSIER_SORTIE}")
