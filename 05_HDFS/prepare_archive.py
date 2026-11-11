"""
Projet 11 : préparation de l'archive à envoyer dans HDFS.
Lancement depuis le dossier 05_HDFS :  python prepare_archive.py
"""
from pathlib import Path
import shutil

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


# ---------------------------------------------------------------------
# Étape 2.3 : écrire les incidents, un fichier par mois
# ---------------------------------------------------------------------

# Repartir d'une archive vide : on peut relancer le script sans doublon
if ARCHIVE.exists():
    shutil.rmtree(ARCHIVE)

print()
print("Fichiers créés :")
for (annee, mois), partie in incidents.groupby(["annee", "mois"]):
    dossier = ARCHIVE / "raw" / "incidents" / f"year={annee}" / f"month={mois}"
    dossier.mkdir(parents=True, exist_ok=True)

    fichier = dossier / f"incidents_{annee}_{mois}.csv"
    partie.drop(columns=["annee", "mois"]).to_csv(fichier, index=False)

    print(f"  {fichier.relative_to(ARCHIVE)} : {len(partie)} lignes")


    
# ---------------------------------------------------------------------
# Étape 2.4 : écrire les observations, un fichier par mois
# ---------------------------------------------------------------------
observations = pd.read_csv(DOSSIER_01_DATA_RAW / "safety_observations.csv")

dates = pd.to_datetime(observations["observation_ts"])
observations["annee"] = dates.dt.strftime("%Y")
observations["mois"] = dates.dt.strftime("%m")

for (annee, mois), partie in observations.groupby(["annee", "mois"]):
    dossier = ARCHIVE / "raw" / "safety_observations" / f"year={annee}" / f"month={mois}"
    dossier.mkdir(parents=True, exist_ok=True)

    fichier = dossier / f"safety_observations_{annee}_{mois}.csv"
    partie.drop(columns=["annee", "mois"]).to_csv(fichier, index=False)

    print(f"  {fichier.relative_to(ARCHIVE)} : {len(partie)} lignes")


    
# ---------------------------------------------------------------------
# Étape 2.5 : copier les tables de référence telles quelles
# ---------------------------------------------------------------------
dossier_reference = ARCHIVE / "reference"
dossier_reference.mkdir(parents=True, exist_ok=True)

for table in ["locations", "workers_synthetic", "equipment"]:
    source = DOSSIER_01_DATA_RAW / (table + ".csv")
    fichier = dossier_reference / (table + ".csv")
    shutil.copyfile(source, fichier)

    nb_lignes = len(pd.read_csv(fichier))
    print(f"  {fichier.relative_to(ARCHIVE)} : {nb_lignes} lignes")