"""
Projet 11 : préparation de l'archive à envoyer dans HDFS.
Lancement depuis le dossier 05_HDFS :  python prepare_archive.py
"""
from pathlib import Path

import pandas as pd

# Où se trouve ce script : le dossier 05_HDFS
DOSSIER_05_HDFS = Path(__file__).resolve().parent

# Où se trouvent les données sources : le dossier 01_DATA_RAW, à côté de 05_HDFS
DOSSIER_01_DATA_RAW = DOSSIER_05_HDFS.parent / "01_DATA_RAW"

# Où on va construire l'archive : 05_HDFS/archive
ARCHIVE = DOSSIER_05_HDFS / "archive"

print("Script     :", DOSSIER_05_HDFS)
print("Sources    :", DOSSIER_01_DATA_RAW)
print("Archive    :", ARCHIVE)


# ---------------------------------------------------------------------
# Étape 2.2 : lire les incidents et extraire l'année et le mois
# ---------------------------------------------------------------------
incidents = pd.read_csv(DOSSIER_01_DATA_RAW / "incidents.csv")

dates = pd.to_datetime(incidents["incident_ts"])
incidents["annee"] = dates.dt.strftime("%Y")
incidents["mois"] = dates.dt.strftime("%m")

print()
print("Incidents lus :", len(incidents))
print(incidents[["incident_id", "incident_ts", "annee", "mois"]].head())
print()
print("Nombre d'incidents par mois :")
print(incidents.groupby(["annee", "mois"]).size())