# 2. Description des sources et analyse des 5V

## 2.1 Objectif

Cette section décrit les cinq fichiers fournis, puis les analyse selon les 5V. Les 5V sont cinq critères qui servent à décrire un jeu de données massives : Volume, Vélocité, Variété, Véracité et Valeur.

## 2.2 Les cinq fichiers sources

Les données sont cinq fichiers au format CSV. Un fichier CSV est un fichier texte où chaque ligne est un enregistrement et où les valeurs sont séparées par des virgules. Ils sont rangés dans le dossier `01_DATA_RAW`, que nous ne modifions jamais.

**Tableau 2. Les cinq fichiers sources**

| Fichier | Contenu | Lignes | Colonnes | Taille | Clé |
|---|---|---|---|---|---|
| `incidents.csv` | 1 ligne = 1 incident | 1 400 | 7 | 88,0 ko | `incident_id` |
| `safety_observations.csv` | 1 ligne = 1 observation de sécurité | 3 500 | 5 | 164,8 ko | `observation_id` |
| `locations.csv` | 1 ligne = 1 zone du port | 25 | 3 | 0,6 ko | `location_id` |
| `workers_synthetic.csv` | 1 ligne = 1 travailleur synthétique | 350 | 3 | 6,5 ko | `worker_id` |
| `equipment.csv` | 1 ligne = 1 engin de manutention | 40 | 3 | 0,6 ko | `equipment_id` |
| **Total** | | **5 315** | **21** | **260,5 ko** | |

Le tableau 2 distingue deux familles. Les deux premiers fichiers sont des événements : ils grossissent avec le temps. Les trois autres sont des référentiels : ils décrivent le site et changent peu. Les événements couvrent la période du 1er janvier au 28 octobre 2026. Le dernier mois est donc incomplet, ce qui compte pour les moyennes mensuelles (section 5). *Source : fichiers de `01_DATA_RAW` ; `02_DATA_DICTIONARY/data_dictionary.csv` ; requêtes Q01 et Q01 bis de `03_SQL/starter_queries.sql`.*

Un incident porte une date, une zone, un engin, un travailleur, un type (6 valeurs, de `COLLISION` à `SPILL`) et une gravité (4 niveaux, de `LOW` à `CRITICAL`). Une observation porte une date, une zone, un type (`SAFE`, `UNSAFE` ou `NEAR_MISS`) et le rôle de la personne qui l'a déclarée. *Source : `02_DATA_DICTIONARY/data_dictionary.csv` ; `03_SQL/schema_sources.sql`.*

## 2.3 Analyse des 5V

**Tableau 3. Les 5V appliqués au projet**

| V | Constat sur nos données | Conséquence pour le projet |
|---|---|---|
| **Volume** | 5 315 lignes, 260,5 ko | Volume faible : une base SQLite suffit pour l'analyse |
| **Vélocité** | Jeu statique, sans flux (hypothèse) | Traitement par lot : un run complet à chaque livraison de fichiers |
| **Variété** | 5 fichiers CSV structurés, 2 types d'événements, 3 référentiels | Un modèle relationnel, puis un schéma en étoile |
| **Véracité** | 0 valeur vide, 0 doublon, 0 clé orpheline ; 1 anomalie : `home_area` | 12 règles de qualité appliquées à chaque run |
| **Valeur** | 6 KPI demandés, reliés à des décisions HSE | Tables d'analyse (MART) et dashboard |

Le tableau 3 appelle cinq commentaires.

**Volume.** Le jeu est petit : 260,5 ko au total. Il ne justifie pas, à lui seul, des outils de données massives. Nous le disons clairement : le projet applique les méthodes du cours à un jeu d'enseignement. L'architecture est pensée pour un historique qui grandit d'année en année. *Source : fichiers de `01_DATA_RAW`.*

**Vélocité.** La vélocité est la vitesse à laquelle les données arrivent. Les fichiers fournis sont un jeu statique d'enseignement : aucune donnée n'arrive en continu. **Hypothèse du groupe :** dans un terminal réel, les incidents seraient livrés par lot. Notre politique prévoit un run complet après chaque livraison de nouvelles sources, et une alerte si le dernier événement a plus de 31 jours. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 5.*

**Variété.** Les cinq fichiers ont le même format et sont tous structurés. La variété est donc faible. Elle tient au contenu : deux sortes d'événements, qui n'ont pas les mêmes colonnes, et trois référentiels. C'est ce qui conduit à deux tables de faits (section 4). *Source : `02_DATA_DICTIONARY/data_dictionary.csv`.*

**Véracité.** La véracité est le degré de confiance que l'on peut accorder aux données. Les contrôles ne trouvent aucune valeur vide, aucun doublon d'identifiant et aucune clé orpheline. Une clé orpheline est une référence vers une ligne qui n'existe pas, par exemple un incident dans une zone inconnue. Une seule anomalie apparaît : la colonne `home_area` des engins contient des codes `Yxx` qui ne correspondent à aucune zone `LOCxxx`, pour les 40 engins. « Aucune erreur détectée » ne veut pas dire « données parfaites » : les contrôles ne vérifient que ce qu'ils savent tester. *Source : requêtes Q04, Q13 et Q14 de `03_SQL/starter_queries.sql` ; table `dq_results`, règles DQ02, DQ03, DQ07 et DQ11.*

**Valeur.** La valeur est ce que les données apportent à la décision. Elle vient des six KPI du sujet, auxquels le groupe a ajouté deux indicateurs (section 9). *Source : sujet, § 4 ; `10_EXPECTED_KPIS/kpi_catalog.csv`.*

## 2.4 Pourquoi cette analyse

Les 5V orientent les choix techniques. Un volume faible et un traitement par lot conduisent à un pipeline simple, relancé en entier. Une véracité à surveiller conduit à des règles de qualité automatiques. La valeur attendue conduit à des tables MART construites pour les questions du service HSE.

## 2.5 Limites et hypothèses

- Le dictionnaire fourni décrit les colonnes par un libellé court et un exemple. Il ne donne ni les horaires des équipes, ni les heures travaillées, ni la définition de la gravité. *Source : `02_DATA_DICTIONARY/data_dictionary.csv`.*
- La vélocité est une hypothèse, signalée ci-dessus : aucun fichier du dépôt ne décrit la fréquence réelle d'arrivée des données.
- Les deux fichiers d'événements n'ont aucune clé commune. On ne peut pas savoir si un near-miss noté dans les incidents est aussi noté dans les observations. *Source : `10_EXPECTED_KPIS/kpi_catalog.csv`, KPI4.*
