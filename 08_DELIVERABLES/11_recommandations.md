# 11. Recommandations et conclusion

## 11.1 Objectif

Cette section traduit les résultats en actions pour le service HSE, puis fait le bilan du projet.

## 11.2 Recommandations pour le service HSE

**Tableau 22. Recommandations métier**

| Constat | Chiffre | Recommandation |
|---|---|---|
| Le parc à conteneurs concentre le risque | LOC015 : score 95,4 ; LOC014 : 91,6 ; 28,0 % d'incidents graves au parc | Renforcer en priorité les rondes sur LOC015 et LOC014 |
| Mai est un pic | 171 incidents, +29,5 % par rapport à avril, 27,5 % de graves | Chercher la cause : activité, saison, effectif |
| Plus d'un incident sur cinq est grave | 22,3 % (312 incidents) | Fixer un objectif de réduction et le suivre chaque mois |
| Certains groupes sont plus exposés | Opérateurs A : 4,84 ; conducteurs C : 4,79 incidents par travailleur | Briefing de sécurité renforcé pour ces deux groupes |
| Le ratio near-miss / graves baisse en mai et en juillet | 1,96 et 1,83, contre 2,4 en moyenne | Encourager la déclaration des near-miss ; suivre le ratio |
| Les observations ne désignent pas les zones dangereuses | Corrélation de −0,14 | Croiser observations et incidents ; équilibrer les observations entre zones |

Le tableau 22 classe les actions de la plus ciblée à la plus générale. Les deux premières lignes disent où et quand regarder d'abord. Les deux dernières concernent la méthode de prévention elle-même : ce que le service observe ne suffit pas à prédire où les incidents graves se produisent. Ces recommandations viennent de données synthétiques : elles montrent le type de décision que le dispositif permet. *Source : `07_EDA/eda_projet11.ipynb`, lignes « Action HSE » ; `10_EXPECTED_KPIS/kpi_catalog.csv` ; requête Q03.*

## 11.3 Recommandations sur les données

Trois manques limitent aujourd'hui l'analyse. Les combler serait utile au service HSE.

- **Les heures travaillées.** Elles permettraient un vrai taux d'exposition par équipe, au lieu d'un taux par effectif.
- **La zone de rattachement des engins.** Les codes `home_area` devraient utiliser les mêmes identifiants que les zones.
- **Un lien entre incidents et observations.** Une clé commune éviterait de compter deux fois un même near-miss.

*Source : `04_ETL/dwh_conception.md`, § 5 et § 6 ; `10_EXPECTED_KPIS/kpi_catalog.csv`. Ces trois propositions sont des déductions du groupe à partir des limites constatées.*

## 11.4 Bilan du projet

Le projet répond à la problématique de la section 1. Les cinq fichiers sources sont devenus huit indicateurs contrôlés, qui disent où, quand, comment et à qui arrivent les incidents.

Les huit étapes du sujet sont couvertes. Le SQL vérifie les sources et calcule les premiers KPI. Le Data Warehouse organise les données en étoile, avec 2 faits et 9 dimensions. Le pipeline charge 5 315 lignes à travers quatre couches, applique 12 règles de qualité et prouve par trois tests qu'il est idempotent, qu'il trace les rejets et qu'il résiste à une panne. L'archive HDFS conserve l'historique par mois. La gouvernance fixe les responsables, la classification, les accès et le lineage. L'analyse Python interprète six graphiques. Le dashboard met le tout à disposition. *Source : sections 3 à 10.*

## 11.5 Limites et suites possibles

Les limites ont été signalées dans chaque section. Les principales sont : un jeu de données petit et synthétique, des définitions posées par le groupe (incident grave, score de risque, seuils d'alerte), des droits d'accès documentés mais non appliqués, et un pipeline lancé à la main.

Avec des données réelles, les suites logiques seraient : valider les définitions et les seuils avec le service HSE, appliquer techniquement les droits d'accès, pseudonymiser l'identifiant des travailleurs, et déclencher le pipeline automatiquement à chaque livraison. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 8 ; le déclenchement automatique est une proposition du groupe.*
