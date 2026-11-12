"""
Projet 11 : export des tables MART du DWH en Parquet, pour l'archive HDFS.
À lancer depuis 05_HDFS, APRÈS 04_ETL/etl_pipeline.py et APRÈS prepare_archive.py :
    python export_mart_parquet.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

DOSSIER_05_HDFS = Path(__file__).resolve().parent
BASE_DWH = DOSSIER_05_HDFS.parent / "04_ETL" / "project_11_dwh.db"
DOSSIER_MART = DOSSIER_05_HDFS / "archive" / "curated" / "mart"
DOSSIER_MART.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(BASE_DWH)
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE name LIKE 'mart_%' ORDER BY name", con
)["name"]

total = 0
for table in tables:
    df = pd.read_sql_query(f"SELECT * FROM {table}", con)
    fichier = DOSSIER_MART / (table + ".parquet")
    df.to_parquet(fichier, index=False)

    # Relire le fichier écrit pour vérifier qu'il est complet
    relu = pd.read_parquet(fichier)
    statut = "OK" if len(relu) == len(df) else "ÉCART"
    total += len(df)
    print(f"  {table:<32} {len(df):>3} lignes -> {fichier.name} : {statut}")

con.close()
print(f"{len(tables)} tables MART exportées, {total} lignes au total")