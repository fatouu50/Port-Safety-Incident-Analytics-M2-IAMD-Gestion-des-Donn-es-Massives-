"""
Projet 11 : tests du pipeline ETL.

Lancement, depuis la racine du projet :
    python 04_ETL/test_etl.py

Chaque test travaille dans un dossier temporaire (copie du pipeline et des
données) : 01_DATA_RAW et la vraie base ne sont jamais touchés.

  Test 1 : idempotence, deux runs donnent exactement la même base
  Test 2 : anomalies, 11 anomalies injectées donnent 11 rejets tracés
  Test 3 : panne, rollback, l'ancienne base reste intacte
"""
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

DOSSIER_ETL = Path(__file__).resolve().parent
DOSSIER_DONNEES = DOSSIER_ETL.parent / "01_DATA_RAW"
PIPELINE = DOSSIER_ETL / "etl_pipeline.py"

nb_erreurs = 0


def verifier(libelle, ok, detail=""):
    """Affiche OK / ERREUR et compte les erreurs."""
    global nb_erreurs
    if not ok:
        nb_erreurs += 1
    print(f"  {libelle:<58} {detail:<24} : {'OK' if ok else 'ERREUR'}")


def preparer(dossier):
    """Recrée dans `dossier` la même arborescence que le projet (04_ETL + 01_DATA_RAW).
    Le pipeline calcule ses chemins depuis son emplacement : il marche donc tel quel."""
    (dossier / "04_ETL").mkdir()
    shutil.copytree(DOSSIER_DONNEES, dossier / "01_DATA_RAW")
    shutil.copyfile(PIPELINE, dossier / "04_ETL" / "etl_pipeline.py")
    return dossier / "04_ETL" / "etl_pipeline.py", dossier / "04_ETL" / "project_11_dwh.db", dossier / "01_DATA_RAW"


def lancer(script):
    """Lance le pipeline dans un sous-processus et renvoie le résultat."""
    return subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def empreinte(base):
    """Empreinte SHA-256 du contenu de la base.
    On exclut ce qui change à chaque run par construction : la colonne _run_id,
    le journal des runs et dq_results (qui contient l'âge des données)."""
    con = sqlite3.connect(base)
    h = hashlib.sha256()
    tables = [t[0] for t in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
              if not t[0].startswith("sqlite_") and t[0] not in ("etl_run_log", "dq_results")]
    for table in tables:
        colonnes = ", ".join(c[1] for c in con.execute(f"PRAGMA table_info({table})") if c[1] != "_run_id")
        h.update(table.encode())
        for ligne in con.execute(f"SELECT {colonnes} FROM {table} ORDER BY {colonnes}"):
            h.update(repr(ligne).encode())
    con.close()
    return h.hexdigest()


# ---------------------------------------------------------------------
# Test 1 : idempotence
# ---------------------------------------------------------------------
print("Test 1 : idempotence (2 runs = même base)")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    script, base, donnees = preparer(Path(tmp))
    r1 = lancer(script)
    e1 = empreinte(base)
    r2 = lancer(script)
    e2 = empreinte(base)

    verifier("Run 1 terminé sans erreur", r1.returncode == 0)
    verifier("Run 2 terminé sans erreur", r2.returncode == 0)
    verifier("Même empreinte après le run 1 et le run 2", e1 == e2, e1[:12] + " = " + e2[:12])

    con = sqlite3.connect(base)
    nb_runs = con.execute("SELECT COUNT(*) FROM etl_run_log").fetchone()[0]
    detail_dq12 = con.execute("SELECT detail FROM dq_results WHERE regle = 'DQ12'").fetchone()[0]
    con.close()
    verifier("Journal : 2 runs enregistrés", nb_runs == 2, f"{nb_runs} run(s)")
    verifier("DQ12 : sources identiques au run précédent", "identiques" in detail_dq12)


# ---------------------------------------------------------------------
# Test 2 : anomalies, 11 rejets tracés
# ---------------------------------------------------------------------
print()
print("Test 2 : anomalies (11 anomalies injectées = 11 rejets)")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    script, base, donnees = preparer(Path(tmp))

    # Anomalies dans les incidents (9 lignes à rejeter)
    inc = pd.read_csv(donnees / "incidents.csv", dtype=str)
    inc.loc[0, "worker_id"] = ""                        # DQ02 : valeur obligatoire absente
    inc.loc[1, "incident_id"] = "XYZ1"                  # DQ04 : format d'identifiant
    inc.loc[2, "incident_ts"] = "2026-13-45 99:00:00"   # DQ05 : date invalide
    inc.loc[3, "incident_ts"] = "2019-05-01 10:00:00"   # DQ05 : avant 2020
    inc.loc[4, "incident_ts"] = "2027-01-01 10:00:00"   # DQ05 : dans le futur
    inc.loc[5, "severity"] = "URGENT"                   # DQ06 : valeur non autorisée
    inc.loc[6, "location_id"] = "LOC999"                # DQ07 : zone inconnue
    inc.loc[7, "equipment_id"] = "CHE99"                # DQ07 : engin inconnu
    inc.loc[10, "incident_type"] = "  spill "           # PAS un rejet : espaces et minuscules, corrigé
    identifiant_corrige = inc.loc[10, "incident_id"]
    inc = pd.concat([inc, inc.iloc[[20]]], ignore_index=True)   # DQ03 : doublon de clé
    inc.to_csv(donnees / "incidents.csv", index=False)

    # Anomalies dans les observations (2 lignes à rejeter)
    obs = pd.read_csv(donnees / "safety_observations.csv", dtype=str)
    obs.loc[0, "observation_type"] = "MAYBE"            # DQ06 : valeur non autorisée
    obs.loc[1, "location_id"] = "LOC888"               # DQ07 : zone inconnue
    obs.to_csv(donnees / "safety_observations.csv", index=False)

    r = lancer(script)
    verifier("Pipeline terminé sans erreur malgré les anomalies", r.returncode == 0)

    con = sqlite3.connect(base)
    rejets = pd.read_sql("SELECT table_name, row_num, rule, reason FROM stg_rejects "
                         "ORDER BY table_name, row_num", con)
    verifier("stg_rejects contient 11 lignes", len(rejets) == 11, f"{len(rejets)} rejets")
    attendu = {"DQ02": 1, "DQ03": 1, "DQ04": 1, "DQ05": 3, "DQ06": 2, "DQ07": 3}
    obtenu = rejets["rule"].value_counts().to_dict()
    verifier("Rejets par règle : DQ02=1 DQ03=1 DQ04=1 DQ05=3 DQ06=2 DQ07=3", obtenu == attendu, str(obtenu))
    verifier("Chaque rejet a une raison", (rejets["reason"].str.len() > 0).all())

    nb_inc = con.execute("SELECT COUNT(*) FROM fact_incident").fetchone()[0]
    nb_obs = con.execute("SELECT COUNT(*) FROM fact_safety_observation").fetchone()[0]
    verifier("Incidents : RAW 1401 = rejets 9 + faits 1392", nb_inc == 1392, f"faits = {nb_inc}")
    verifier("Observations : RAW 3500 = rejets 2 + faits 3498", nb_obs == 3498, f"faits = {nb_obs}")

    statuts_dq08 = [s[0] for s in con.execute("SELECT statut FROM dq_results WHERE regle = 'DQ08'")]
    verifier("DQ08 réconciliation OK pour les 5 tables", statuts_dq08 == ["OK"] * 5)

    type_corrige = con.execute("SELECT incident_type FROM stg_incidents WHERE incident_id = ?",
                               (identifiant_corrige,)).fetchone()
    verifier("'  spill ' corrigé en SPILL (pas rejeté)", type_corrige is not None and type_corrige[0] == "SPILL")
    con.close()

    print()
    print("  Les 11 rejets tracés :")
    print(rejets.to_string(index=False))


# ---------------------------------------------------------------------
# Test 3 : panne en cours de route, rollback
# ---------------------------------------------------------------------
print()
print("Test 3 : panne simulée (rollback)")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    script, base, donnees = preparer(Path(tmp))

    # Un premier run réussi : c'est la "bonne" base à protéger
    verifier("Run initial réussi", lancer(script).returncode == 0)
    empreinte_avant = empreinte(base)

    # On injecte une panne au début de l'étape 5.7 (après CORE et MART)
    code = script.read_text(encoding="utf-8")
    marqueur = "# Étape 5.7 : monitoring"
    verifier("Marqueur de panne trouvé dans le pipeline", marqueur in code)
    script.write_text(code.replace(marqueur, "raise RuntimeError('panne simulée')\n" + marqueur),
                      encoding="utf-8")

    r = lancer(script)
    verifier("Le run en panne se termine en erreur", r.returncode != 0)
    verifier("L'erreur est bien celle simulée", "panne simulée" in r.stderr)
    verifier("Base précédente intacte (même empreinte)", empreinte(base) == empreinte_avant)
    verifier("Base temporaire supprimée", not (base.parent / "project_11_dwh.tmp.db").exists())

    con = sqlite3.connect(base)
    journal = pd.read_sql("SELECT run_id, statut, message FROM etl_run_log", con)
    con.close()
    verifier("Journal : SUCCES puis ECHEC", list(journal["statut"]) == ["SUCCES", "ECHEC"],
             str(list(journal["statut"])))
    print()
    print("  Journal après la panne :")
    print(journal.to_string(index=False))

print()
if nb_erreurs == 0:
    print("Tous les tests sont passés.")
else:
    print(f"{nb_erreurs} test(s) en erreur.")
    sys.exit(1)
