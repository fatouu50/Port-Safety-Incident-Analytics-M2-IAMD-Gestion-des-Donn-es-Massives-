# 3. Modèle relationnel et requêtes SQL

## 3.1 Objectif

Avant de construire le Data Warehouse, nous avons chargé les cinq fichiers dans une base relationnelle. Une base relationnelle range les données dans des tables reliées entre elles par des clés. L'objectif est double : vérifier que les fichiers sont cohérents entre eux, et calculer une première fois les KPI en SQL, le langage d'interrogation des bases. *Source : sujet, étape 2.*

## 3.2 Ce que nous avons fait

**La base source.** Le script `build_source_db.py` crée la base `project_11_sources.db` (SQLite) à partir du schéma `schema_sources.sql`, puis y charge les cinq fichiers. On peut le relancer : la base est reconstruite à l'identique. *Source : `03_SQL/build_source_db.py`.*

**Tableau 4. Le modèle relationnel source**

| Table | Lignes | Clé primaire | Clés étrangères | Valeurs contrôlées (CHECK) |
|---|---|---|---|---|
| `locations` | 25 | `location_id` | — | 5 types de zone |
| `workers_synthetic` | 350 | `worker_id` | — | 4 rôles, 3 équipes |
| `equipment` | 40 | `equipment_id` | — | 5 types d'engin |
| `incidents` | 1 400 | `incident_id` | zone, engin, travailleur | 4 gravités, 6 types |
| `safety_observations` | 3 500 | `observation_id` | zone | 3 types, 3 rôles de déclarant |

Le tableau 4 décrit trois sortes de règles. La clé primaire identifie chaque ligne : deux incidents ne peuvent pas porter le même `incident_id`. La clé étrangère relie deux tables : un incident ne peut citer qu'une zone qui existe dans `locations`. La contrainte CHECK limite les valeurs : la gravité ne peut être que `LOW`, `MEDIUM`, `HIGH` ou `CRITICAL`. La base refuse toute ligne qui enfreint une de ces règles. Au chargement, les 5 315 lignes sont acceptées et la vérification des clés étrangères ne signale aucune erreur. *Source : `03_SQL/schema_sources.sql` ; sortie de `python 03_SQL/build_source_db.py`.*

Le schéma crée aussi cinq index, sur les colonnes de zone, de travailleur et de date. Un index est une table des matières qui évite de lire toute la table. *Source : `03_SQL/schema_sources.sql`.*

**Les requêtes.** Le fichier `starter_queries.sql` contient 15 requêtes numérotées, de Q01 à Q15, avec 4 variantes.

**Tableau 5. Les requêtes SQL, par technique**

| Technique demandée | Requêtes | Exemple de résultat |
|---|---|---|
| Volumes et période | Q01, Q01 bis | 5 315 lignes ; du 1er janvier au 28 octobre 2026 |
| Jointures (3 demandées) | Q02, Q03, Q04 | Q02 bis : 1 400 lignes avant et après la jointure |
| Agrégations (GROUP BY) | Q05 à Q08 | Q05 bis : 144,0 incidents par mois complet |
| Sous-requête | Q09 | 13 zones au-dessus de la moyenne d'incidents par zone |
| CTE et fonctions de fenêtre | Q10, Q11, Q12 | Q11 : mai, +29,5 % par rapport à avril |
| Unicité et grain | Q13, Q14 | 0 doublon d'identifiant, 0 doublon métier |
| Plan d'exécution | Q15, Q15 bis | Index utilisé pour la zone ; lecture complète pour l'engin |

Le tableau 5 montre que chaque technique du sujet est couverte. Une jointure assemble deux tables par leur clé. Une agrégation regroupe des lignes pour compter. Une CTE (expression de table commune) est une requête intermédiaire à laquelle on donne un nom, pour découper un calcul en étapes lisibles. *Source : `03_SQL/starter_queries.sql` ; résultats obtenus en exécutant le fichier sur `project_11_sources.db`.*

## 3.3 Pourquoi ces choix

Les contraintes du schéma servent le besoin de fiabilité du service HSE : une erreur de saisie est refusée dès l'entrée, avant tout calcul.

Trois requêtes sont des contrôles, et non des analyses. Q02 bis vérifie qu'une jointure ne multiplie pas les lignes : un incident compté deux fois fausserait tous les KPI. Q04 cherche les clés orphelines : elle en trouve 0 sur les quatre liens testés. Q13 vérifie que chaque identifiant est unique : c'est la condition pour choisir le grain « une ligne par incident » du Data Warehouse (section 4). *Source : `03_SQL/starter_queries.sql`, Q02 bis, Q04, Q13.*

Le SQL calcule aussi les KPI une première fois, directement sur les sources. Le Data Warehouse doit ensuite retrouver les mêmes chiffres : c'est une vérification croisée.

## 3.4 Résultat

Les KPI calculés en SQL sont : 144,0 incidents par mois complet (Q05 bis), 22,3 % d'incidents graves (Q06 : 17,1 % `HIGH` et 5,2 % `CRITICAL`), 759 near-miss (Q07 : 225 dans les incidents et 534 dans les observations), et 4,84 incidents par travailleur pour les opérateurs de l'équipe A (Q08). Ces chiffres sont identiques à ceux de la table `mart_kpi_summary` du Data Warehouse. *Source : résultats de `03_SQL/starter_queries.sql` ; `mart_kpi_summary`.*

**Tableau 6. Incidents et part d'incidents graves par type de zone (requête Q03)**

| Type de zone | Zones | Incidents | Incidents graves | Part de graves |
|---|---|---|---|---|
| BERTH (quai) | 9 | 472 | 104 | 22,0 % |
| GATE (porte) | 5 | 290 | 53 | 18,3 % |
| RAIL (voie ferrée) | 5 | 282 | 70 | 24,8 % |
| YARD (parc à conteneurs) | 3 | 182 | 51 | 28,0 % |
| WORKSHOP (atelier) | 3 | 174 | 34 | 19,5 % |

Le tableau 6 distingue le volume et la gravité. Les quais comptent le plus d'incidents (472), mais ils regroupent aussi le plus de zones (9). Le parc à conteneurs compte peu d'incidents (182) mais la plus forte part d'incidents graves : 28,0 %, contre 22,3 % en moyenne. Pour le service HSE, le parc est donc la zone où un incident a le plus de chances d'être grave. *Source : requête Q03 ; nombre de zones par type dans `mart_incidents_by_area`.*

La requête Q10 cherche le type d'incident le plus fréquent dans chaque type de zone. `SPILL` (déversement) arrive en tête sur les quais, le rail et l'atelier ; il est à égalité avec `NEAR_MISS` aux portes ; au parc, c'est `FALL` (chute) qui domine, avec 19,8 %. *Source : requête Q10.*

La requête Q15 compare deux plans d'exécution. Pour un filtre sur la zone, SQLite utilise l'index `idx_inc_location`. Pour un filtre sur l'engin, sans index, il lit toute la table. Sur 1 400 lignes, la différence de temps est invisible ; elle compterait sur un historique de plusieurs années. *Source : requêtes Q15 et Q15 bis ; la remarque sur le temps est une déduction du groupe.*

## 3.5 Limites et hypothèses

- La colonne `home_area` des engins n'a pas de clé étrangère : ses codes ne correspondent à aucune zone. *Source : `03_SQL/schema_sources.sql`.*
- La requête Q05 bis exclut octobre par une date écrite en dur (`mois < '2026-10'`). Le Data Warehouse calcule la même exclusion de façon générale, en comparant les jours couverts aux jours du mois. *Source : `03_SQL/starter_queries.sql` ; `04_ETL/etl_pipeline.py`.*
- Le taux de Q08 divise par le nombre de travailleurs, faute d'heures travaillées dans les sources. *Source : `03_SQL/starter_queries.sql`, Q08.*
- [À COMPLÉTER : relecture de cette section par Fatouma, auteure du SQL]
