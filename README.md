# Projet 11 — Port Safety & Incident Analytics

Master 2 IAMD — Gestion des Données Massives — Université de Djibouti

**Groupe :** Mako Mohamed Aden, Fatouma Soubere Mahamoud

## Objectif

Construire pour le service HSE (Hygiène, Sécurité, Environnement) d'un terminal portuaire un dispositif analytique qui répond à quatre questions : **où, quand, comment et à qui** arrivent les incidents, les near-miss et les risques récurrents.

Toutes les données sont **synthétiques** : aucune donnée personnelle réelle n'est utilisée.

## Chaîne de traitement

```
Sources CSV → SQL → Data Warehouse (RAW → STAGING → CORE → MART) → HDFS → EDA → Dashboard
```

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `00_BRIEF` | Sujet et consignes |
| `01_DATA_RAW` | Données sources CSV (**ne jamais les modifier**) |
| `02_DATA_DICTIONARY` | Dictionnaire de données |
| `03_SQL` | Modèle relationnel et requêtes SQL |
| `04_ETL` | Pipeline RAW → STAGING → CORE → MART |
| `05_HDFS` | Archivage de l'historique dans HDFS |
| `06_GOVERNANCE` | Qualité, lineage, accès, sécurité |
| `07_EDA` | Analyse exploratoire Python |
| `08_DELIVERABLES` | Rapport final (20 à 30 pages) |
| `09_PRESENTATION` | Soutenance (10 à 12 slides) |
| `10_EXPECTED_KPIS` | Catalogue des KPI |
| `11_ARCHITECTURE` | Schéma d'architecture final |

## Organisation Git

| Branche | Usage |
|---|---|
| `main` | Version propre et validée. On n'y travaille pas directement. |
| `fatouma` | Travail de Fatouma |
| `mako` | Travail de Mako |

Quand une partie est terminée et testée, on ouvre une **Pull Request** vers `main`, et l'autre membre la relit avant la fusion.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Outils complémentaires : DB Browser for SQLite, Docker Desktop (pour HDFS).

## Lancer le Data Warehouse

Depuis la racine du projet :

```powershell
python 04_ETL/etl_pipeline.py     # RAW -> STAGING -> CORE -> MART, crée 04_ETL/project_11_dwh.db
python 04_ETL/test_etl.py         # tests : idempotence, 11 rejets tracés, panne et rollback
```

Le pipeline peut être relancé autant de fois qu'on veut : la base est reconstruite à l'identique.
En cas d'erreur, la base précédente est conservée (rollback) et l'échec est noté dans `etl_run_log`.

Tables MART lues par l'EDA et le dashboard : `mart_incidents_month`, `mart_severity_distribution`,
`mart_incidents_by_area`, `mart_near_miss`, `mart_recurring_incident_type`,
`mart_incident_rate_shift_role`, `mart_kpi_summary`.

Conception du DWH : `04_ETL/dwh_conception.md`. Gouvernance : `06_GOVERNANCE/`
(règles qualité, lineage, dictionnaire enrichi, politique d'accès).

## Avancement

- [x] 03_SQL
- [x] 04_ETL
- [x] 05_HDFS
- [x] 06_GOVERNANCE
- [x] 07_EDA
- [ ] Dashboard
- [ ] 11_ARCHITECTURE
- [ ] Rapport
- [ ] Présentation
