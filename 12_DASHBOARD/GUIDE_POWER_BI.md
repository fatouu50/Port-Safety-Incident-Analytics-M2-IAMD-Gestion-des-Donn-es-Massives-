# Guide Power BI : construire le dashboard pas à pas

Projet 11 : Port Safety & Incident Analytics. Une seule page, simple.
Power BI Desktop est gratuit (Windows). Les noms de boutons sont ceux de la version française.

## 0. Préparer les données

Depuis la racine du projet :

```powershell
python 04_ETL/etl_pipeline.py          # crée la base
python 12_DASHBOARD/export_dashboard.py # écrit les 8 CSV dans 12_DASHBOARD/data
```

Aucun `worker_id` dans les CSV : le dashboard lit uniquement les MART et `dq_results`.
À refaire après chaque nouveau run du pipeline (le `_run_id` de `dq_results` change).

## 1. Importer les CSV

1. **Accueil → Obtenir les données → Texte/CSV**, choisir un fichier de `12_DASHBOARD/data`, puis **Charger**.
2. Recommencer pour les 8 fichiers (7 `mart_*` et `dq_results`).
3. **Accueil → Transformer les données** : vérifier les types.
   - `mois` doit rester du **texte** (`2026-01`).
   - `valeur`, `pct`, `score_risque` : **nombre décimal**.
4. **Fermer et appliquer**.
5. Vue **Modèle** : ne garder **aucune relation**. Les tables sont indépendantes (supprimer celles que Power BI a créées seul).

## 2. Les 8 cartes KPI

1. Insérer un visuel **Carte** et glisser `valeur` (table `mart_kpi_summary`).
2. Dans **Filtres sur ce visuel** : `kpi_id` → filtrage de base → cocher `KPI1`.
3. Mettre le nom du KPI sous le chiffre (`kpi` ou `unite`) et un titre court.
4. Copier-coller la carte 7 fois et changer le filtre : `KPI2` à `KPI8`.
5. Aligner les 8 cartes sur une ligne en haut de la page.

Valeurs attendues (à vérifier à l'écran) :

| Carte | Valeur | Sens |
|---|---|---|
| KPI1 | 144,0 | incidents par mois (mois complets) |
| KPI2 | 22,3 % | incidents graves |
| KPI3 | 95,4 | score de la zone la plus à risque (LOC015) |
| KPI4 | 759 | near-miss |
| KPI5 | 18,1 % | type le plus fréquent (SPILL) |
| KPI6 | 4,84 | incidents par travailleur (OPERATOR, équipe A) |
| KPI7 | 29,4 % | observations UNSAFE |
| KPI8 | 1 400 | incidents au total |

**Note à placer sous les cartes** (visuel **Zone de texte**) :

> Les cartes KPI sont des valeurs globales calculées par le pipeline : elles ne changent pas avec les filtres.
> KPI1 exclut octobre, qui s'arrête au 28 (le compter donnerait 140,0 à tort).

## 3. Les graphiques

| Question | Visuel | Table | Réglage |
|---|---|---|---|
| Quand | Histogramme + courbe | `mart_incidents_month` | axe `mois`, barres `nb_incidents`, courbe `nb_near_miss` |
| Où | Barres horizontales | `mart_incidents_by_area` | axe `location_id`, valeur `score_risque`, filtre **N premiers** = 10 |
| Comment (gravité) | Histogramme | `mart_severity_distribution` | axe `severity`, valeur `pct` |
| Comment (type) | Barres horizontales | `mart_recurring_incident_type` | axe `incident_type`, valeur `pct` |
| À qui | Matrice | `mart_incident_rate_shift_role` | lignes `role`, colonnes `shift`, valeurs `incidents_par_travailleur` |

- Gravité : ordre LOW, MEDIUM, HIGH, CRITICAL (trier à la main, pas par ordre alphabétique).
- Matrice : **Mise en forme conditionnelle → Couleur d'arrière-plan → dégradé** (case sombre = groupe le plus touché).
- Ne pas refaire les graphiques de l'EDA : le dashboard reste une vitrine des KPI. Un titre clair par visuel.

## 4. Le panneau qualité

1. Visuel **Tableau** avec `regle`, `table_name`, `nb_echecs`, `statut`, `detail` (table `dq_results`).
2. Sur `statut` : **Mise en forme conditionnelle → Règles** : OK vert, ALERTE orange, REJETS jaune, ECHEC rouge.
3. Trois cartes au-dessus : nombre de règles OK, nombre d'ALERTE, somme de `nb_echecs`
   (pour chacune, filtre du visuel sur le `statut` voulu, valeur = **Nombre de** `regle`).
4. Titre : « Qualité des données (DQ01 à DQ12) ».

## 5. Les filtres

Les MART sont déjà agrégés : chaque filtre n'agit que sur sa propre table.

| Segment | Table | Agit sur |
|---|---|---|
| `mois` | `mart_incidents_month` | graphique « Quand » |
| `area_type` | `mart_incidents_by_area` | graphique « Où » |
| `role` et `shift` | `mart_incident_rate_shift_role` | matrice « À qui » |

1. Insérer un **Segment** par ligne du tableau et glisser le champ.
2. Si un segment agit sur un visuel d'une autre table : sélectionner le segment, **Format → Modifier les interactions**, et mettre l'icône « aucun » sur ce visuel.
3. Les cartes KPI ne bougent pas : c'est voulu (voir la note).

## 6. Pour finir

- Thème clair, titres lisibles, mise en page en 16:9.
- Enregistrer sous `12_DASHBOARD/port_safety.pbix` (fichier binaire : décider avec Fatouma s'il est versionné).
- Soutenance : une phrase par visuel qui dit **ce qu'il montre** et **la décision HSE** qui en découle. Les captures seules ne suffisent pas.
