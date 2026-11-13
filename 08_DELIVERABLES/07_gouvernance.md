# 7. Qualité, gouvernance, sécurité et lineage

## 7.1 Objectif

La gouvernance des données fixe les règles du jeu : qui est responsable des données, qui peut les lire, comment on vérifie leur qualité et comment on retrouve l'origine d'un chiffre. Le sujet demande au moins six contrôles qualité, la documentation des rejets et de la réconciliation, le lineage, les accès, les données sensibles et le suivi. *Source : sujet, étape 6 et § 5.*

## 7.2 Ce que nous avons fait

**Les règles de qualité.** Nous avons défini 12 règles, nommées DQ01 à DQ12 (DQ pour « Data Quality »). Le pipeline les applique à chaque run et écrit le résultat dans la table `dq_results`.

**Tableau 15. Les 12 règles de qualité et leur résultat au dernier run**

| Règle | Ce qu'elle vérifie | Si elle échoue | Résultat |
|---|---|---|---|
| DQ01 | Chaque fichier contient au moins une ligne | Signalement | OK (5 tables) |
| DQ02 | Aucune valeur obligatoire n'est vide | Rejet de la ligne | OK, 0 rejet |
| DQ03 | Aucun doublon sur la clé | Rejet de la ligne | OK, 0 rejet |
| DQ04 | Les identifiants ont le bon format (ex. `LOC` + 3 chiffres) | Rejet de la ligne | OK, 0 rejet |
| DQ05 | Les dates sont valides, entre 2020 et la date du run | Rejet de la ligne | OK, 0 rejet |
| DQ06 | Les valeurs sont dans la liste autorisée (ex. 4 gravités) | Rejet de la ligne | OK, 0 rejet |
| DQ07 | Chaque clé étrangère existe dans son référentiel | Rejet de la ligne | OK, 0 rejet |
| DQ08 | Réconciliation : RAW = rejets + chargées | Blocage du run | OK, écart 0 (5 tables) |
| DQ09 | Fraîcheur : dernier événement âgé de 31 jours au plus | Alerte | OK (16 jours) |
| DQ10 | Variation entre deux mois complets : 25 % au plus | Alerte | **ALERTE** : mai +29,5 % |
| DQ11 | `home_area` des engins correspond à une zone | Alerte | **ALERTE** : 40 engins sur 40 |
| DQ12 | Les fichiers sources n'ont pas changé (empreinte MD5) | Alerte | OK |

Le tableau 15 distingue quatre réactions. Un rejet écarte une ligne fausse sans arrêter le pipeline. Un blocage arrête tout et conserve la base précédente. Une alerte laisse le run continuer et signale un point à examiner. Un signalement est une simple mention dans `dq_results`. Au dernier run, 10 règles sur 12 sont OK et 2 sont en alerte. Le sujet demandait 6 contrôles : nous en appliquons 12, dont DQ12, ajoutée par le groupe. *Source : `06_GOVERNANCE/data_quality_rules.csv` ; table `dq_results` (39 contrôles).*

**Les deux alertes.** DQ10 signale que mai compte 171 incidents, contre 132 en avril, soit +29,5 %. Ce n'est pas une erreur de données : c'est un signal métier, que le service HSE doit analyser (section 8). DQ11 signale que les codes `home_area` des engins (`Yxx`) ne correspondent à aucune zone (`LOCxxx`). C'est une limite des données sources, déjà notée dans l'hypothèse H4. *Source : table `dq_results` ; `04_ETL/dwh_conception.md`, § 5.*

**Les rejets.** Les données fournies ne produisent aucun rejet. Le test d'anomalies (section 5) prouve que les règles DQ02 à DQ07 détectent bien les erreurs : 11 anomalies injectées, 11 rejets tracés. *Source : `04_ETL/test_etl.py`, test 2.*

**Les propriétaires.** Le propriétaire métier est le service HSE : il définit ce qu'est un incident grave, valide les KPI et décide des actions. Le propriétaire technique est le data engineer, rôle tenu par le groupe : il exploite le pipeline, applique les règles et gère les accès. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 1.*

**La classification.** Chaque donnée reçoit un niveau de sensibilité.

**Tableau 16. Classification des données**

| Donnée | Niveau | Raison |
|---|---|---|
| Fichiers sources, couches RAW, STAGING et CORE | Confidentiel | Contiennent `worker_id`, l'identifiant d'un travailleur |
| Couche MART, tables de suivi | Interne | Agrégats et volumes seulement, aucun `worker_id` |
| Rapport, présentation, captures du dashboard | Public | Agrégats seulement, à relire avant diffusion |

Le tableau 16 repose sur une seule colonne sensible : `worker_id`. Elle est synthétique, mais nous la traitons comme un identifiant réel. Elle reste dans les couches confidentielles et n'apparaît dans aucune table MART. La table `stg_rejects` est aussi confidentielle : elle garde la ligne source complète. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 2 et § 4.*

**Les accès.** Nous appliquons le principe du moindre privilège : chaque rôle ne lit que ce dont il a besoin.

**Tableau 17. Matrice d'accès (R = lecture, W = écriture, — = aucun accès)**

| Rôle | RAW et STAGING | CORE | MART | Suivi |
|---|---|---|---|---|
| Data engineer | R W | R W | R W | R W |
| Responsable HSE | — | — | R | R |
| Analyste (notebook EDA) | — | — | R | R |
| Dashboard | — | — | R | R |
| Auditeur qualité | R (`stg_rejects` seulement) | — | R | R |

Le tableau 17 montre que seul le data engineer accède aux couches confidentielles. L'analyse et le dashboard lisent uniquement les tables MART et le suivi : ils n'ont jamais besoin de connaître un travailleur. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 3 ; `07_EDA/eda_projet11.ipynb` ; `12_DASHBOARD/app.py`.*

**Les petits groupes.** Le taux d'incidents est publié par groupe « rôle × équipe ». Les 12 groupes comptent de 21 à 41 travailleurs. Un groupe trop petit permettrait de deviner une personne : la politique fixe une taille minimale de 20. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 4 ; `mart_incident_rate_shift_role`.*

**Le lineage.** Le lineage est le chemin suivi par une donnée, de la source au chiffre affiché. Le fichier `lineage.csv` décrit 36 liens : pour chacun, la source, la cible, la transformation et les règles appliquées.

**Tableau 18. Exemple de lineage : d'où vient le KPI « 759 near-miss »**

| Étape | Objet | Ce qui se passe |
|---|---|---|
| 1 | `incidents.csv`, `safety_observations.csv` | Fichiers sources |
| 2 | `raw_incidents`, `raw_safety_observations` | Copie fidèle (liens L04, L05) |
| 3 | `stg_incidents`, `stg_safety_observations` | Nettoyage et contrôles (L10, L11) |
| 4 | `fact_incident`, `fact_safety_observation` | Mesure `is_near_miss` (L22, L23) |
| 5 | `mart_near_miss` | Somme par mois : 225 + 534 (L27) |
| 6 | `mart_kpi_summary` | KPI4 = 759 (L30) |

Le tableau 18 se lit dans les deux sens. De haut en bas, il décrit la fabrication du chiffre. De bas en haut, il sert au diagnostic : si le KPI paraît faux, on compare le nombre de lignes à chaque étape et on trouve la couche où l'erreur apparaît. *Source : `06_GOVERNANCE/lineage.csv`.*

**Le dictionnaire enrichi.** Le dictionnaire fourni décrivait 21 colonnes sources. Notre version enrichie décrit 148 colonnes, de la source aux tables de suivi, avec pour chacune la classification et les règles de qualité. *Source : `02_DATA_DICTIONARY/data_dictionary.csv` ; `06_GOVERNANCE/data_dictionary_enrichi.csv`.*

## 7.3 Pourquoi ces choix

Les incidents concernent des personnes. Le service HSE a besoin de savoir quels groupes former, pas quel individu a eu un incident. Publier seulement des agrégats répond à ce besoin et protège les travailleurs. Les règles de qualité, elles, protègent la décision : un total faux orienterait les rondes vers la mauvaise zone. Le blocage de DQ08 garantit qu'un chiffre publié repose sur toutes les lignes reçues.

## 7.4 Résultat

Le suivi se lit à trois endroits : `dq_results` (une ligne par règle et par table), `etl_run_log` (une ligne par run) et `stg_rejects` (les lignes refusées). L'onglet « Qualité des données » du dashboard affiche ces informations : règles OK, rejets, alertes et dernier run. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 7 ; `12_DASHBOARD/app.py`.*

## 7.5 Limites et hypothèses

- **Accès non appliqués techniquement.** SQLite ne gère pas les droits par utilisateur. La matrice d'accès est une politique écrite. En production, elle serait appliquée par des rôles et des droits dans la base. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 3 et § 8.*
- **Seuils.** Les seuils de 31 jours (fraîcheur) et de 25 % (variation) sont des hypothèses du groupe, à valider par le service HSE. La fraîcheur passera en alerte à partir du 29 novembre 2026 : c'est normal pour un historique figé. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 5.*
- **DQ01 non bloquante.** Un fichier vide est signalé mais n'arrête pas le pipeline dans le code actuel. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 6.*
- **Données réelles.** Avec des données réelles, il faudrait ajouter la pseudonymisation de `worker_id`, une durée de conservation et un registre des traitements (RGPD). *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 8.*
