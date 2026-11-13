# 5. ETL : des sources aux tables d'analyse

## 5.1 Objectif

Un ETL (Extract, Transform, Load) est un programme qui lit les sources, les contrôle, les transforme et les charge dans le Data Warehouse. Notre ETL est un seul script Python, appelé « le pipeline ». Il fait passer les données par quatre couches : RAW, STAGING, CORE et MART. Le sujet demande aussi des rejets expliqués et une réconciliation des volumes. *Source : sujet, étape 4 ; `04_ETL/README_ETL.md`.*

## 5.2 Ce que nous avons fait

Le pipeline se lance par une commande : `python 04_ETL/etl_pipeline.py`. Il construit la base `project_11_dwh.db` en 1,48 seconde (dernier run enregistré). *Source : `README.md` ; table `etl_run_log`.*

**Tableau 10. Les quatre couches du pipeline et leurs volumes**

| Couche | Rôle | Tables | Lignes |
|---|---|---|---|
| RAW | Copie fidèle des fichiers, tout en texte, sans correction | 5 tables `raw_*` et `raw_manifest` | 5 315 |
| STAGING | Données nettoyées et contrôlées ; lignes refusées à part | 5 tables `stg_*` et `stg_rejects` | 5 315 valides, 0 rejet |
| CORE | Schéma en étoile (section 4) | 9 dimensions, 2 faits | 4 900 faits |
| MART | Tables agrégées, prêtes pour l'analyse | 7 tables `mart_*` | 75 |

Le tableau 10 se lit de haut en bas. Les 5 315 lignes sources entrent en RAW. Toutes passent les contrôles. Les 4 900 événements (1 400 incidents et 3 500 observations) deviennent des faits. Les 415 autres lignes sont les référentiels (25 zones, 350 travailleurs, 40 engins) : elles deviennent des dimensions. *Source : tables `etl_run_log` et `dq_results`.*

**Couche RAW.** Chaque fichier est chargé tel quel, en texte. Le pipeline ajoute trois colonnes de traçabilité : le nom du fichier, le numéro de la ligne et l'identifiant du run (`_run_id`). Un run est une exécution complète du pipeline. Le pipeline enregistre aussi une empreinte MD5 de chaque fichier. Une empreinte MD5 est un code de 32 caractères calculé à partir du contenu : si un seul caractère du fichier change, le code change. Exemple : `incidents.csv` a l'empreinte `8f6bf245…`. *Source : `04_ETL/etl_pipeline.py`, étape 5.1 ; table `raw_manifest`.*

**Couche STAGING.** Le pipeline standardise d'abord les valeurs : il supprime les espaces et met en majuscules. Exemple testé : la valeur `'  spill '` devient `SPILL` et n'est pas rejetée. Il applique ensuite six règles de qualité, DQ02 à DQ07 (détail en section 7). Une ligne qui échoue est un rejet : elle n'entre pas dans le DWH. Elle est écrite dans `stg_rejects` avec la règle, la raison et la ligne d'origine. *Source : `04_ETL/etl_pipeline.py`, étape 5.2 ; `04_ETL/test_etl.py`, test 2.*

**Couche CORE.** Le pipeline crée les 9 dimensions, puis les 2 tables de faits. Dans les faits, chaque texte est remplacé par la clé de substitution de sa dimension. *Source : `04_ETL/etl_pipeline.py`, étapes 5.3 et 5.4.*

**Couche MART.** Une table MART est un résultat déjà calculé, que l'utilisateur lit sans écrire de jointure. Exemple : `mart_incidents_month` contient 10 lignes, une par mois.

**Tableau 11. Les 7 tables MART**

| Table MART | Une ligne représente | Lignes | Question HSE |
|---|---|---|---|
| `mart_incidents_month` | 1 mois | 10 | Quand ? |
| `mart_severity_distribution` | 1 niveau de gravité | 4 | Comment ? |
| `mart_incidents_by_area` | 1 zone | 25 | Où ? |
| `mart_near_miss` | 1 mois | 10 | Signaux faibles |
| `mart_recurring_incident_type` | 1 type d'incident | 6 | Comment ? |
| `mart_incident_rate_shift_role` | 1 groupe rôle × équipe | 12 | À qui ? |
| `mart_kpi_summary` | 1 KPI | 8 | Synthèse |

Le tableau 11 relie chaque table à une question du service HSE. Les six premières tables correspondent aux six KPI du sujet. La dernière rassemble les 8 chiffres clés (section 9). Aucune table MART ne contient d'identifiant de travailleur : le pipeline le vérifie à chaque run et s'arrête sinon. *Source : `04_ETL/etl_pipeline.py`, étapes 5.5 et 5.6 ; `README.md`.*

**Mois complets.** Les données s'arrêtent le 28 octobre 2026. Octobre ne couvre que 28 jours sur 31. Le pipeline compare, pour chaque mois, les jours couverts aux jours du mois, et marque octobre comme incomplet (`mois_complet = 0`). La moyenne mensuelle ne porte que sur les 9 mois complets : 1 296 incidents ÷ 9 = 144,0. Avec octobre, on obtiendrait 140,0, un chiffre trop bas. *Source : `mart_incidents_month` ; `10_EXPECTED_KPIS/kpi_catalog.csv`, KPI1.*

**Réconciliation.** La réconciliation vérifie qu'aucune ligne n'a été perdue ou créée entre deux couches. La règle est : lignes RAW = lignes rejetées + lignes chargées. Exemple : pour les incidents, 1 400 = 0 + 1 400. Le pipeline fait ce contrôle (DQ08) pour les 5 tables. Un écart, même d'une ligne, arrête le run. *Source : table `dq_results`, règle DQ08.*

**Suivi (monitoring).** Chaque run écrit une ligne dans `etl_run_log` : date, durée, volumes, nombre d'alertes, statut. Chaque contrôle écrit une ligne dans `dq_results`. *Source : `04_ETL/etl_pipeline.py`, étape 5.7.*

## 5.3 Pourquoi ces choix

Le service HSE décide à partir de chiffres : il doit pouvoir leur faire confiance. Trois propriétés y répondent.

**L'idempotence.** Un traitement est idempotent s'il donne le même résultat quand on le relance. Exemple : deux runs de suite produisent deux fois 1 400 incidents, et non 2 800. Le pipeline reconstruit toute la base à chaque run. *Source : `04_ETL/test_etl.py`, test 1.*

**Le rollback.** Un rollback est un retour à l'état précédent en cas d'erreur. Le pipeline construit la nouvelle base dans un fichier temporaire. Il ne remplace l'ancienne base qu'à la fin, si tous les contrôles bloquants passent. En cas de panne, l'ancienne base reste en place et l'échec est noté dans `etl_run_log`. Le service HSE ne lit donc jamais une base à moitié construite. *Source : `04_ETL/etl_pipeline.py`, étape 5.8.*

**Le rejet ligne par ligne.** Une ligne fausse ne bloque pas les autres. Elle est mise de côté avec sa raison, pour que la source soit corrigée. *Source : `04_ETL/etl_pipeline.py`, étape 5.2.*

Garder la couche RAW sans correction a aussi une raison : on peut toujours comparer ce qui a été reçu et ce qui a été chargé.

## 5.4 Résultat

Sur les données fournies, le dernier run se termine avec le statut SUCCES : 5 315 lignes lues, 0 rejet, 4 900 faits, 75 lignes MART, 2 alertes et 0 échec. Les deux alertes sont expliquées en section 7. *Source : table `etl_run_log`.*

Les données fournies sont propres : elles ne produisent aucun rejet. Pour prouver que les contrôles fonctionnent, le script `04_ETL/test_etl.py` exécute le pipeline sur des copies modifiées des données.

**Tableau 12. Les trois tests du pipeline**

| Test | Ce qu'il fait | Résultat obtenu |
|---|---|---|
| 1. Idempotence | Lance 2 runs et compare l'empreinte SHA-256 du contenu des deux bases | Même empreinte ; 2 runs dans le journal |
| 2. Anomalies | Injecte 11 anomalies dans les sources (date invalide, doublon, clé inconnue…) | 11 rejets, chacun avec sa raison ; réconciliation correcte : 1 401 = 9 + 1 392 pour les incidents |
| 3. Panne | Provoque une erreur au milieu d'un run | Base précédente intacte ; fichier temporaire supprimé ; journal : SUCCES puis ECHEC |

Le tableau 12 montre que les trois propriétés annoncées sont vérifiées par l'exécution, et non seulement affirmées. Dans le test 2, les 11 rejets se répartissent ainsi : valeur absente (1), doublon (1), format (1), date (3), valeur non autorisée (2), clé étrangère (3). Nous avons relancé ces tests le 13 novembre 2026 : tous passent. *Source : sortie de `python 04_ETL/test_etl.py`.*

## 5.5 Limites et hypothèses

- **Chargement complet.** Le pipeline recharge tout à chaque run. C'est simple et sûr pour 5 315 lignes. Pour un volume beaucoup plus grand, il faudrait un chargement incrémental (ne charger que les nouveautés). *Déduction du groupe.*
- **Rollback par fichier.** Le retour arrière repose sur le remplacement d'un fichier, et non sur une transaction de la base. *Source : `04_ETL/etl_pipeline.py`, étape 5.8.*
- **Chiffres de référence.** Le pipeline compare aussi ses résultats aux chiffres attendus (144,0 ; 22,3 % ; 759). Ces contrôles sont informatifs et ne bloquent pas : des rejets légitimes peuvent changer ces chiffres. *Source : `04_ETL/etl_pipeline.py`, étape 5.5.*
- **Seuils.** Les seuils de fraîcheur (31 jours) et de variation mensuelle (25 %) sont des hypothèses du groupe. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 5.*
