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

## Avancement

- [x] 03_SQL
- [ ] 04_ETL
- [x] 05_HDFS
- [ ] 06_GOVERNANCE
- [ ] 07_EDA
- [ ] Dashboard
- [ ] 11_ARCHITECTURE
- [ ] Rapport
- [ ] Présentation
