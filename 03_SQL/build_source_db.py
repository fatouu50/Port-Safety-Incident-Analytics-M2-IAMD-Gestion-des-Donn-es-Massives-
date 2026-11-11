"""
Projet 11 : construction de la base source SQLite.

Lancement, depuis la racine du projet :
    python 03_SQL/build_source_db.py

Le script crée 03_SQL/project_11_sources.db à partir de schema_sources.sql
et des fichiers CSV de 01_DATA_RAW. On peut le relancer autant de fois
qu'on veut : la base est reconstruite à l'identique.
"""
import sqlite3
from pathlib import Path

import pandas as pd

# Chemins calculés à partir de l'emplacement du script :
# le script marche quel que soit le dossier d'où on le lance.
DOSSIER_SQL = Path(__file__).resolve().parent
DOSSIER_DONNEES = DOSSIER_SQL.parent / "01_DATA_RAW"
BASE = DOSSIER_SQL / "project_11_sources.db"

# 1. Repartir d'une base vide (reproductibilité)
if BASE.exists():
    BASE.unlink()

con = sqlite3.connect(BASE)
con.execute("PRAGMA foreign_keys = ON")

# 2. Créer les tables avec le schéma (PK, FK, CHECK, index)
schema = (DOSSIER_SQL / "schema_sources.sql").read_text(encoding="utf-8")
con.executescript(schema)
print("Schéma créé")

# 3. Charger les CSV
# Ordre important : les tables de référence d'abord,
# car les incidents et les observations pointent vers elles.
tables = ["locations", "workers_synthetic", "equipment", "incidents", "safety_observations"]

for table in tables:
    df = pd.read_csv(DOSSIER_DONNEES / (table + ".csv"))
    df.to_sql(table, con, index=False, if_exists="append")
    print(f"  {table:<22} {len(df):>5} lignes chargées")

con.commit()

# 4. Vérifier qu'aucune clé étrangère n'est cassée
erreurs = con.execute("PRAGMA foreign_key_check").fetchall()
if erreurs:
    print("Clés étrangères cassées :", len(erreurs))
else:
    print("Clés étrangères : OK, aucune erreur")

con.close()
print("Base créée :", BASE.name)