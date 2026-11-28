# 9. KPI et résultats métier

## 9.1 Objectif

Cette section rassemble les indicateurs du projet en un seul tableau. Le sujet demande au moins 5 KPI et en nomme 6. Nous en publions 8 : les 6 du sujet et 2 ajoutés par le groupe. *Source : sujet, § 4 et § 6.*

## 9.2 Ce que nous avons fait

Chaque KPI est décrit dans un catalogue : sa définition, son grain, sa formule, sa table MART, la décision qu'il sert et ses limites. Les valeurs sont calculées par le pipeline et rangées dans la table `mart_kpi_summary`. Le dashboard et le notebook lisent cette table : le chiffre est donc le même partout. *Source : `10_EXPECTED_KPIS/kpi_catalog.csv` ; `04_ETL/etl_pipeline.py`, étape 5.6.*

**Tableau 20. Les 8 KPI du projet**

| KPI | Valeur | Calcul | Décision HSE |
|---|---|---|---|
| KPI1. Incidents par mois | 144,0 | 1 296 incidents ÷ 9 mois complets | Repérer les mois anormaux (mai : 171) |
| KPI2. Incidents graves | 22,3 % | (239 `HIGH` + 73 `CRITICAL`) ÷ 1 400 | Fixer un objectif de réduction |
| KPI3. Zone la plus à risque | 95,4 / 100 | Score de LOC015 (parc à conteneurs) | Prioriser les rondes et les inspections |
| KPI4. Near-miss | 759 | 225 (incidents) + 534 (observations) | Suivre les signaux faibles |
| KPI5. Type le plus fréquent | 18,1 % | `SPILL` : 253 ÷ 1 400 | Cibler les causes récurrentes |
| KPI6. Groupe le plus exposé | 4,84 | Opérateurs, équipe A : 121 incidents ÷ 25 travailleurs | Cibler la formation et les briefings |
| KPI7. Observations `UNSAFE` (ajouté) | 29,4 % | 1 030 ÷ 3 500 observations | Mesurer la vigilance sur le terrain |
| KPI8. Total des incidents (ajouté) | 1 400 | Nombre de lignes de `fact_incident` | Vérifier que le Data Warehouse est complet |

Le tableau 20 donne, pour chaque chiffre, les nombres qui le composent : le lecteur peut refaire le calcul. Les KPI 1 à 6 répondent aux six demandes du sujet. Le KPI7 complète le KPI4 : il mesure ce que les observateurs voient sur le terrain. Le KPI8 est un contrôle : il doit égaler le nombre de lignes du fichier `incidents.csv`. *Source : `10_EXPECTED_KPIS/kpi_catalog.csv` ; table `mart_kpi_summary`.*

## 9.3 Pourquoi ces choix

Un KPI doit pouvoir être expliqué en une phrase au service HSE. Trois choix de calcul vont dans ce sens.

- **KPI1 sur les mois complets.** Octobre s'arrête au 28. Le compter comme un mois entier donnerait 140,0 au lieu de 144,0 et ferait croire à une baisse.
- **KPI3 sous forme de score.** Le nombre d'incidents seul favorise les zones très fréquentées. Le score combine la gravité, le volume et les observations. Chaque terme est divisé par le maximum des zones, pour que le score aille de 0 à 100. *Source : `kpi_catalog.csv`, KPI3.*
- **KPI6 par travailleur.** Les groupes n'ont pas la même taille (21 à 41 personnes). Diviser par l'effectif permet de les comparer.

## 9.4 Résultat

Les valeurs calculées en SQL sur les sources (KPI1, KPI2, KPI4 et KPI6, section 3) sont identiques à celles du Data Warehouse. Le notebook (section 8) et le dashboard lisent les huit valeurs dans la même table. À chaque run, le pipeline les compare aux valeurs attendues et affiche le résultat. *Source : `04_ETL/etl_pipeline.py`, étapes 5.5 et 5.6 ; `03_SQL/starter_queries.sql` ; `07_EDA/eda_projet11.ipynb`.*

Pour le service HSE, la lecture d'ensemble est la suivante. Le volume mensuel est stable (144 incidents), avec un pic en mai. Plus d'un incident sur cinq est grave. Le risque se concentre sur le parc à conteneurs. Aucun type d'incident ne domine : les six types pèsent entre 15,5 % et 18,1 %. Les écarts entre groupes de travailleurs sont modérés. *Source : `kpi_catalog.csv` ; `mart_recurring_incident_type`.*

## 9.5 Limites et hypothèses

- **KPI2** dépend de la définition de « grave » (hypothèse H2).
- **KPI3** dépend des pondérations 50 / 30 / 20, choisies par le groupe.
- **KPI4** additionne deux sources sans clé commune : un même événement pourrait être compté deux fois.
- **KPI5** distingue peu les types : l'écart entre le premier et le dernier est de 2,6 points.
- **KPI6** est un taux par effectif. Il ne prouve pas qu'un groupe est plus dangereux qu'un autre.

*Source : `10_EXPECTED_KPIS/kpi_catalog.csv`, colonne `hypotheses_limites`.*
