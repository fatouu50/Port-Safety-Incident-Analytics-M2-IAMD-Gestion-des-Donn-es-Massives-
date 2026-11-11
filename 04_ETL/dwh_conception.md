# Projet 11 : conception du Data Warehouse

Modèle dimensionnel (schéma en étoile) alimenté par `etl_pipeline.py`.
Chaîne : Sources → RAW → STAGING → **CORE (ce document)** → MART.

## 1. Grain

| Table de faits | 1 ligne = | Clé métier |
|---|---|---|
| `fact_incident` | 1 incident | `incident_id` (1 400 lignes) |
| `fact_safety_observation` | 1 observation de sécurité | `observation_id` (3 500 lignes) |

Les deux faits ont un grain différent : on ne les mélange pas dans une même table.
Ils se rejoignent uniquement par les dimensions communes (date, heure, zone).

## 2. Dimensions (9)

Chaque dimension a une clé de substitution entière (`*_key`), générée par l'ETL.
La clé métier d'origine est conservée à côté pour la traçabilité.

| Dimension | Clé de substitution | Contenu | Utilisée par |
|---|---|---|---|
| `dim_date` | `date_key` (AAAAMMJJ) | date, année, mois, jour, nom du mois, jours dans le mois | les 2 faits |
| `dim_hour` | `hour_key` (0-23) | heure, tranche horaire (voir ci-dessous) | les 2 faits |
| `dim_location` | `location_key` | `location_id`, `area_type`, `area_name` | les 2 faits |
| `dim_equipment` | `equipment_key` | `equipment_id`, `equipment_type`, `home_area` | `fact_incident` |
| `dim_worker` | `worker_key` | `worker_id` (synthétique), `role`, `shift` | `fact_incident` |
| `dim_incident_type` | `incident_type_key` | COLLISION, EQUIPMENT, FALL, NEAR_MISS, PPE, SPILL | `fact_incident` |
| `dim_severity` | `severity_key` | LOW, MEDIUM, HIGH, CRITICAL, poids, `is_serious` | `fact_incident` |
| `dim_observation_type` | `observation_type_key` | SAFE, UNSAFE, NEAR_MISS | `fact_safety_observation` |
| `dim_reporter_role` | `reporter_role_key` | OPERATOR, SUPERVISOR, HSE | `fact_safety_observation` |

Tranches de `dim_hour` (heure de début incluse, heure de fin exclue) :

| Tranche | Heures (`hour_key`) | Plage |
|---|---|---|
| NUIT | 0, 1, 2, 3, 4, 5 | 00:00 à 05:59 |
| MATIN | 6, 7, 8, 9, 10, 11 | 06:00 à 11:59 |
| APRES_MIDI | 12, 13, 14, 15, 16, 17 | 12:00 à 17:59 |
| SOIR | 18, 19, 20, 21, 22, 23 | 18:00 à 23:59 |

Remarques :
- `home_area` (Y01…) ne correspond à aucune `location_id` (LOCxxx) : on la garde
  comme simple attribut de l'engin, sans jointure (alerte DQ11).
  **Limite :** on ne peut pas dire dans quelle zone « habite » un engin, ni comparer
  la zone de rattachement avec la zone de l'incident.
- `dim_worker` contient `worker_id` : table CONFIDENTIELLE, jamais exposée dans les MART.
- `role` (travailleur) et `reported_by_role` (déclarant) sont deux notions différentes :
  deux dimensions séparées.

## 3. Tables de faits et mesures

### `fact_incident` (grain : 1 incident)

| Colonne | Type | Rôle |
|---|---|---|
| `incident_id` | texte | clé métier (dimension dégénérée) |
| `date_key`, `hour_key` | entier | quand |
| `location_key` | entier | où |
| `equipment_key` | entier | avec quel engin |
| `worker_key` | entier | qui |
| `incident_type_key`, `severity_key` | entier | quoi, gravité |
| `incident_count` | entier | toujours 1 (permet de faire des SUM) |
| `is_serious` | 0/1 | 1 si gravité HIGH ou CRITICAL |
| `is_near_miss` | 0/1 | 1 si type NEAR_MISS |
| `severity_weight` | entier | LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4 (proposition) |

### `fact_safety_observation` (grain : 1 observation)

| Colonne | Type | Rôle |
|---|---|---|
| `observation_id` | entier | clé métier (dimension dégénérée) |
| `date_key`, `hour_key` | entier | quand |
| `location_key` | entier | où |
| `observation_type_key` | entier | SAFE / UNSAFE / NEAR_MISS |
| `reporter_role_key` | entier | qui a déclaré |
| `observation_count` | entier | toujours 1 |
| `is_unsafe` | 0/1 | 1 si UNSAFE |
| `is_near_miss` | 0/1 | 1 si NEAR_MISS |

Near-miss (décision validée) : 225 dans `fact_incident` + 534 dans `fact_safety_observation` = 759.

## 4. Schéma en étoile

Trois dimensions sont communes aux deux faits : `dim_date`, `dim_hour`, `dim_location`.
Les autres sont propres à un seul fait. Une étoile par fait :

```
fact_incident
  ├── date_key           → dim_date
  ├── hour_key           → dim_hour
  ├── location_key       → dim_location
  ├── equipment_key      → dim_equipment
  ├── worker_key         → dim_worker
  ├── incident_type_key  → dim_incident_type
  └── severity_key       → dim_severity

fact_safety_observation
  ├── date_key             → dim_date
  ├── hour_key             → dim_hour
  ├── location_key         → dim_location
  ├── observation_type_key → dim_observation_type
  └── reporter_role_key    → dim_reporter_role
```

## 5. Hypothèses du groupe (non fournies par le sujet)

| N° | Hypothèse | Pourquoi | Impact |
|---|---|---|---|
| H1 | `severity_weight` : LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4 | Le dictionnaire de données du prof donne seulement « Sévérité » (exemple LOW), aucun poids. Échelle ordinale simple. | Mesure de pondération, non utilisée dans les 7 MART validées. |
| H2 | Incident « grave » = gravité HIGH ou CRITICAL (`is_serious`) | Le sujet ne définit pas « grave ». | Base du KPI2 (22,3 %) et du score de risque. |
| H3 | Tranches de `dim_hour` : 4 blocs de 6 h (NUIT, MATIN, APRES_MIDI, SOIR) | Les horaires des équipes A, B et C ne sont pas fournis. | Les tranches ne remplacent pas l'équipe (shift) : l'équipe vient du travailleur. |
| H4 | `home_area` conservée sans jointure | Les codes Yxx ne correspondent à aucune zone LOCxxx. | Aucune analyse « zone de rattachement » possible. |

## 6. Choix à retenir pour le rapport

- **Pourquoi deux faits ?** Un incident et une observation n'ont ni le même grain
  ni les mêmes dimensions. Les mélanger créerait des colonnes vides et des erreurs de comptage.
- **Pourquoi des clés de substitution ?** Elles isolent le DWH des identifiants sources
  (qui peuvent changer de format) et rendent les jointures plus rapides (entiers).
- **Pourquoi des mesures 0/1 (`is_serious`…) ?** Un `SUM` donne directement le nombre,
  un `AVG` donne directement le pourcentage.
- **Limite :** pas d'heures travaillées dans les sources, donc le taux par rôle et équipe
  se calcule par effectif (hypothèse à signaler).
