# Projet 11 — Port Safety & Incident Analytics

Master 2 IAMD — Gestion des Données Massives — Université de Djibouti

**Groupe 8 :** Mako Mohamed Aden & Fatouma Soubere Mahamoud

**Dashboard en ligne :** https://projet11-port-safety.streamlit.app/

---

## Sommaire

1. [Objectif](#objectif)
2. [Les données](#les-données)
3. [Architecture](#architecture)
4. [Résultats clés](#résultats-clés)
5. [Structure du dépôt](#structure-du-dépôt)
6. [Reproduire le projet de A à Z](#reproduire-le-projet-de-a-à-z)
7. [Organisation Git et répartition](#organisation-git-et-répartition)
8. [Avancement](#avancement)
9. [Limites](#limites)
10. [Charte graphique](#charte-graphique)

---

## Objectif

Le service HSE (Hygiène, Sécurité, Environnement) d'un terminal portuaire veut savoir **où, quand, comment et à qui** arrivent les incidents, les near-miss et les risques récurrents.

Nous avons construit une chaîne complète, des fichiers CSV jusqu'aux décisions HSE : base SQL, Data Warehouse, archive HDFS, gouvernance, analyse exploratoire et dashboard.

Toutes les données sont **synthétiques** : aucune donnée personnelle réelle n'est utilisée.

## Les données

Cinq fichiers CSV dans `01_DATA_RAW`, du 1er janvier au 28 octobre 2026, soit **5 315 lignes** :

| Fichier | Lignes | Rôle |
|---|---|---|
| `incidents.csv` | 1 400 | Événements datés |
| `safety_observations.csv` | 3 500 | Événements datés |
| `workers_synthetic.csv` | 350 | Référence |
| `equipment.csv` | 40 | Référence |
| `locations.csv` | 25 | Référence |

## Architecture

```
Sources CSV → SQL → Data Warehouse (RAW → STAGING → CORE → MART) → EDA → Dashboard → Décisions HSE
                                          └──────────→ Archive HDFS (historique brut + MART en Parquet)
```

Schéma complet : `11_ARCHITECTURE/architecture_finale.png`.

| Brique | Outil | Rôle |
|---|---|---|
| Base source | SQLite, SQL | Vérifier les sources, premiers KPI (15 requêtes : jointures, agrégations, sous-requête, CTE, fonctions de fenêtre, index) |
| Data Warehouse | SQLite, Python (pandas) | 4 couches, schéma en étoile (2 tables de faits, 9 dimensions), 12 règles qualité DQ01 à DQ12 |
| Archive | HDFS (Hadoop 3.3.6, Docker) | 1 NameNode + 2 DataNodes, réplication 2, archive partitionnée par mois, manifeste MD5, MART en Parquet |
| Gouvernance | Fichiers CSV / Markdown | Dictionnaire enrichi, règles qualité, 36 liens de lineage, politique d'accès |
| Analyse | Notebook Python (pandas, matplotlib) | 6 graphiques interprétés |
| Dashboard | Streamlit | 3 KPI, 6 graphiques, filtres, export CSV, section qualité des données |

## Résultats clés

| KPI | Valeur |
|---|---|
| Incidents par mois (9 mois complets) | **144,0** (pic en mai : 171) |
| Part d'incidents graves (HIGH + CRITICAL) | **22,3 %** |
| Zone la plus à risque | **LOC015 (YARD), score 95,4 / 100** |
| Near-miss (incidents + observations) | **759** |
| Type d'incident le plus fréquent | **SPILL, 18,1 %** |
| Groupe le plus touché | **OPERATOR, équipe A : 4,84 incidents / travailleur** |
| Observations UNSAFE | **29,4 %** |
| Incidents chargés dans le DWH | **1 400** |

Définitions, formules et limites : `10_EXPECTED_KPIS/kpi_catalog.csv`.

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `00_BRIEF` | Sujet et consignes |
| `01_DATA_RAW` | Données sources CSV (**ne jamais les modifier**) |
| `02_DATA_DICTIONARY` | Dictionnaire de données |
| `03_SQL` | Schéma relationnel, construction de la base source, 15 requêtes SQL |
| `04_ETL` | Pipeline RAW → STAGING → CORE → MART, tests, conception du DWH |
| `05_HDFS` | Cluster Docker, préparation de l'archive, commandes HDFS, vérification MD5, export Parquet |
| `06_GOVERNANCE` | Dictionnaire enrichi, règles qualité, lineage, checklist de gouvernance |
| `07_EDA` | Notebook d'analyse exploratoire et les 6 figures |
| `08_DELIVERABLES` | Rapport final `rapport_final_projet.pdf` et ses sections en Markdown |
| `09_PRESENTATION` | Soutenance `Port_safety.pptx` |
| `10_EXPECTED_KPIS` | Catalogue des 8 KPI |
| `11_ARCHITECTURE` | Schéma d'architecture final |
| `12_DASHBOARD` | Application Streamlit, images et données exportées |

---

## Reproduire le projet de A à Z

Les bases SQLite et l'archive HDFS ne sont **pas** dans le dépôt (voir `.gitignore`) : les étapes ci-dessous les recréent. Suivez-les dans l'ordre. Sauf mention contraire, **toutes les commandes se lancent depuis la racine du projet**.

### Étape 0 — Prérequis

| Outil | Pour quoi | Obligatoire |
|---|---|---|
| Python 3.10 ou plus | Tous les scripts | Oui |
| Git | Récupérer le dépôt | Oui |
| Docker + Docker Compose | Cluster HDFS (étape 5) | Pour HDFS seulement |
| DB Browser for SQLite | Exécuter et voir les requêtes SQL (étape 2) | Conseillé |

### Étape 1 — Récupérer le projet et installer Python

```bash
git clone https://github.com/fatouu50/Port-Safety-Incident-Analytics-M2-IAMD-Gestion-des-Donn-es-Massives-.git port-safety
cd port-safety

python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

> Si vous utilisez Anaconda, faites d'abord `conda deactivate` : sinon les paquets s'installent dans le mauvais environnement.

### Étape 2 — SQL : base source et requêtes

**2.1 Construire la base**

```bash
python 03_SQL/build_source_db.py
```

Le script crée `03_SQL/project_11_sources.db` à partir de `03_SQL/schema_sources.sql` (tables, clés, contraintes) et des 5 CSV. On peut le relancer : la base est reconstruite à l'identique.

**2.2 Exécuter les requêtes** — deux façons :

*Avec DB Browser for SQLite (conseillé pour voir les résultats)*

1. **Ouvrir une base de données** → `03_SQL/project_11_sources.db`.
2. Onglet **Exécuter le SQL** → ouvrir le fichier `03_SQL/starter_queries.sql`.
3. Placer le curseur dans une requête et appuyer sur `Shift+F5` (exécuter la ligne courante) ; `F5` ou `Ctrl+Entrée` exécute tout le fichier.

*En ligne de commande (si `sqlite3` est installé)*

```bash
sqlite3 -header -column 03_SQL/project_11_sources.db < 03_SQL/starter_queries.sql
```

Les requêtes sont numérotées de Q01 à Q15 :

| Requêtes | Ce qu'elles font |
|---|---|
| Q01 | Volume de chaque table et période couverte |
| Q02 à Q04 | Jointures : incidents enrichis, graves par type de zone, clés orphelines |
| Q05 à Q08 | KPI : incidents par mois, gravité, near-miss, taux par rôle et équipe |
| Q09 à Q12 | Sous-requête, CTE + `RANK`, CTE + `LAG`, UNSAFE face aux incidents graves |
| Q13, Q14 | Qualité : unicité des identifiants, doublons métier |
| Q15 | Plans d'exécution avec et sans index |

### Étape 3 — Data Warehouse (ETL)

```bash
python 04_ETL/etl_pipeline.py      # RAW → STAGING → CORE → MART, crée 04_ETL/project_11_dwh.db
python 04_ETL/test_etl.py          # tests : idempotence, 11 rejets tracés, panne et rollback
```

- Le pipeline applique les 12 règles qualité (DQ01 à DQ12) et écrit les résultats dans `dq_results`.
- Il peut être relancé autant de fois qu'on veut : la base est reconstruite à l'identique.
- En cas d'erreur, la base précédente est conservée (rollback) et l'échec est noté dans `etl_run_log`.
- Tables MART produites : `mart_incidents_month`, `mart_severity_distribution`, `mart_incidents_by_area`, `mart_near_miss`, `mart_recurring_incident_type`, `mart_incident_rate_shift_role`, `mart_kpi_summary`.

Conception : `04_ETL/dwh_conception.md` et `04_ETL/schema_etoile.png`.

### Étape 4 — Analyse exploratoire (EDA)

```bash
jupyter notebook 07_EDA/eda_projet11.ipynb
```

Dans Jupyter : **Run → Run All Cells**. Le notebook lit les tables MART (l'étape 3 doit être faite) et enregistre les 6 graphiques dans `07_EDA/figures/`.

### Étape 5 — Archive HDFS avec Docker

> Toutes les commandes de cette étape se lancent **depuis le dossier `05_HDFS`**. Les commandes `hdfs` s'exécutent **dans le conteneur** : elles commencent toujours par `docker exec namenode`.

**5.1 Préparer l'archive sur le PC**

```bash
cd 05_HDFS
python prepare_archive.py
```

Le script crée `05_HDFS/archive/` : les CSV bruts découpés par mois (`year=2026/month=MM`), les tables de référence et un manifeste (`_manifest/manifest.csv`) avec le nombre de lignes et l'empreinte MD5 de chaque fichier.

**5.2 Démarrer le cluster**

Si un autre cluster Hadoop tourne déjà (par exemple celui d'un TP), arrêtez-le d'abord, sinon le port 9870 est déjà pris :

```bash
docker ps                          # voir ce qui tourne
docker stop $(docker ps -q)        # arrêter tous les conteneurs (rien n'est supprimé)
```

Puis :

```bash
docker compose up -d               # namenode, datanode1, datanode2 (Apache Hadoop 3.3.6)
docker ps                          # les 3 conteneurs doivent être « Up »
```

Attendez environ 30 secondes, puis ouvrez l'interface web : **http://localhost:9870** (onglet *Datanodes* : 2 nœuds actifs ; *Utilities → Browse the file system* : l'archive).

**5.3 Charger l'archive dans HDFS**

```bash
docker cp archive namenode:/tmp/archive
docker exec namenode hdfs dfs -mkdir -p /port_exam/project_11
docker exec namenode hdfs dfs -put -f /tmp/archive /port_exam/project_11/
```

**5.4 Vérifier le contenu, les blocs et la réplication**

```bash
docker exec namenode hdfs dfs -ls -R /port_exam/project_11
docker exec namenode hdfs dfs -count /port_exam/project_11/archive
docker exec namenode hdfs fsck /port_exam/project_11/archive
docker exec namenode hdfs dfs -setrep -w 2 /port_exam/project_11/archive
```

`fsck` doit afficher **HEALTHY** et une réplication moyenne de **2.0**.

**5.5 Test de panne** — un DataNode arrêté, le fichier reste lisible. Lancez les commandes **une par une** :

```bash
docker stop datanode1
docker exec namenode hdfs dfs -cat /port_exam/project_11/archive/reference/locations.csv 2>/dev/null
docker start datanode1
```

La lecture peut prendre environ 60 secondes : HDFS essaie d'abord le DataNode arrêté, puis lit la copie sur `datanode2`.

**5.6 Vérifier l'intégrité (lignes et MD5)**

```bash
python hdfs_verify.py
```

**5.7 Ajouter les tables MART en Parquet** (après l'étape 3)

```bash
python export_mart_parquet.py
docker exec namenode rm -rf /tmp/curated
docker cp archive/curated namenode:/tmp/curated
docker exec namenode hdfs dfs -put -f /tmp/curated /port_exam/project_11/archive/
docker exec namenode hdfs dfs -ls /port_exam/project_11/archive/curated/mart
python hdfs_verify.py
```

Résultat attendu : 31 fichiers, état **HEALTHY**, réplication 2, **23/23 CSV et 7/7 Parquet** identiques au manifeste.

**5.8 Arrêter le cluster**

```bash
docker compose stop                # garde les conteneurs ; « docker compose start » pour relancer
cd ..                              # revenir à la racine du projet
```

Toutes ces commandes sont aussi dans `05_HDFS/hdfs_commands.txt`.

### Étape 6 — Dashboard

```bash
streamlit run 12_DASHBOARD/app.py
```

Le dashboard s'ouvre sur **http://localhost:8501**. Pour l'arrêter : `Ctrl+C` dans le terminal.

- Si la base `04_ETL/project_11_dwh.db` n'existe pas, le dashboard lance lui-même le pipeline au démarrage.
- En haut : 3 KPI issus de la partie SQL (Q05 bis, Q06, Q07). Puis les 6 graphiques de l'EDA, avec 3 filtres : période, types de zone, équipes. Sous chaque titre, une mention indique quel filtre agit sur le graphique.
- Trois boutons exportent en CSV les données filtrées.
- En bas : la qualité des données (règles DQ01 à DQ12, rejets, dernier run de l'ETL, alertes connues).

Version en ligne : https://projet11-port-safety.streamlit.app/

### Étape 7 (facultative) — Schémas et rapport

```bash
python 11_ARCHITECTURE/faire_schemas.py        # schémas du rapport
python 08_DELIVERABLES/assembler_rapport.py    # rapport en PDF
```

### Récapitulatif

| # | Étape | Commande | Dossier |
|---|---|---|---|
| 1 | Installation | `pip install -r requirements.txt` | racine |
| 2 | Base source SQL | `python 03_SQL/build_source_db.py` | racine |
| 3 | Data Warehouse | `python 04_ETL/etl_pipeline.py` | racine |
| 3 | Tests du pipeline | `python 04_ETL/test_etl.py` | racine |
| 4 | EDA | `jupyter notebook 07_EDA/eda_projet11.ipynb` | racine |
| 5 | Archive HDFS | `python prepare_archive.py` puis `docker compose up -d` | `05_HDFS` |
| 6 | Dashboard | `streamlit run 12_DASHBOARD/app.py` | racine |

### Problèmes fréquents

| Message | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'matplotlib'` | Mauvais environnement Python (souvent Anaconda) | `conda deactivate`, `source .venv/bin/activate`, `pip install -r requirements.txt` |
| `no configuration file provided: not found` | `docker compose` lancé hors de `05_HDFS` | `cd 05_HDFS` puis relancer |
| `hdfs: command not found` | Commande `hdfs` tapée sur le PC | La préfixer : `docker exec namenode hdfs ...` |
| L'interface 9870 montre un autre cluster | Le Docker d'un autre projet tourne encore | `docker stop $(docker ps -q)` puis `docker compose up -d` |
| `hdfs_verify.py` échoue | Cluster éteint ou archive non chargée | Refaire 5.2 et 5.3 |

---

## Organisation Git et répartition

| Branche | Usage |
|---|---|
| `main` | Version propre et validée. On n'y travaille pas directement. |
| `fatouma` | Travail de Fatouma |
| `mako` | Travail de Mako |

Quand une partie est terminée et testée, on ouvre une **Pull Request** vers `main`.

| Membre | Parties |
|---|---|
| **Fatouma Soubere Mahamoud** | SQL (03), HDFS (05), EDA (07) |
| **Mako Mohamed Aden** | Data Warehouse et ETL (04), gouvernance (06), dashboard (12) |
| **Ensemble** | Données et KPI, architecture, rapport, présentation |

## Avancement

- [x] 03_SQL
- [x] 04_ETL
- [x] 05_HDFS
- [x] 06_GOVERNANCE
- [x] 07_EDA
- [x] Dashboard
- [x] 11_ARCHITECTURE
- [x] Rapport
- [x] Présentation

## Limites

- Données synthétiques et de petit volume : SQLite suffit, HDFS est une démonstration.
- « Incident grave » (HIGH ou CRITICAL) et le score de risque (50 % incidents graves, 30 % nombre d'incidents, 20 % % UNSAFE) sont des hypothèses du groupe.
- Pas d'heures travaillées dans les sources : le taux d'incidents est calculé par effectif.
- Le `home_area` des engins ne correspond à aucune zone (alerte DQ11).
- La politique d'accès est écrite, mais ni SQLite ni le cluster de démonstration ne l'appliquent.
- Le pipeline est lancé à la main : aucun ordonnanceur ne le déclenche automatiquement.

## Charte graphique

Rose + violet + blanc, à parts égales : le violet structure (titres, texte fort), le rose anime (barres principales, filtres, accents), les fonds restent clairs.

| Couleur | Code | Rôle |
|---|---|---|
| Violet foncé | `#4A1D6E` | Titres, texte fort, incidents graves dans les graphiques |
| Violet | `#7B3FA0` | Chiffres des cartes KPI, ligne de moyenne |
| Rose | `#EE82B7` | Couleur principale du thème (filtres), barres principales |
| Lavande | `#EDE4F5` | Fonds de cartes |
| Rose pâle | `#FDEEF5` | Fond des cartes en alerte |
| Blanc | `#FFFFFF` | Fond des cartes et des graphiques |
| Gravité | `#D9C8EA` → `#A77BC9` → `#EE82B7` → `#9E1F5C` | LOW → MEDIUM → HIGH → CRITICAL |
| Framboise | `#9E1F5C` | Valeurs en alerte, 1re barre d'un classement, mentions de filtre |
| Mois incomplet | `#CFC8D6` | Octobre (s'arrête au 28) |
| Statuts qualité | `#2E8B57` / `#D99A1B` | OK / ALERTE |

Le bandeau du dashboard est un dégradé violet foncé → violet → rose, avec une photo du port à gauche et le logo de l'Université de Djibouti à droite. Le fond de page est une photo du terminal sous un voile clair. Le thème Streamlit est réglé dans `.streamlit/config.toml` (`primaryColor = "#EE82B7"`).

Règles : jamais de texte rose sur fond blanc (illisible) ; la framboise est réservée à ce qui doit attirer l'œil ; les statuts qualité gardent vert et orange.
