# Gouvernance / Sécurité

Projet 11 : Port Safety & Incident Analytics.
Toutes les données sont synthétiques : aucune donnée personnelle réelle n'est utilisée.
Ce document est la politique du projet. Les règles qualité sont dans
`data_quality_rules.csv`, le lineage dans `lineage.csv` et le dictionnaire enrichi
dans `data_dictionary_enrichi.csv` (étapes 7.2 et 7.3).

## 1. Propriétaires

| Rôle | Qui | Responsabilités |
|---|---|---|
| **Propriétaire métier** | Service HSE (responsable HSE) | Définit ce qu'est un incident « grave » et un near-miss, valide les KPI et les seuils métier, décide des actions à partir des résultats. |
| **Propriétaire technique** | Data engineer (équipe projet) | Construit et exploite le pipeline, applique les règles qualité, gère les accès, tient le journal des runs. |

Dans le projet, le rôle de propriétaire technique est tenu par le groupe (Mako : DWH, ETL, gouvernance ;
Fatouma : SQL, HDFS, EDA).

## 2. Classification des données

Niveaux : **public**, **interne**, **confidentiel**.

| Donnée | Niveau | Pourquoi |
|---|---|---|
| Fichiers sources `01_DATA_RAW/*.csv` | Confidentiel | Contiennent des identifiants individuels (`worker_id`), même synthétiques. |
| Couche RAW (`raw_*`, `raw_manifest`) | Confidentiel | Copie fidèle des sources. |
| Couche STAGING (`stg_*`, `stg_rejects`) | Confidentiel | `stg_rejects` garde la ligne source complète (avec `worker_id`). |
| Couche CORE (`dim_*`, `fact_*`) | Confidentiel | `dim_worker` et `fact_incident.worker_key` permettent de suivre un individu. `dim_worker` est la table la plus sensible. |
| Couche MART (`mart_*`) | Interne | Agrégats uniquement, aucun `worker_id`. |
| Suivi (`dq_results`, `etl_run_log`) | Interne | Volumes et statuts, aucune donnée individuelle. |
| Archive HDFS : `raw/` et `reference/` | Confidentiel | Copie des sources. |
| Archive HDFS : MART en Parquet | Interne | Agrégats. |
| Rapport, présentation, captures du dashboard | Public | Ne contiennent que des agrégats (à relire avant diffusion). |

## 3. Matrice d'accès (moindre privilège)

R = lecture, W = écriture, « — » = aucun accès. Chaque rôle n'a que ce dont il a besoin.

| Rôle | RAW / STAGING | CORE | MART | Suivi (`dq_results`, `etl_run_log`) | Archive HDFS `raw/` |
|---|---|---|---|---|---|
| Data engineer | R W | R W | R W | R W | R W |
| Responsable HSE | — | — | R | R | — |
| Analyste EDA (notebook) | — | — | R | R | — |
| Dashboard (compte de service) | — | — | R | R | — |
| Auditeur qualité | R (`stg_rejects` seulement) | — | R | R | — |

Remarques :
- L'EDA et le dashboard lisent **uniquement les MART** (ils n'ont jamais besoin d'un identifiant de travailleur).
- Limite : SQLite ne gère pas les droits par utilisateur. Cette matrice est une politique ;
  dans un environnement de production, on l'appliquerait avec des rôles et des `GRANT`
  (base relationnelle) et des ACL (HDFS).

## 4. Données sensibles et protection

- **Identifiants individuels** : seul `worker_id` (synthétique, pseudonyme) en est un.
  Il reste dans RAW, STAGING et CORE (confidentiels) et n'apparaît dans **aucune** MART.
  Le pipeline le vérifie à chaque run (contrôle « Aucun worker_id dans les MART », bloquant).
- **Petits groupes** : le taux par rôle et équipe est publié par groupe de 21 à 41 travailleurs
  (12 groupes), jamais pour une personne seule. Un groupe trop petit permettrait de deviner
  un individu : on garde une taille minimale de 20.
- **Rejets** : `stg_rejects` conserve la ligne brute pour pouvoir corriger la source, donc elle est
  classée confidentielle.
- **Traçabilité** : chaque ligne RAW porte `_source_file`, `_row_num` et `_run_id`. Le manifeste MD5
  prouve quelle version de chaque fichier a été chargée.

## 5. SLA, fraîcheur et seuils d'alerte

Seuils = hypothèses du groupe, à valider avec le propriétaire métier.

| Sujet | Engagement / seuil | Règle | Si dépassé |
|---|---|---|---|
| Fraîcheur des données | Dernier événement âgé de 31 jours au plus | DQ09 | ALERTE |
| Rafraîchissement | Un run complet après chaque livraison de nouvelles sources | — | — |
| Durée d'un run | Quelques secondes (environ 1 à 2 s mesurées sur le jeu actuel) | `etl_run_log.duree_s` | À surveiller |
| Réconciliation des volumes | Écart de 0 ligne (RAW = rejets + CORE) | DQ08 | BLOCAGE : le run échoue et rien n'est publié |
| Variation mensuelle | 25 % maximum entre deux mois complets | DQ10 | ALERTE (le signal est analysé par le HSE) |
| Sources modifiées | Aucun fichier modifié sans le savoir | DQ12 | ALERTE |
| Rejets | Tout rejet est tracé avec sa raison | DQ02 à DQ07 | Le propriétaire technique examine `stg_rejects` |
| Disponibilité de la dernière bonne base | Une panne ne remplace jamais la base précédente | Base temporaire et rollback | `etl_run_log` : statut ECHEC |

Le jeu actuel s'arrête au 28 octobre : la fraîcheur est OK à la date de la soutenance (16/11) et passera en
ALERTE à partir du 29 novembre 2026, ce qui est normal pour un historique figé.

## 6. Règles qualité (résumé)

12 règles (DQ01 à DQ12), détaillées dans `data_quality_rules.csv` (une ligne par règle et par table).

| Action en cas d'échec | Règles | Effet |
|---|---|---|
| REJET_LIGNE | DQ02, DQ03, DQ04, DQ05, DQ06, DQ07 | La ligne est écrite dans `stg_rejects` avec sa raison et n'entre pas dans le DWH. |
| BLOCAGE | DQ08 (et les contrôles de structure des faits et des MART) | Le run s'arrête, la base précédente est conservée. |
| ALERTE | DQ09, DQ10, DQ11, DQ12 | Signalée dans `dq_results`, le run continue. |
| SIGNALEMENT | DQ01 | Signalé dans `dq_results` (non bloquant dans le code actuel). |

## 7. Où suivre la qualité

- `dq_results` : une ligne par règle et par table, avec le statut (OK, REJETS, ALERTE, ECHEC) et le détail.
- `etl_run_log` : une ligne par run (date, durée, volumes, statut SUCCES ou ECHEC, message d'erreur).
- `stg_rejects` : les lignes refusées et leurs raisons.
- Tests : `python 04_ETL/test_etl.py` (idempotence, 11 rejets tracés, panne et rollback).

## 8. Hypothèses et limites

- Les seuils de fraîcheur (31 jours) et de variation (25 %) sont des choix du groupe.
- **DQ12** (intégrité des sources) est une règle ajoutée par le groupe : le sujet n'en demande que DQ01 à DQ11.
- Pas d'heures travaillées dans les sources : le taux par rôle et équipe est calculé par effectif.
- Les droits d'accès sont une politique documentée, non appliquée techniquement (SQLite).
- Aucune donnée personnelle réelle : si le projet passait sur des données réelles, il faudrait ajouter
  la pseudonymisation de `worker_id`, une durée de conservation et un registre des traitements (RGPD).
