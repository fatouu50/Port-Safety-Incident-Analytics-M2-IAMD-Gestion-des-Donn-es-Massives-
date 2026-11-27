# 1. Contexte et problématique

## 1.1 Objectif

Cette section présente le besoin du service HSE, les utilisateurs du projet et les questions auxquelles le dispositif doit répondre.

## 1.2 Le contexte

Le projet se place dans un terminal portuaire. Le service HSE (Hygiène, Sécurité, Environnement) est chargé de la sécurité des personnes sur le site. Il souhaite analyser trois choses : les incidents, les near-miss et les zones qui présentent des risques récurrents. Un near-miss est un presque-accident : un événement qui aurait pu causer un dommage, mais qui n'en a pas causé. *Source : sujet, § 1.*

L'objectif fixé par le sujet est de construire un dispositif analytique de sécurité portuaire, sans utiliser de données personnelles réelles. Toutes les données du projet sont synthétiques : elles ont été fabriquées pour l'enseignement. *Source : sujet, § 1 et § 2.*

## 1.3 La problématique

Le service HSE dispose de cinq fichiers. Deux enregistrent des événements, un par un : les incidents et les observations de sécurité. Trois décrivent le site : les zones, les travailleurs et les engins. Tels quels, ces fichiers ne répondent à aucune question. Il faut les relier, les contrôler et les résumer.

La problématique est donc la suivante : **comment transformer des fichiers d'événements bruts en indicateurs fiables, qui disent au service HSE où, quand, comment et à qui arrivent les incidents ?** *Source : `README.md`, objectif.*

Le sujet impose six indicateurs, appelés KPI (indicateurs clés de performance). Un KPI est un chiffre suivi dans le temps pour décider. Exemple : le nombre d'incidents par mois.

**Tableau 1. Les six KPI du sujet, la question du service HSE à laquelle chacun répond et la décision visée**

| Question | KPI demandé par le sujet | Décision visée |
|---|---|---|
| Quand ? | Incidents par mois | Repérer les mois anormaux |
| Comment ? | Répartition par gravité | Fixer un objectif sur les incidents graves |
| Comment ? | Type d'incident récurrent | Cibler les causes récurrentes |
| Où ? | Incidents par zone | Prioriser les rondes et les inspections |
| À qui ? | Taux d'incidents par équipe et par rôle | Cibler la formation et les briefings |
| Signaux faibles | Nombre de near-miss | Suivre la culture de déclaration |

Le tableau 1 relie chaque KPI à une décision. C'est le fil du rapport : un chiffre n'a d'intérêt que s'il aide le service HSE à agir. Les décisions visées sont celles du catalogue de KPI du groupe. *Source : sujet, § 4 ; `10_EXPECTED_KPIS/kpi_catalog.csv`, colonne `decision_hse`.*

## 1.4 Les utilisateurs

Le sujet nomme un seul utilisateur : le service HSE. Le groupe a défini cinq rôles dans sa politique d'accès, dont quatre sont des personnes et un est un compte de service, c'est-à-dire un accès réservé à un programme. C'est une hypothèse d'organisation, et non une donnée du sujet.

- **Le responsable HSE** lit les indicateurs et décide des actions.
- **L'analyste** explore les données avec Python.
- **Le dashboard** n'est pas une personne : c'est le compte de service du tableau de bord interactif, qui lit les indicateurs pour les afficher à l'écran.
- **L'auditeur qualité** vérifie les contrôles et les lignes rejetées.
- **Le data engineer** construit et exploite la chaîne de traitement. Ce rôle est tenu par le groupe.

*Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 1 et § 3.*

## 1.5 La démarche

Le sujet impose huit étapes. Le rapport les suit dans l'ordre : contexte et données (sections 1 et 2), SQL (section 3), Data Warehouse (section 4), ETL (section 5), stockage distribué HDFS (section 6), qualité et gouvernance (section 7), analyse exploratoire en Python (section 8), puis KPI, architecture finale et recommandations (sections 9 à 11). *Source : sujet, § 3 ; `08_DELIVERABLES/TRAME_RAPPORT.md`.*

La chaîne complète tient en une ligne : fichiers CSV → SQL → Data Warehouse → HDFS → analyse → dashboard. Tout le code est dans le dépôt du projet. Chaque résultat peut être reproduit par les commandes listées en annexe B. *Source : `README.md` ; en-tête de chaque script.*

## 1.6 Limites et hypothèses

- Les données sont synthétiques. Les résultats illustrent la méthode ; ils ne décrivent pas un terminal réel. *Source : sujet, § 2.*
- Le sujet ne définit ni « incident grave », ni la formule d'un score de risque par zone. Le groupe a posé ses propres définitions, signalées à chaque usage (hypothèses H1 à H4, section 4).
- La répartition du travail dans le groupe est la suivante : Fatouma Soubere Mahamoud a réalisé le SQL, HDFS et l'analyse exploratoire ; Mako Mohamed Aden a réalisé le Data Warehouse, l'ETL et la gouvernance. Le dashboard a été fait à deux, sur une seule page : Fatouma a réalisé la partie du haut (filtres, 3 KPI et 6 graphiques) et Mako la section « Qualité des données » en bas de page. *Source : `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 1.*
