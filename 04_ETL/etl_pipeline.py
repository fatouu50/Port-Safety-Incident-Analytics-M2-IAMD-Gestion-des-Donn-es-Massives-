"""
Projet 11 : pipeline ETL  Sources -> RAW -> STAGING -> CORE -> MART.

Lancement, depuis la racine du projet :
    python 04_ETL/etl_pipeline.py

Le script crée 04_ETL/project_11_dwh.db. On peut le relancer autant de fois
qu'on veut : la base est reconstruite à l'identique (idempotence).
"""
import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Chemins calculés à partir de l'emplacement du script :
# le script marche quel que soit le dossier d'où on le lance.
DOSSIER_ETL = Path(__file__).resolve().parent
DOSSIER_DONNEES = DOSSIER_ETL.parent / "01_DATA_RAW"
BASE = DOSSIER_ETL / "project_11_dwh.db"
BASE_TEMP = DOSSIER_ETL / "project_11_dwh.tmp.db"   # base en construction (voir rollback)

# Les 5 sources, référentiels d'abord (même ordre que 03_SQL)
TABLES = ["locations", "workers_synthetic", "equipment", "incidents", "safety_observations"]

# Identifiant du run : sert à savoir quel lancement a chargé quelle ligne
DEBUT = datetime.now()
RUN_ID = DEBUT.strftime("%Y%m%d_%H%M%S")

print("Run        :", RUN_ID)
print("Sources    :", DOSSIER_DONNEES)
print("Base       :", BASE)

# 1. Mémoire entre deux runs : la base est recréée à chaque lancement, donc on
# relit d'abord le manifeste des sources (pour détecter un fichier modifié)
# et le journal des runs (pour garder l'historique) du run précédent.
manifeste_precedent = None
journal_precedent = None
if BASE.exists():
    ancienne = sqlite3.connect(BASE)
    try:
        manifeste_precedent = pd.read_sql("SELECT * FROM raw_manifest", ancienne)
    except Exception:
        pass
    try:
        journal_precedent = pd.read_sql("SELECT * FROM etl_run_log", ancienne)
    except Exception:
        pass
    ancienne.close()

# 2. Construire dans un fichier temporaire (reproductibilité et rollback).
# La vraie base n'est remplacée qu'à la toute fin, si tout a réussi :
# en cas de panne, l'ancienne base reste intacte (tout ou rien).
if BASE_TEMP.exists():
    BASE_TEMP.unlink()

COLONNES_JOURNAL = ["run_id", "debut", "fin", "duree_s", "statut", "nb_raw", "nb_staging", "nb_rejets",
                    "nb_faits", "nb_lignes_mart", "nb_alertes", "nb_echecs", "message"]


def echec_du_run(type_erreur, erreur, trace):
    """Appelée par Python si le pipeline plante : ROLLBACK.
    On supprime la base temporaire, la base précédente n'est pas touchée,
    et on note le run en ECHEC dans etl_run_log."""
    try:
        if globals().get("con") is not None:
            con.close()
        if BASE_TEMP.exists():
            BASE_TEMP.unlink()
        fin = datetime.now()
        echec = pd.DataFrame([[RUN_ID, DEBUT.strftime("%Y-%m-%d %H:%M:%S"), fin.strftime("%Y-%m-%d %H:%M:%S"),
                               round((fin - DEBUT).total_seconds(), 2), "ECHEC",
                               None, None, None, None, None, None, None,
                               f"{type_erreur.__name__} : {erreur}"]], columns=COLONNES_JOURNAL)
        if journal_precedent is not None:
            echec = pd.concat([journal_precedent, echec], ignore_index=True)
        base_journal = sqlite3.connect(BASE)
        echec.to_sql("etl_run_log", base_journal, index=False, if_exists="replace")
        base_journal.close()
        print()
        print("ECHEC du run : rollback, la base précédente est conservée, échec noté dans etl_run_log.")
    except Exception as probleme:
        print("Rollback incomplet :", probleme)
    sys.__excepthook__(type_erreur, erreur, trace)


sys.excepthook = echec_du_run

con = sqlite3.connect(BASE_TEMP)


# ---------------------------------------------------------------------
# Étape 5.1 : RAW, charger les CSV tels quels (aucune transformation)
# ---------------------------------------------------------------------
# Tout est lu en texte (dtype=str) : RAW ne corrige rien, il garde la source
# fidèle. Les types viendront dans STAGING.
# Trois colonnes de traçabilité sont ajoutées : fichier source, numéro de
# ligne dans le fichier (l'en-tête est la ligne 1) et run.
print()
print("RAW : chargement des sources")

for table in TABLES:
    chemin = DOSSIER_DONNEES / (table + ".csv")
    df = pd.read_csv(chemin, dtype=str, keep_default_na=False)

    df["_source_file"] = table + ".csv"
    df["_row_num"] = range(2, len(df) + 2)
    df["_run_id"] = RUN_ID

    df.to_sql("raw_" + table, con, index=False, if_exists="replace")
    print(f"  raw_{table:<22} {len(df):>5} lignes chargées")


# ---------------------------------------------------------------------
# Étape 5.1 bis : manifeste des sources (nombre de lignes et empreinte MD5)
# ---------------------------------------------------------------------
# L'empreinte MD5 change si un seul octet du fichier change : elle prouve
# que RAW a été chargé depuis la bonne version de la source.
lignes_manifeste = []
for table in TABLES:
    chemin = DOSSIER_DONNEES / (table + ".csv")
    nb_lignes = len(pd.read_csv(chemin, dtype=str, keep_default_na=False))
    md5 = hashlib.md5(chemin.read_bytes()).hexdigest()
    lignes_manifeste.append([chemin.name, nb_lignes, md5, RUN_ID])

manifeste = pd.DataFrame(lignes_manifeste, columns=["fichier", "nb_lignes", "md5", "_run_id"])
manifeste.to_sql("raw_manifest", con, index=False, if_exists="replace")

print()
print("Manifeste des sources :")
print(manifeste[["fichier", "nb_lignes", "md5"]].to_string(index=False))


# ---------------------------------------------------------------------
# Contrôle : le nombre de lignes de RAW = celui du fichier source
# ---------------------------------------------------------------------
print()
print("Contrôle source = RAW :")
for _, ligne in manifeste.iterrows():
    table = ligne["fichier"].replace(".csv", "")
    dans_raw = con.execute(f"SELECT COUNT(*) FROM raw_{table}").fetchone()[0]
    statut = "OK" if dans_raw == ligne["nb_lignes"] else "ÉCART"
    print(f"  {table:<22} source {ligne['nb_lignes']:>5} = RAW {dans_raw:>5} : {statut}")


# ---------------------------------------------------------------------
# Étape 5.2 : STAGING, nettoyage, contrôles qualité (DQ) et rejets
# ---------------------------------------------------------------------
# On part de RAW (jamais des CSV). Pour chaque table :
#   1. standardiser : supprimer les espaces, mettre en majuscules
#   2. appliquer les contrôles DQ02 à DQ07
#   3. écrire les lignes refusées dans stg_rejects, avec la raison
#   4. écrire les lignes valides, typées, dans stg_<table>
# Une ligne refusée n'est jamais supprimée en silence : elle est tracée.
print()
print("STAGING : nettoyage et contrôles qualité")

DATE_MIN = pd.Timestamp("2020-01-01")
MAINTENANT = pd.Timestamp.now()
FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

# Règles propres à chaque table
REGLES = {
    "locations": {
        "cle": "location_id",
        "formats": {"location_id": r"LOC\d{3}"},
        "valeurs": {"area_type": ["BERTH", "GATE", "RAIL", "WORKSHOP", "YARD"]},
        "dates": [],
        "cles_etrangeres": [],
    },
    "workers_synthetic": {
        "cle": "worker_id",
        "formats": {"worker_id": r"W\d{4}"},
        "valeurs": {"role": ["SUPERVISOR", "OPERATOR", "TECHNICIAN", "DRIVER"],
                    "shift": ["A", "B", "C"]},
        "dates": [],
        "cles_etrangeres": [],
    },
    "equipment": {
        "cle": "equipment_id",
        "formats": {"equipment_id": r"CHE\d{2}"},
        "valeurs": {"equipment_type": ["RMG", "RTG", "TT", "FL", "RS"]},
        "dates": [],
        "cles_etrangeres": [],
    },
    "incidents": {
        "cle": "incident_id",
        "formats": {"incident_id": r"INC\d{6}", "location_id": r"LOC\d{3}",
                    "equipment_id": r"CHE\d{2}", "worker_id": r"W\d{4}"},
        "valeurs": {"severity": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "incident_type": ["COLLISION", "EQUIPMENT", "FALL", "NEAR_MISS", "PPE", "SPILL"]},
        "dates": ["incident_ts"],
        "cles_etrangeres": [("location_id", "locations", "location_id"),
                            ("equipment_id", "equipment", "equipment_id"),
                            ("worker_id", "workers_synthetic", "worker_id")],
    },
    "safety_observations": {
        "cle": "observation_id",
        "formats": {"observation_id": r"\d+", "location_id": r"LOC\d{3}"},
        "valeurs": {"observation_type": ["SAFE", "UNSAFE", "NEAR_MISS"],
                    "reported_by_role": ["OPERATOR", "SUPERVISOR", "HSE"]},
        "dates": ["observation_ts"],
        "cles_etrangeres": [("location_id", "locations", "location_id")],
    },
}

rejets = []         # un petit tableau par contrôle qui a trouvé des lignes en échec
resultats_dq = []   # une ligne par (règle, table)
stg = {}            # tables STAGING valides


def controler(df, table, regle, controles):
    """Applique une règle DQ : écrit les rejets et le résultat, renvoie le masque des lignes en échec.
    controles = liste de (masque des lignes en échec, raison du rejet)."""
    en_echec = pd.Series(False, index=df.index)
    for masque, raison in controles:
        lignes = df[masque]
        if len(lignes) > 0:
            rejets.append(pd.DataFrame({
                "_run_id": RUN_ID,
                "table_name": table,
                "source_file": table + ".csv",
                "row_num": lignes["_row_num"],
                "rule": regle,
                "reason": raison,
                "record": lignes["_brut"],
            }))
        en_echec = en_echec | masque
    statut = "OK" if not en_echec.any() else "REJETS"
    resultats_dq.append([RUN_ID, regle, table, len(df), int(en_echec.sum()), statut, ""])
    return en_echec


bilan = []  # (table, lignes RAW, lignes rejetées, lignes STAGING)

# Référentiels d'abord : les contrôles de clés étrangères (DQ07) des
# événements s'appuient sur les référentiels déjà nettoyés.
for table in TABLES:
    regles = REGLES[table]
    df = pd.read_sql(f"SELECT * FROM raw_{table}", con)
    colonnes = [c for c in df.columns if not c.startswith("_")]

    # La ligne telle qu'elle est dans la source, pour la garder dans stg_rejects
    df["_brut"] = df[colonnes].apply(lambda ligne: "|".join(ligne), axis=1)

    # DQ01 : volume non nul
    resultats_dq.append([RUN_ID, "DQ01", table, len(df), 0 if len(df) > 0 else 1,
                         "OK" if len(df) > 0 else "REJETS", "volume non nul"])

    # Standardisation : espaces supprimés, majuscules
    for c in colonnes:
        df[c] = df[c].str.strip().str.upper()

    # DQ02 : valeurs obligatoires (aucune colonne vide)
    rejete = controler(df, table, "DQ02",
                       [(df[c] == "", f"valeur obligatoire absente : {c}") for c in colonnes])

    # DQ03 : doublons sur la clé (on garde la première ligne, on refuse les suivantes)
    cle = regles["cle"]
    rejete |= controler(df, table, "DQ03",
                        [(df.duplicated(subset=cle, keep="first") & (df[cle] != ""),
                          f"doublon sur la clé {cle}")])

    # DQ04 : format des identifiants
    rejete |= controler(df, table, "DQ04",
                        [((df[c] != "") & ~df[c].str.fullmatch(motif),
                          f"format invalide : {c}") for c, motif in regles["formats"].items()])

    # DQ05 : dates valides, ni avant 2020 ni dans le futur
    if regles["dates"]:
        controles = []
        for c in regles["dates"]:
            dates = pd.to_datetime(df[c], format=FORMAT_DATE, errors="coerce")
            controles.append(((df[c] != "") & dates.isna(), f"date invalide : {c}"))
            controles.append((dates.notna() & ((dates < DATE_MIN) | (dates > MAINTENANT)),
                              f"date hors période (avant 2020 ou dans le futur) : {c}"))
        rejete |= controler(df, table, "DQ05", controles)

    # DQ06 : valeurs autorisées
    rejete |= controler(df, table, "DQ06",
                        [((df[c] != "") & ~df[c].isin(autorisees),
                          f"valeur non autorisée : {c}") for c, autorisees in regles["valeurs"].items()])

    # DQ07 : clés étrangères (la valeur doit exister dans le référentiel valide)
    if regles["cles_etrangeres"]:
        controles = []
        for c, table_ref, col_ref in regles["cles_etrangeres"]:
            connues = set(stg[table_ref][col_ref])
            controles.append(((df[c] != "") & ~df[c].isin(connues),
                              f"clé étrangère introuvable : {c} -> {table_ref}.{col_ref}"))
        rejete |= controler(df, table, "DQ07", controles)

    # Lignes valides, typées
    valides = df[~rejete].drop(columns=["_brut"]).copy()
    if table == "safety_observations":
        valides["observation_id"] = valides["observation_id"].astype(int)
    valides.to_sql("stg_" + table, con, index=False, if_exists="replace")
    stg[table] = valides
    bilan.append([table, len(df), int(rejete.sum()), len(valides)])

# DQ11 : alerte (pas un rejet) sur home_area, qui ne correspond à aucune zone
zones = set(stg["locations"]["location_id"])
sans_zone = int((~stg["equipment"]["home_area"].isin(zones)).sum())
resultats_dq.append([RUN_ID, "DQ11", "equipment", len(stg["equipment"]), sans_zone,
                     "ALERTE" if sans_zone > 0 else "OK",
                     "home_area (Yxx) ne correspond à aucune location_id (LOCxxx)"])

# Écriture des rejets et des résultats DQ
colonnes_rejets = ["_run_id", "table_name", "source_file", "row_num", "rule", "reason", "record"]
if rejets:
    table_rejets = pd.concat(rejets, ignore_index=True)
else:
    table_rejets = pd.DataFrame(columns=colonnes_rejets)
table_rejets.to_sql("stg_rejects", con, index=False, if_exists="replace")

dq_results = pd.DataFrame(resultats_dq, columns=["_run_id", "regle", "table_name",
                                                 "nb_controles", "nb_echecs", "statut", "detail"])
dq_results.to_sql("dq_results", con, index=False, if_exists="replace")

print()
print("Résultats des contrôles qualité :")
print(dq_results.drop(columns=["_run_id", "detail"]).to_string(index=False))

print()
print("Réconciliation RAW = STAGING + rejets :")
for table, nb_raw, nb_rejetes, nb_stg in bilan:
    statut = "OK" if nb_raw == nb_stg + nb_rejetes else "ÉCART"
    print(f"  {table:<22} RAW {nb_raw:>5} = STAGING {nb_stg:>5} + rejets {nb_rejetes:>3} : {statut}")
print(f"  Lignes dans stg_rejects : {len(table_rejets)}")


# ---------------------------------------------------------------------
# Étape 5.3 : CORE, les 9 dimensions
# ---------------------------------------------------------------------
# Chaque dimension reçoit une clé de substitution entière (*_key).
# Les clés sont attribuées dans un ordre fixe (trié) : deux runs donnent
# exactement les mêmes clés (idempotence). Voir dwh_conception.md.
print()
print("CORE : dimensions")

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
POIDS_GRAVITE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}   # hypothèse H1


def creer_dimension(nom, ddl, df):
    """Crée la table avec sa clé primaire, puis la remplit."""
    con.execute(ddl)
    df.to_sql(nom, con, index=False, if_exists="append")


def tranche_horaire(heure):
    """Hypothèse H3 : 4 blocs de 6 heures."""
    if heure < 6:
        return "NUIT"
    if heure < 12:
        return "MATIN"
    if heure < 18:
        return "APRES_MIDI"
    return "SOIR"


# dim_date : un jour par ligne, du premier au dernier jour avec des données
dates_evenements = pd.concat([pd.to_datetime(stg["incidents"]["incident_ts"]),
                              pd.to_datetime(stg["safety_observations"]["observation_ts"])])
calendrier = pd.date_range(dates_evenements.min().normalize(),
                           dates_evenements.max().normalize(), freq="D")
dim_date = pd.DataFrame({
    "date_key": calendrier.strftime("%Y%m%d").astype(int),
    "full_date": calendrier.strftime("%Y-%m-%d"),
    "year": calendrier.year,
    "month": calendrier.month,
    "day": calendrier.day,
    "year_month": calendrier.strftime("%Y-%m"),
    "month_name": [MOIS[m - 1] for m in calendrier.month],
    "day_of_week": calendrier.dayofweek + 1,          # 1 = lundi
    "days_in_month": calendrier.days_in_month,
})
creer_dimension("dim_date", """
    CREATE TABLE dim_date (
        date_key INTEGER PRIMARY KEY, full_date TEXT NOT NULL, year INTEGER NOT NULL,
        month INTEGER NOT NULL, day INTEGER NOT NULL, year_month TEXT NOT NULL,
        month_name TEXT NOT NULL, day_of_week INTEGER NOT NULL, days_in_month INTEGER NOT NULL)""",
    dim_date)

# dim_hour : 24 lignes, de 0 h à 23 h
dim_hour = pd.DataFrame({"hour_key": range(24)})
dim_hour["hour_label"] = dim_hour["hour_key"].apply(lambda h: f"{h:02d}:00")
dim_hour["time_band"] = dim_hour["hour_key"].apply(tranche_horaire)
creer_dimension("dim_hour", """
    CREATE TABLE dim_hour (
        hour_key INTEGER PRIMARY KEY, hour_label TEXT NOT NULL, time_band TEXT NOT NULL)""",
    dim_hour)

# Dimensions issues des référentiels : clé = 1, 2, 3... dans l'ordre de l'identifiant
def depuis_reference(table, cle_substitution, colonnes):
    df = stg[table].sort_values(colonnes[0])[colonnes].reset_index(drop=True)
    df.insert(0, cle_substitution, range(1, len(df) + 1))
    return df

creer_dimension("dim_location", """
    CREATE TABLE dim_location (
        location_key INTEGER PRIMARY KEY, location_id TEXT NOT NULL UNIQUE,
        area_type TEXT NOT NULL, area_name TEXT NOT NULL)""",
    depuis_reference("locations", "location_key", ["location_id", "area_type", "area_name"]))

creer_dimension("dim_equipment", """
    CREATE TABLE dim_equipment (
        equipment_key INTEGER PRIMARY KEY, equipment_id TEXT NOT NULL UNIQUE,
        equipment_type TEXT NOT NULL, home_area TEXT)""",
    depuis_reference("equipment", "equipment_key", ["equipment_id", "equipment_type", "home_area"]))

# dim_worker : contient worker_id (synthétique), table CONFIDENTIELLE, jamais exposée dans les MART
creer_dimension("dim_worker", """
    CREATE TABLE dim_worker (
        worker_key INTEGER PRIMARY KEY, worker_id TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL, shift TEXT NOT NULL)""",
    depuis_reference("workers_synthetic", "worker_key", ["worker_id", "role", "shift"]))

# Petites dimensions de domaine : on prend la liste complète des valeurs
# autorisées (pas seulement celles vues dans les données) pour que les clés
# restent stables.
types_incident = REGLES["incidents"]["valeurs"]["incident_type"]
dim_incident_type = pd.DataFrame({"incident_type": sorted(types_incident)})
dim_incident_type.insert(0, "incident_type_key", range(1, len(dim_incident_type) + 1))
dim_incident_type["is_near_miss"] = (dim_incident_type["incident_type"] == "NEAR_MISS").astype(int)
creer_dimension("dim_incident_type", """
    CREATE TABLE dim_incident_type (
        incident_type_key INTEGER PRIMARY KEY, incident_type TEXT NOT NULL UNIQUE,
        is_near_miss INTEGER NOT NULL)""",
    dim_incident_type)

# dim_severity : rangée dans l'ordre de gravité (et non alphabétique)
dim_severity = pd.DataFrame({"severity": REGLES["incidents"]["valeurs"]["severity"]})
dim_severity.insert(0, "severity_key", range(1, len(dim_severity) + 1))
dim_severity["severity_weight"] = dim_severity["severity"].map(POIDS_GRAVITE)
dim_severity["is_serious"] = dim_severity["severity"].isin(["HIGH", "CRITICAL"]).astype(int)
creer_dimension("dim_severity", """
    CREATE TABLE dim_severity (
        severity_key INTEGER PRIMARY KEY, severity TEXT NOT NULL UNIQUE,
        severity_weight INTEGER NOT NULL, is_serious INTEGER NOT NULL)""",
    dim_severity)

types_observation = sorted(REGLES["safety_observations"]["valeurs"]["observation_type"])
dim_observation_type = pd.DataFrame({"observation_type": types_observation})
dim_observation_type.insert(0, "observation_type_key", range(1, len(dim_observation_type) + 1))
creer_dimension("dim_observation_type", """
    CREATE TABLE dim_observation_type (
        observation_type_key INTEGER PRIMARY KEY, observation_type TEXT NOT NULL UNIQUE)""",
    dim_observation_type)

roles_declarant = sorted(REGLES["safety_observations"]["valeurs"]["reported_by_role"])
dim_reporter_role = pd.DataFrame({"reporter_role": roles_declarant})
dim_reporter_role.insert(0, "reporter_role_key", range(1, len(dim_reporter_role) + 1))
creer_dimension("dim_reporter_role", """
    CREATE TABLE dim_reporter_role (
        reporter_role_key INTEGER PRIMARY KEY, reporter_role TEXT NOT NULL UNIQUE)""",
    dim_reporter_role)

# Contrôle : nombre de lignes, clés distinctes, clés vides
print("  Période de dim_date :", dim_date["full_date"].iloc[0], "->", dim_date["full_date"].iloc[-1],
      f"({len(dim_date)} jours)")
print()
print("Contrôle des dimensions :")
for nom, cle in [("dim_date", "date_key"), ("dim_hour", "hour_key"),
                 ("dim_location", "location_key"), ("dim_equipment", "equipment_key"),
                 ("dim_worker", "worker_key"), ("dim_incident_type", "incident_type_key"),
                 ("dim_severity", "severity_key"), ("dim_observation_type", "observation_type_key"),
                 ("dim_reporter_role", "reporter_role_key")]:
    nb, nb_distinctes, nb_vides = con.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT {cle}), SUM({cle} IS NULL) FROM {nom}").fetchone()
    statut = "OK" if nb == nb_distinctes and nb_vides == 0 else "ERREUR"
    print(f"  {nom:<22} {nb:>4} lignes, {nb_distinctes:>4} clés distinctes, {nb_vides} clé vide : {statut}")


# ---------------------------------------------------------------------
# Étape 5.4 : CORE, les 2 tables de faits
# ---------------------------------------------------------------------
# Grain : 1 ligne = 1 incident / 1 ligne = 1 observation.
# On remplace chaque texte (LOC002, HIGH...) par la clé de substitution de
# sa dimension. Les clés sont relues dans la base : une seule source de vérité.
print()
print("CORE : tables de faits")

con.execute("PRAGMA foreign_keys = ON")   # SQLite refuse alors une clé étrangère cassée


def cles(dimension, colonne_metier, colonne_cle):
    """Dictionnaire {valeur métier: clé de substitution} lu dans la dimension."""
    lignes = con.execute(f"SELECT {colonne_metier}, {colonne_cle} FROM {dimension}").fetchall()
    return dict(lignes)


def mesure(dimension, colonne_metier, colonne_mesure):
    """Dictionnaire {valeur métier: mesure} (ex. gravité -> is_serious)."""
    lignes = con.execute(f"SELECT {colonne_metier}, {colonne_mesure} FROM {dimension}").fetchall()
    return dict(lignes)


# fact_incident
inc = stg["incidents"]
ts = pd.to_datetime(inc["incident_ts"])
fact_incident = pd.DataFrame({
    "incident_id": inc["incident_id"].values,
    "date_key": ts.dt.strftime("%Y%m%d").astype(int).values,
    "hour_key": ts.dt.hour.values,
    "location_key": inc["location_id"].map(cles("dim_location", "location_id", "location_key")).values,
    "equipment_key": inc["equipment_id"].map(cles("dim_equipment", "equipment_id", "equipment_key")).values,
    "worker_key": inc["worker_id"].map(cles("dim_worker", "worker_id", "worker_key")).values,
    "incident_type_key": inc["incident_type"].map(
        cles("dim_incident_type", "incident_type", "incident_type_key")).values,
    "severity_key": inc["severity"].map(cles("dim_severity", "severity", "severity_key")).values,
})
fact_incident["incident_count"] = 1
fact_incident["is_serious"] = inc["severity"].map(mesure("dim_severity", "severity", "is_serious")).values
fact_incident["is_near_miss"] = inc["incident_type"].map(
    mesure("dim_incident_type", "incident_type", "is_near_miss")).values
fact_incident["severity_weight"] = inc["severity"].map(
    mesure("dim_severity", "severity", "severity_weight")).values

con.execute("""
    CREATE TABLE fact_incident (
        incident_id       TEXT PRIMARY KEY,
        date_key          INTEGER NOT NULL REFERENCES dim_date(date_key),
        hour_key          INTEGER NOT NULL REFERENCES dim_hour(hour_key),
        location_key      INTEGER NOT NULL REFERENCES dim_location(location_key),
        equipment_key     INTEGER NOT NULL REFERENCES dim_equipment(equipment_key),
        worker_key        INTEGER NOT NULL REFERENCES dim_worker(worker_key),
        incident_type_key INTEGER NOT NULL REFERENCES dim_incident_type(incident_type_key),
        severity_key      INTEGER NOT NULL REFERENCES dim_severity(severity_key),
        incident_count    INTEGER NOT NULL,
        is_serious        INTEGER NOT NULL,
        is_near_miss      INTEGER NOT NULL,
        severity_weight   INTEGER NOT NULL)""")
fact_incident.to_sql("fact_incident", con, index=False, if_exists="append")
con.execute("CREATE INDEX idx_fi_location ON fact_incident(location_key)")
con.execute("CREATE INDEX idx_fi_date ON fact_incident(date_key)")
con.execute("CREATE INDEX idx_fi_worker ON fact_incident(worker_key)")

# fact_safety_observation
obs = stg["safety_observations"]
ts = pd.to_datetime(obs["observation_ts"])
fact_observation = pd.DataFrame({
    "observation_id": obs["observation_id"].values,
    "date_key": ts.dt.strftime("%Y%m%d").astype(int).values,
    "hour_key": ts.dt.hour.values,
    "location_key": obs["location_id"].map(cles("dim_location", "location_id", "location_key")).values,
    "observation_type_key": obs["observation_type"].map(
        cles("dim_observation_type", "observation_type", "observation_type_key")).values,
    "reporter_role_key": obs["reported_by_role"].map(
        cles("dim_reporter_role", "reporter_role", "reporter_role_key")).values,
})
fact_observation["observation_count"] = 1
fact_observation["is_unsafe"] = (obs["observation_type"] == "UNSAFE").astype(int).values
fact_observation["is_near_miss"] = (obs["observation_type"] == "NEAR_MISS").astype(int).values

con.execute("""
    CREATE TABLE fact_safety_observation (
        observation_id       INTEGER PRIMARY KEY,
        date_key             INTEGER NOT NULL REFERENCES dim_date(date_key),
        hour_key             INTEGER NOT NULL REFERENCES dim_hour(hour_key),
        location_key         INTEGER NOT NULL REFERENCES dim_location(location_key),
        observation_type_key INTEGER NOT NULL REFERENCES dim_observation_type(observation_type_key),
        reporter_role_key    INTEGER NOT NULL REFERENCES dim_reporter_role(reporter_role_key),
        observation_count    INTEGER NOT NULL,
        is_unsafe            INTEGER NOT NULL,
        is_near_miss         INTEGER NOT NULL)""")
fact_observation.to_sql("fact_safety_observation", con, index=False, if_exists="append")
con.execute("CREATE INDEX idx_fo_location ON fact_safety_observation(location_key)")
con.execute("CREATE INDEX idx_fo_date ON fact_safety_observation(date_key)")


# ---------------------------------------------------------------------
# Étape 5.4 bis : les 5 contrôles du TP S3 sur les faits
# ---------------------------------------------------------------------
print()
print("Contrôles des faits :")

FAITS = {
    "fact_incident": {
        "cle_metier": "incident_id", "nb_stg": len(stg["incidents"]), "mesure_compte": "incident_count",
        "dimensions": [("date_key", "dim_date"), ("hour_key", "dim_hour"),
                       ("location_key", "dim_location"), ("equipment_key", "dim_equipment"),
                       ("worker_key", "dim_worker"), ("incident_type_key", "dim_incident_type"),
                       ("severity_key", "dim_severity")],
    },
    "fact_safety_observation": {
        "cle_metier": "observation_id", "nb_stg": len(stg["safety_observations"]),
        "mesure_compte": "observation_count",
        "dimensions": [("date_key", "dim_date"), ("hour_key", "dim_hour"),
                       ("location_key", "dim_location"),
                       ("observation_type_key", "dim_observation_type"),
                       ("reporter_role_key", "dim_reporter_role")],
    },
}


ERREURS_CONTROLE = []   # contrôles critiques en échec : ils bloquent la publication de la base


def afficher_controle(libelle, ok, detail, bloquant=True):
    """bloquant=True : un échec arrête le run (rollback). bloquant=False : simple information,
    utilisé pour les chiffres de référence du jeu officiel, qui changent légitimement si des
    lignes sont rejetées ou si les données évoluent."""
    etat = "OK" if ok else ("ERREUR" if bloquant else "ÉCART (info)")
    print(f"  {libelle:<44} {detail:<28} : {etat}")
    if not ok and bloquant:
        ERREURS_CONTROLE.append(libelle)


for fait, p in FAITS.items():
    print(f" {fait}")
    # 1. COUNT : autant de lignes que dans STAGING
    nb = con.execute(f"SELECT COUNT(*) FROM {fait}").fetchone()[0]
    afficher_controle("1. COUNT (fait = STAGING)", nb == p["nb_stg"], f"{nb} = {p['nb_stg']}")

    # 2. Clés NULL : aucune clé de dimension vide
    cond = " OR ".join(f"{c} IS NULL" for c, _ in p["dimensions"])
    nb_null = con.execute(f"SELECT COUNT(*) FROM {fait} WHERE {cond}").fetchone()[0]
    afficher_controle("2. Clés NULL", nb_null == 0, f"{nb_null} ligne(s)")

    # 3. Unicité : une ligne par clé métier (le grain)
    nb_distinctes = con.execute(f"SELECT COUNT(DISTINCT {p['cle_metier']}) FROM {fait}").fetchone()[0]
    afficher_controle("3. Unicité du grain", nb == nb_distinctes, f"{nb} lignes, {nb_distinctes} clés")

    # 4. Correspondances : chaque clé existe dans sa dimension (aucun orphelin)
    nb_orphelins = 0
    for colonne, dimension in p["dimensions"]:
        nb_orphelins += con.execute(
            f"SELECT COUNT(*) FROM {fait} f LEFT JOIN {dimension} d ON d.{colonne} = f.{colonne} "
            f"WHERE d.{colonne} IS NULL").fetchone()[0]
    afficher_controle("4. Correspondances avec les dimensions", nb_orphelins == 0,
                      f"{nb_orphelins} orphelin(s)")

    # 5. SUM(count) : la somme de la mesure de comptage égale le nombre de lignes
    somme = con.execute(f"SELECT SUM({p['mesure_compte']}) FROM {fait}").fetchone()[0]
    afficher_controle("5. SUM(count) = nombre de lignes", somme == p["nb_stg"], f"{somme} = {p['nb_stg']}")

erreurs_cles = con.execute("PRAGMA foreign_key_check").fetchall()
print(f"  PRAGMA foreign_key_check : {'OK, aucune erreur' if not erreurs_cles else str(len(erreurs_cles)) + ' erreur(s)'}")

# Chiffres de contrôle métier, calculés depuis les faits
total, graves = con.execute("SELECT SUM(incident_count), SUM(is_serious) FROM fact_incident").fetchone()
nm_inc = con.execute("SELECT SUM(is_near_miss) FROM fact_incident").fetchone()[0]
nm_obs = con.execute("SELECT SUM(is_near_miss) FROM fact_safety_observation").fetchone()[0]
print()
print("Chiffres de contrôle métier :")
print(f"  Incidents graves : {graves} / {total} = {100 * graves / total:.1f} %   (attendu 22,3 %)")
print(f"  Near-miss        : {nm_inc} + {nm_obs} = {nm_inc + nm_obs}   (attendu 225 + 534 = 759)")


# ---------------------------------------------------------------------
# Étape 5.5 : MART, les 6 tables d'agrégats (prêtes pour l'EDA et le dashboard)
# ---------------------------------------------------------------------
# Les MART sont calculées uniquement depuis CORE (faits + dimensions).
# Elles ne contiennent que des agrégats : jamais de worker_id.
print()
print("MART : tables d'agrégats")

MARTS = {}

# KPI1 : incidents par mois. Un mois est complet si les données couvrent
# tous ses jours (jours dans dim_date = jours du mois). Octobre s'arrête au 28.
MARTS["mart_incidents_month"] = """
    WITH calendrier AS (
        SELECT year_month, COUNT(*) AS jours_couverts, MAX(days_in_month) AS jours_du_mois
        FROM dim_date GROUP BY year_month),
    inc AS (
        SELECT d.year_month, SUM(f.incident_count) AS nb_incidents,
               SUM(f.is_serious) AS nb_graves, SUM(f.is_near_miss) AS nb_near_miss
        FROM fact_incident f JOIN dim_date d ON d.date_key = f.date_key
        GROUP BY d.year_month)
    SELECT c.year_month AS mois,
           COALESCE(i.nb_incidents, 0) AS nb_incidents,
           COALESCE(i.nb_graves, 0) AS nb_graves,
           CASE WHEN COALESCE(i.nb_incidents, 0) = 0 THEN 0.0
                ELSE ROUND(100.0 * i.nb_graves / i.nb_incidents, 1) END AS pct_graves,
           COALESCE(i.nb_near_miss, 0) AS nb_near_miss,
           c.jours_couverts,
           CASE WHEN c.jours_couverts = c.jours_du_mois THEN 1 ELSE 0 END AS mois_complet
    FROM calendrier c LEFT JOIN inc i ON i.year_month = c.year_month
    ORDER BY c.year_month"""

# KPI2 : répartition par gravité (dans l'ordre LOW -> CRITICAL)
MARTS["mart_severity_distribution"] = """
    SELECT s.severity,
           COALESCE(SUM(f.incident_count), 0) AS nb_incidents,
           ROUND(100.0 * COALESCE(SUM(f.incident_count), 0)
                 / (SELECT SUM(incident_count) FROM fact_incident), 1) AS pct
    FROM dim_severity s LEFT JOIN fact_incident f ON f.severity_key = s.severity_key
    GROUP BY s.severity_key, s.severity
    ORDER BY s.severity_key"""

# KPI3 : zones. Score de risque (formule de Steps, À CONFIRMER avec Fatouma) :
# 100 x (0,5 x graves + 0,3 x volume + 0,2 x % unsafe), chacun divisé par son maximum.
MARTS["mart_incidents_by_area"] = """
    WITH inc AS (
        SELECT location_key, SUM(incident_count) AS nb_incidents, SUM(is_serious) AS nb_graves
        FROM fact_incident GROUP BY location_key),
    obs AS (
        SELECT location_key, SUM(observation_count) AS nb_observations, SUM(is_unsafe) AS nb_unsafe
        FROM fact_safety_observation GROUP BY location_key),
    zone AS (
        SELECT l.location_id, l.area_type,
               COALESCE(i.nb_incidents, 0) AS nb_incidents,
               COALESCE(i.nb_graves, 0) AS nb_graves,
               COALESCE(o.nb_observations, 0) AS nb_observations,
               COALESCE(o.nb_unsafe, 0) AS nb_unsafe,
               CASE WHEN COALESCE(o.nb_observations, 0) = 0 THEN 0.0
                    ELSE 100.0 * o.nb_unsafe / o.nb_observations END AS pct_unsafe
        FROM dim_location l
        LEFT JOIN inc i ON i.location_key = l.location_key
        LEFT JOIN obs o ON o.location_key = l.location_key)
    SELECT location_id, area_type, nb_incidents, nb_graves, nb_observations, nb_unsafe,
           ROUND(pct_unsafe, 1) AS pct_unsafe,
           ROUND(100.0 * (0.5 * nb_graves / MAX(nb_graves) OVER ()
                        + 0.3 * nb_incidents / MAX(nb_incidents) OVER ()
                        + 0.2 * pct_unsafe / MAX(pct_unsafe) OVER ()), 1) AS score_risque
    FROM zone
    ORDER BY score_risque DESC, location_id"""

# KPI4 : near-miss. On additionne les 2 sources (décision validée).
MARTS["mart_near_miss"] = """
    WITH mois AS (SELECT DISTINCT year_month FROM dim_date),
    inc AS (
        SELECT d.year_month, SUM(f.is_near_miss) AS nm, SUM(f.is_serious) AS graves
        FROM fact_incident f JOIN dim_date d ON d.date_key = f.date_key
        GROUP BY d.year_month),
    obs AS (
        SELECT d.year_month, SUM(f.is_near_miss) AS nm
        FROM fact_safety_observation f JOIN dim_date d ON d.date_key = f.date_key
        GROUP BY d.year_month)
    SELECT m.year_month AS mois,
           COALESCE(i.nm, 0) AS near_miss_incidents,
           COALESCE(o.nm, 0) AS near_miss_observations,
           COALESCE(i.nm, 0) + COALESCE(o.nm, 0) AS near_miss_total,
           COALESCE(i.graves, 0) AS incidents_graves
    FROM mois m
    LEFT JOIN inc i ON i.year_month = m.year_month
    LEFT JOIN obs o ON o.year_month = m.year_month
    ORDER BY m.year_month"""

# KPI5 : types d'incident classés du plus fréquent au moins fréquent
MARTS["mart_recurring_incident_type"] = """
    SELECT RANK() OVER (ORDER BY nb_incidents DESC) AS rang,
           incident_type, nb_incidents,
           ROUND(100.0 * nb_incidents / (SELECT SUM(incident_count) FROM fact_incident), 1) AS pct
    FROM (SELECT t.incident_type, COALESCE(SUM(f.incident_count), 0) AS nb_incidents
          FROM dim_incident_type t
          LEFT JOIN fact_incident f ON f.incident_type_key = t.incident_type_key
          GROUP BY t.incident_type_key, t.incident_type)
    ORDER BY rang, incident_type"""

# KPI6 : incidents par travailleur, pour chaque rôle et équipe.
# Hypothèse : pas d'heures travaillées, on divise par l'effectif.
MARTS["mart_incident_rate_shift_role"] = """
    SELECT w.role, w.shift,
           COUNT(DISTINCT w.worker_key) AS nb_travailleurs,
           COALESCE(SUM(f.incident_count), 0) AS nb_incidents,
           ROUND(1.0 * COALESCE(SUM(f.incident_count), 0) / COUNT(DISTINCT w.worker_key), 2)
               AS incidents_par_travailleur
    FROM dim_worker w LEFT JOIN fact_incident f ON f.worker_key = w.worker_key
    GROUP BY w.role, w.shift
    ORDER BY incidents_par_travailleur DESC, w.role, w.shift"""

for nom, requete in MARTS.items():
    con.execute(f"CREATE TABLE {nom} AS {requete}")

# Aperçu de chaque MART
for nom, nb_lignes_affichees in [("mart_incidents_month", 10), ("mart_severity_distribution", 4),
                                 ("mart_incidents_by_area", 5), ("mart_near_miss", 10),
                                 ("mart_recurring_incident_type", 6),
                                 ("mart_incident_rate_shift_role", 5)]:
    apercu = pd.read_sql(f"SELECT * FROM {nom}", con)
    print()
    print(f"{nom} ({len(apercu)} lignes) :")
    print(apercu.head(nb_lignes_affichees).to_string(index=False))

# Contrôles des MART : chiffres attendus
print()
print("Contrôles des MART (les chiffres « attendu » sont ceux du jeu officiel : un écart y est informatif) :")


def valeur(requete):
    return con.execute(requete).fetchone()[0]


nb_faits_incidents = valeur("SELECT COUNT(*) FROM fact_incident")
moyenne_kpi1 = valeur("SELECT ROUND(AVG(nb_incidents), 1) FROM mart_incidents_month WHERE mois_complet = 1")
nb_mois_complets = valeur("SELECT COUNT(*) FROM mart_incidents_month WHERE mois_complet = 1")
afficher_controle("KPI1 moyenne des mois complets", moyenne_kpi1 == 144.0,
                  f"{moyenne_kpi1} ({nb_mois_complets} mois), attendu 144,0", bloquant=False)
oct_complet = valeur("SELECT mois_complet FROM mart_incidents_month WHERE mois = '2026-10'")
afficher_controle("Octobre exclu (mois_complet = 0)", oct_complet == 0, f"mois_complet = {oct_complet}", bloquant=False)
afficher_controle("Total incidents par mois = nombre de faits",
                  valeur("SELECT SUM(nb_incidents) FROM mart_incidents_month") == nb_faits_incidents,
                  f"{nb_faits_incidents} faits")
pct_graves = valeur("SELECT ROUND(100.0 * SUM(nb_graves) / SUM(nb_incidents), 1) FROM mart_incidents_month")
afficher_controle("Incidents graves", pct_graves == 22.3, f"{pct_graves} %, attendu 22,3 %", bloquant=False)
afficher_controle("Total par gravité = nombre de faits",
                  valeur("SELECT SUM(nb_incidents) FROM mart_severity_distribution") == nb_faits_incidents, "")
afficher_controle("Total par zone = nombre de faits",
                  valeur("SELECT SUM(nb_incidents) FROM mart_incidents_by_area") == nb_faits_incidents, "")
nm_total = valeur("SELECT SUM(near_miss_total) FROM mart_near_miss")
afficher_controle("Near-miss 225 + 534", nm_total == 759, f"{nm_total}, attendu 759", bloquant=False)
spill = valeur("SELECT pct FROM mart_recurring_incident_type WHERE incident_type = 'SPILL' AND rang = 1")
afficher_controle("SPILL type le plus fréquent", spill == 18.1, f"{spill} %, attendu 18,1 %", bloquant=False)
operateur_a = valeur("SELECT incidents_par_travailleur FROM mart_incident_rate_shift_role "
                     "WHERE role = 'OPERATOR' AND shift = 'A'")
afficher_controle("OPERATOR équipe A", operateur_a == 4.84, f"{operateur_a}, attendu 4,84", bloquant=False)
afficher_controle("Effectif total = nombre de travailleurs (dim_worker)",
                  valeur("SELECT SUM(nb_travailleurs) FROM mart_incident_rate_shift_role")
                  == valeur("SELECT COUNT(*) FROM dim_worker"), "")
afficher_controle("Incidents par rôle/équipe = nombre de faits",
                  valeur("SELECT SUM(nb_incidents) FROM mart_incident_rate_shift_role") == nb_faits_incidents, "")

# Confidentialité : aucune colonne d'identifiant de travailleur dans les MART
colonnes_interdites = 0
for nom in MARTS:
    for colonne in con.execute(f"PRAGMA table_info({nom})").fetchall():
        if "worker" in colonne[1].lower():
            colonnes_interdites += 1
afficher_controle("Aucun worker_id dans les MART", colonnes_interdites == 0,
                  f"{colonnes_interdites} colonne(s) interdite(s)")


# ---------------------------------------------------------------------
# Étape 5.6 : mart_kpi_summary, les 8 KPI en une seule table
# ---------------------------------------------------------------------
# Cette table ne recalcule rien depuis les faits : elle reprend les chiffres
# des autres MART. Le dashboard lira ses 8 cartes ici.
print()
print("MART : mart_kpi_summary")

zone_top = con.execute("SELECT location_id, area_type, score_risque FROM mart_incidents_by_area "
                       "ORDER BY score_risque DESC, location_id LIMIT 1").fetchone()
type_top = con.execute("SELECT incident_type, nb_incidents, pct FROM mart_recurring_incident_type "
                       "WHERE rang = 1 ORDER BY incident_type LIMIT 1").fetchone()
groupe_top = con.execute("SELECT role, shift, incidents_par_travailleur FROM mart_incident_rate_shift_role "
                         "ORDER BY incidents_par_travailleur DESC, role, shift LIMIT 1").fetchone()

lignes_kpi = [
    ["KPI1", "Incidents/month",
     "Moyenne mensuelle des incidents sur les mois complets (octobre exclu, il s'arrête au 28)",
     valeur("SELECT ROUND(AVG(nb_incidents), 1) FROM mart_incidents_month WHERE mois_complet = 1"),
     "incidents/mois"],
    ["KPI2", "Severity distribution",
     "Part des incidents graves (gravité HIGH ou CRITICAL)",
     valeur("SELECT ROUND(100.0 * SUM(nb_graves) / SUM(nb_incidents), 1) FROM mart_incidents_month"),
     "%"],
    ["KPI3", "Incidents by area",
     f"Score de risque de la zone la plus à risque : {zone_top[0]} ({zone_top[1]})",
     zone_top[2], "score /100"],
    ["KPI4", "Near-miss count",
     "Presque-accidents : incidents NEAR_MISS + observations NEAR_MISS",
     valeur("SELECT SUM(near_miss_total) FROM mart_near_miss"),
     "near-miss"],
    ["KPI5", "Recurring incident type",
     f"Part du type d'incident le plus fréquent : {type_top[0]} ({type_top[1]} incidents)",
     type_top[2], "%"],
    ["KPI6", "Incident rate by shift/role",
     f"Incidents par travailleur du groupe le plus touché : {groupe_top[0]}, équipe {groupe_top[1]} "
     "(par effectif, faute d'heures travaillées)",
     groupe_top[2], "incidents/travailleur"],
    ["KPI7", "Unsafe observations",
     "Part des observations de terrain classées UNSAFE",
     valeur("SELECT ROUND(100.0 * SUM(nb_unsafe) / SUM(nb_observations), 1) FROM mart_incidents_by_area"),
     "%"],
    ["KPI8", "Total incidents",
     "Nombre d'incidents chargés dans le DWH (contrôle de réconciliation)",
     valeur("SELECT SUM(nb_incidents) FROM mart_severity_distribution"),
     "incidents"],
]
kpi_summary = pd.DataFrame(lignes_kpi, columns=["kpi_id", "kpi", "libelle", "valeur", "unite"])
kpi_summary["valeur"] = kpi_summary["valeur"].astype(float)
kpi_summary.to_sql("mart_kpi_summary", con, index=False, if_exists="replace")

print(pd.read_sql("SELECT kpi_id, kpi, valeur, unite FROM mart_kpi_summary", con).to_string(index=False))

print()
print("Les 5 chiffres de contrôle, lus dans mart_kpi_summary :")
for kpi_id, attendu, nom in [("KPI1", 144.0, "Moyenne mensuelle (mois complets)"),
                             ("KPI2", 22.3, "Incidents graves (%)"),
                             ("KPI4", 759.0, "Near-miss (225 + 534)"),
                             ("KPI5", 18.1, "SPILL, type le plus fréquent (%)"),
                             ("KPI6", 4.84, "OPERATOR équipe A (incidents/travailleur)")]:
    obtenu = valeur(f"SELECT valeur FROM mart_kpi_summary WHERE kpi_id = '{kpi_id}'")
    afficher_controle(f"{kpi_id} {nom}", obtenu == attendu, f"{obtenu}, attendu {attendu}", bloquant=False)
afficher_controle("8 KPI présents, aucun vide",
                  valeur("SELECT COUNT(*) FROM mart_kpi_summary WHERE valeur IS NOT NULL") == 8, "")


# ---------------------------------------------------------------------
# Étape 5.7 : monitoring (DQ08 à DQ10, DQ12) et journal des runs
# ---------------------------------------------------------------------
# DQ08 réconciliation  : RAW = rejets + CORE, pour chaque table
# DQ09 fraîcheur       : le dernier événement n'est pas trop ancien
# DQ10 variation       : le volume d'un mois complet ne saute pas de plus de 25 %
# DQ12 intégrité       : les fichiers sources n'ont pas changé depuis le run précédent
# Seuils = hypothèses du groupe, à documenter dans 06_GOVERNANCE.
print()
print("MONITORING : réconciliation, fraîcheur, variation, intégrité des sources")

SEUIL_FRAICHEUR_JOURS = 31      # un chargement mensuel : au-delà, les données sont trop vieilles
SEUIL_VARIATION_PCT = 25.0      # variation maximale d'un mois complet au suivant

resultats_monitoring = []


def ajouter_dq(regle, table, nb_controles, nb_echecs, statut_si_echec, detail):
    statut = "OK" if nb_echecs == 0 else statut_si_echec
    resultats_monitoring.append([RUN_ID, regle, table, int(nb_controles), int(nb_echecs), statut, detail])


# DQ08 : réconciliation RAW = STAGING + rejets = CORE
CORE_DE = {"locations": "dim_location", "workers_synthetic": "dim_worker",
           "equipment": "dim_equipment", "incidents": "fact_incident",
           "safety_observations": "fact_safety_observation"}
for table, nb_raw, nb_rejetes, nb_stg in bilan:
    nb_core = valeur(f"SELECT COUNT(*) FROM {CORE_DE[table]}")
    ecart = abs(nb_raw - (nb_rejetes + nb_core))
    ajouter_dq("DQ08", table, nb_raw, ecart, "ECHEC",
               f"RAW {nb_raw} = rejets {nb_rejetes} + {CORE_DE[table]} {nb_core}")

# DQ09 : fraîcheur, âge du dernier événement par rapport à aujourd'hui
aujourd_hui = pd.Timestamp.now().normalize()
for fait in ["fact_incident", "fact_safety_observation"]:
    derniere = pd.to_datetime(valeur(
        f"SELECT MAX(d.full_date) FROM {fait} f JOIN dim_date d ON d.date_key = f.date_key"))
    age = (aujourd_hui - derniere).days
    ajouter_dq("DQ09", fait, 1, 1 if age > SEUIL_FRAICHEUR_JOURS else 0, "ALERTE",
               f"dernier événement {derniere:%Y-%m-%d}, âge {age} j, seuil {SEUIL_FRAICHEUR_JOURS} j")

# DQ10 : variation du volume mensuel (mois complets seulement : octobre est tronqué)
mois_complets = con.execute("SELECT mois, nb_incidents FROM mart_incidents_month "
                            "WHERE mois_complet = 1 ORDER BY mois").fetchall()
nb_comparaisons = 0
mois_anormaux = []
for (mois_prec, nb_prec), (mois, nb) in zip(mois_complets, mois_complets[1:]):
    nb_comparaisons += 1
    variation = 100.0 * (nb - nb_prec) / nb_prec
    if abs(variation) > SEUIL_VARIATION_PCT:
        mois_anormaux.append(f"{mois} {variation:+.1f} % vs {mois_prec}")
ajouter_dq("DQ10", "mart_incidents_month", nb_comparaisons, len(mois_anormaux), "ALERTE",
           "; ".join(mois_anormaux) if mois_anormaux else f"aucune variation au-dessus de {SEUIL_VARIATION_PCT:.0f} %")

# DQ12 : les sources sont-elles identiques à celles du run précédent ? (MD5)
if manifeste_precedent is None:
    ajouter_dq("DQ12", "sources", len(manifeste), 0, "ALERTE",
               "premier run : manifeste de référence enregistré")
else:
    md5_precedent = dict(zip(manifeste_precedent["fichier"], manifeste_precedent["md5"]))
    modifies = [f for f, m in zip(manifeste["fichier"], manifeste["md5"]) if md5_precedent.get(f) != m]
    ajouter_dq("DQ12", "sources", len(manifeste), len(modifies), "ALERTE",
               ("source modifiée : " + ", ".join(modifies)) if modifies
               else "sources identiques au run précédent (MD5)")

pd.DataFrame(resultats_monitoring, columns=dq_results.columns).to_sql(
    "dq_results", con, index=False, if_exists="append")

print(pd.read_sql("SELECT regle, table_name, nb_controles, nb_echecs, statut, detail FROM dq_results "
                  "WHERE regle IN ('DQ08', 'DQ09', 'DQ10', 'DQ12') ORDER BY regle, table_name", con
                  ).to_string(index=False))

# Verrou : si un contrôle critique a échoué, on s'arrête ici.
# L'exception déclenche le rollback (echec_du_run) : rien n'est publié.
echecs_dq08 = [r[2] for r in resultats_monitoring if r[1] == "DQ08" and r[5] == "ECHEC"]
if ERREURS_CONTROLE or echecs_dq08:
    raise RuntimeError("contrôle(s) critique(s) en échec : "
                       + "; ".join(ERREURS_CONTROLE + [f"DQ08 {t}" for t in echecs_dq08]))

# Journal des runs : volumes, durée, statut. L'historique des runs précédents est conservé.
FIN = datetime.now()
journal = pd.DataFrame([[
    RUN_ID,
    DEBUT.strftime("%Y-%m-%d %H:%M:%S"),
    FIN.strftime("%Y-%m-%d %H:%M:%S"),
    round((FIN - DEBUT).total_seconds(), 2),
    "SUCCES",
    sum(b[1] for b in bilan),                      # lignes RAW
    sum(b[3] for b in bilan),                      # lignes STAGING
    sum(b[2] for b in bilan),                      # lignes rejetées
    valeur("SELECT COUNT(*) FROM fact_incident") + valeur("SELECT COUNT(*) FROM fact_safety_observation"),
    sum(valeur(f"SELECT COUNT(*) FROM {nom}") for nom in list(MARTS) + ["mart_kpi_summary"]),
    valeur("SELECT COUNT(*) FROM dq_results WHERE statut = 'ALERTE'"),
    valeur("SELECT COUNT(*) FROM dq_results WHERE statut IN ('ECHEC', 'REJETS')"),
    "",                                            # message (rempli seulement en cas d'ECHEC)
]], columns=COLONNES_JOURNAL)
if journal_precedent is not None:
    journal = pd.concat([journal_precedent, journal], ignore_index=True)
journal.to_sql("etl_run_log", con, index=False, if_exists="replace")

print()
print(f"Journal etl_run_log ({len(journal)} run(s) enregistré(s)) :")
print(journal.tail(3).to_string(index=False))

# Publication : tout a réussi, la base temporaire remplace la base précédente
con.commit()
con.close()
os.replace(BASE_TEMP, BASE)
print()
print("Base publiée :", BASE.name)

