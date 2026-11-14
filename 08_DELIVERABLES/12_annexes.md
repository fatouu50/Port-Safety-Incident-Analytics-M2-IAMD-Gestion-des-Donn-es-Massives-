# Annexes

## Annexe A. Glossaire

**Tableau 23. Glossaire des termes techniques**

| Terme | Définition simple |
|---|---|
| Agrégat | Résultat d'un regroupement : un total, une moyenne, un pourcentage. |
| Clé de substitution | Numéro entier créé par le pipeline pour identifier une ligne d'une dimension. |
| Clé étrangère | Colonne qui renvoie à une ligne d'une autre table. |
| Couche | Étape de rangement des données dans le Data Warehouse : RAW, STAGING, CORE, MART. |
| Dashboard | Tableau de bord interactif, ici une page unique qui affiche les indicateurs, les graphiques et l'état de la qualité des données. |
| Data Warehouse (DWH) | Base de données organisée pour l'analyse. |
| Dimension | Table qui décrit un axe d'analyse : date, zone, gravité. |
| DQ (Data Quality) | Qualité des données ; nom de nos 12 règles de contrôle (DQ01 à DQ12). |
| EDA | Analyse exploratoire : statistiques et graphiques pour repérer des tendances. |
| ETL | Programme qui extrait, transforme et charge les données. |
| Fait (table de faits) | Table des événements que l'on compte : incidents, observations. |
| Grain | Ce que représente une ligne d'une table. Exemple : 1 ligne = 1 incident. |
| HDFS | Système de fichiers qui répartit les données sur plusieurs machines. |
| HSE | Hygiène, Sécurité, Environnement : le service utilisateur du projet. |
| Idempotence | Propriété d'un traitement qui donne le même résultat quand on le relance. |
| KPI | Indicateur clé : chiffre suivi dans le temps pour décider. |
| Lineage | Chemin suivi par une donnée, de la source au chiffre affiché. |
| MART | Table de résultats déjà calculés, prête pour l'analyse. |
| MD5 | Empreinte de 32 caractères d'un fichier ; elle change si le fichier change. |
| Near-miss | Presque-accident : événement qui aurait pu causer un dommage. |
| Parquet | Format de fichier en colonnes, adapté à l'analyse. |
| Partition | Rangement des fichiers en dossiers selon une valeur, ici l'année et le mois. |
| Pipeline | Suite d'étapes automatiques qui transforme les sources en tables d'analyse. |
| Réconciliation | Contrôle des volumes : lignes reçues = lignes rejetées + lignes chargées. |
| Rejet | Ligne refusée par un contrôle, mise de côté avec la raison du refus. |
| Réplication | Copie d'un même fichier sur plusieurs machines. |
| Rollback | Retour à l'état précédent quand un traitement échoue. |
| Run | Une exécution complète du pipeline. |
| Schéma en étoile | Modèle où une table de faits est reliée à ses dimensions. |

## Annexe B. Reproduire les résultats

**Tableau 24. Commandes pour reconstruire le projet**

| Étape | Commande | Dossier de lancement |
|---|---|---|
| Base source SQL | `python 03_SQL/build_source_db.py` | racine du projet |
| Data Warehouse | `python 04_ETL/etl_pipeline.py` | racine du projet |
| Tests du pipeline | `python 04_ETL/test_etl.py` | racine du projet |
| Archive pour HDFS | `python prepare_archive.py` | `05_HDFS` |
| Cluster et chargement HDFS | `docker compose up -d`, puis les commandes de `hdfs_commands.txt` | `05_HDFS` |
| Schémas du rapport | `python 11_ARCHITECTURE/faire_schemas.py` | racine du projet |
| Dashboard | `streamlit run 12_DASHBOARD/app.py` | racine du projet |
| Rapport en PDF | `python 08_DELIVERABLES/assembler_rapport.py` | racine du projet |

Le tableau 24 donne l'ordre à suivre : base source, Data Warehouse, puis ce qui en dépend. Les bases et l'archive ne sont pas dans le dépôt : ces commandes les recréent. *Source : en-tête de chaque script ; `.gitignore`.*

## Annexe C. Où trouver les livrables dans le dépôt

**Tableau 25. Livrables demandés par le sujet et emplacement**

| Livrable demandé | Emplacement |
|---|---|
| Code source et scripts reproductibles | Dossiers `03_SQL`, `04_ETL`, `05_HDFS`, `07_EDA`, `12_DASHBOARD` |
| Base SQL / DWH, ou scripts pour la reconstruire | `03_SQL/build_source_db.py`, `04_ETL/etl_pipeline.py` |
| KPI | `10_EXPECTED_KPIS/kpi_catalog.csv` |
| Graphiques interprétés | `07_EDA/eda_projet11.ipynb`, `07_EDA/figures` |
| Schéma d'architecture final | `11_ARCHITECTURE/architecture_finale.png` |
| Dictionnaire de données enrichi | `06_GOVERNANCE/data_dictionary_enrichi.csv` (148 colonnes) |
| Règles de qualité, lineage, politique d'accès | Dossier `06_GOVERNANCE` |

Le tableau 25 relie chaque livrable du sujet à un fichier ; le dictionnaire enrichi (148 lignes) est fourni en fichier. *Source : sujet, § 6 ; arborescence du dépôt.*
