"""
Projet 11 : vérifier que HDFS contient exactement l'archive.
Pour chaque fichier du manifeste : relire depuis HDFS, recompter les lignes,
recalculer l'empreinte MD5, et comparer.
Lancement depuis 05_HDFS (cluster démarré, archive chargée) :  python hdfs_verify.py
"""
import hashlib
import subprocess
from io import BytesIO
from pathlib import Path

import pandas as pd

DOSSIER_05_HDFS = Path(__file__).resolve().parent
HDFS_ARCHIVE = "/port_exam/project_11/archive"

manifeste = pd.read_csv(DOSSIER_05_HDFS / "archive" / "_manifest" / "manifest.csv")

nb_ok = 0
for _, ligne in manifeste.iterrows():
    chemin_hdfs = HDFS_ARCHIVE + "/" + ligne["fichier"]

    # Relire le fichier depuis HDFS (dans le conteneur namenode)
    resultat = subprocess.run(
        ["docker", "exec", "namenode", "hdfs", "dfs", "-cat", chemin_hdfs],
        capture_output=True, check=True,
    )
    contenu = resultat.stdout

    # Recompter et recalculer, puis comparer au manifeste
    md5 = hashlib.md5(contenu).hexdigest()
    nb_lignes = len(pd.read_csv(BytesIO(contenu)))
    identique = (md5 == ligne["md5"]) and (nb_lignes == ligne["nb_lignes"])

    if identique:
        nb_ok += 1
    print(f"  {'OK   ' if identique else 'ÉCART'} {ligne['fichier']} ({nb_lignes} lignes)")

print()
print(f"{nb_ok} fichiers sur {len(manifeste)} identiques dans HDFS")