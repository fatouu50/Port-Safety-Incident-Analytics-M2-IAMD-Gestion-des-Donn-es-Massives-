



\## Répartition du travail

| Responsable | Phases |
|---|---|
| **Fatouma** | Phase 3 (SQL), Phase 6 (HDFS), Phase 8 (EDA) |
| **Mako** | Phase 4 (Data Warehouse), Phase 5 (ETL), Phase 7 (Gouvernance) |
| **Ensemble** | Phase 0 (Préparation), Phase 1 (Données), Phase 2 (KPI et hypothèses), Phase 9 (Dashboard), Phase 10 (Architecture, rapport, soutenance) |



\## Phase 0 — Préparation (fait)

**Responsable : Ensemble**



1\. Lire le sujet `00\_BRIEF/Projet\_11\_Sujet\_Consignes.docx` en entier.

2\. Lire `README\_FIRST.txt` et l'ordre imposé : 03\_SQL → 04\_ETL → 05\_HDFS → 06\_GOVERNANCE → 07\_EDA → 11\_ARCHITECTURE.

3\. Noter le barème /20 et les livrables.

4\. Répartir le travail avec Mako.

5\. Installer Python 3, puis `pip install -r requirements.txt` (pandas, matplotlib, pyarrow, jupyter).

6\. Installer DB Browser for SQLite.

7\. Installer Docker Desktop, pour HDFS.

8\. Installer git et créer le compte GitHub.

9\. Créer le dépôt privé `projet11-port-safety` et faire le premier push. \*\*À vérifier que c'est fait.\*\*

10\. Inviter Mako comme collaborateur.



\## Phase 1 — Comprendre les données (fait)

**Responsable : Ensemble**



11\. Règle d'or : ne \*\*jamais\*\* modifier `01\_DATA\_RAW`.

12\. Ouvrir les CSV avec pandas, pas avec Excel, qui affiche tout dans une seule colonne.

13\. `shape` : 1 400 / 3 500 / 350 / 25 / 40 lignes.

14\. `head()` : définir ce que représente une ligne de chaque table (le grain).

15\. `dtypes`, puis convertir les dates avec `to\_datetime`.

16\. Période couverte : du 1er janvier au 28 octobre, donc octobre est incomplet.

17\. `isna()` : 0 valeur manquante, ce qui ne veut pas dire « données parfaites ».

18\. `nunique()` et `duplicated()` : trouver les clés candidates.

19\. `value\_counts()` : gravité, type d'incident, type d'observation, rôle, équipe.

20\. `isin()` : vérifier les clés étrangères (0 orphelin).

21\. Noter le piège n°1 : NEAR\_MISS existe dans 2 tables.

22\. Noter le piège n°2 : `home\_area` (Y01…) ne correspond à aucune zone LOCxxx.

23\. Lire `02\_DATA\_DICTIONARY/data\_dictionary.csv`.

24\. Rédiger le tableau des 5V (Volume, Vélocité, Variété, Véracité, Valeur).



\## Phase 2 — Définir les KPI et les hypothèses (fait)

**Responsable : Ensemble**



25. Remplir `10_EXPECTED_KPIS/kpi_catalog.csv` : définition, grain, source et formule de chaque KPI (8 KPI).

26. Décider : le near-miss additionne les 2 sources (incidents + observations). **Validé.**

    *Pourquoi : un near-miss est un signal d'alerte avant l'accident, et il est enregistré à 2 endroits (225 dans les incidents, 534 dans les observations). On additionne pour ne perdre aucun signal : 225 + 534 = 759.*

27. Décider : le taux se calcule par effectif, faute d'heures travaillées. **Hypothèse, à signaler comme limite.**

    *Pourquoi : les données n'ont pas d'heures travaillées. On divise donc les incidents du groupe par son nombre de travailleurs (121 ÷ 25 = 4,84). C'est une approximation.*

28. Décider : l'équipe est celle du travailleur, et non celle déduite de l'heure de l'incident. **Validé.**

    *Pourquoi : on n'a pas les horaires des équipes A, B et C, donc déduire l'équipe de l'heure serait inventer. La fiche du travailleur est la seule information fiable. Limite : un travailleur peut avoir un incident hors de son horaire habituel.*

29. Décider : octobre est exclu de la moyenne mensuelle, car il s'arrête au 28. **Validé, code corrigé : KPI1 = 144,0.**

    *Pourquoi : octobre n'a que 28 jours de données (104 incidents contre environ 140 ailleurs). L'inclure ferait baisser la moyenne à tort. On calcule sur les 9 mois complets : 1 296 ÷ 9 = 144,0. Le code comparait d'abord à « 28 jours », ce qui laissait passer octobre ; il compare maintenant au vrai nombre de jours du mois.*



**Le sujet demande au moins 5 KPI. Nous en avons 8.**



| KPI | Valeur | Définition | Formule | Table MART | Décision HSE |
|---|---|---|---|---|---|
| **KPI1** Incidents par mois | 144,0 incidents/mois | Moyenne des incidents sur les mois complets (octobre exclu, il s'arrête au 28) | incidents des 9 mois complets ÷ 9 | `mart_incidents_month` | Repérer les mois anormaux (mai : 171) |
| **KPI2** Part des incidents graves | 22,3 % | Incidents HIGH ou CRITICAL parmi tous les incidents | 100 × graves ÷ total | `mart_severity_distribution` | Fixer un objectif de réduction des événements graves |
| **KPI3** Zone la plus à risque | 95,4 / 100 (LOC015, YARD) | Score par zone : 50 % incidents graves, 30 % volume, 20 % observations UNSAFE | 100 × (0,5 × graves + 0,3 × volume + 0,2 × % unsafe), chacun rapporté au maximum | `mart_area_risk_ranking` | Prioriser les rondes et inspections |
| **KPI4** Near-miss | 759 | Presque-accidents : 225 dans les incidents + 534 dans les observations | 225 + 534 | `mart_near_miss` | Suivre les signaux faibles et la culture de déclaration |
| **KPI5** Type d'incident le plus fréquent | 18,1 % (SPILL, 253) | Part du type d'incident le plus fréquent | 100 × incidents du type ÷ total | `mart_recurring_incident_type` | Cibler les causes récurrentes |
| **KPI6** Taux par rôle et équipe | 484 pour 100 travailleurs (OPERATOR, équipe A) | Incidents du groupe rapportés au nombre de travailleurs du groupe (hypothèse : pas d'heures travaillées) | 100 × incidents du groupe ÷ travailleurs du groupe | `mart_incident_rate_shift_role` | Cibler la formation et les briefings |
| **KPI7** Observations dangereuses | 29,4 % | Part des observations terrain classées UNSAFE | 100 × UNSAFE ÷ total des observations | `mart_kpi_summary` | Mesurer la vigilance terrain |
| **KPI8** Total des incidents | 1 400 | Nombre d'incidents chargés dans le DWH (contrôle de réconciliation) | COUNT(incident_id) | `mart_kpi_summary` | Vérifier que le DWH est complet |



\## Phase 3 — SQL (fait)

**Responsable : Fatouma**



30\. Écrire `schema\_sources.sql` : PRIMARY KEY, REFERENCES, CHECK, INDEX.

31\. Écrire `build\_source\_db.py` : référentiels d'abord, puis incidents et observations.

32\. `PRAGMA foreign\_key\_check` doit renvoyer une liste vide.

33\. Q01 : compter chaque table.

34\. Q02 : JOIN 1, incidents enrichis.

35\. Vérifier que le nombre de lignes est le même avant et après la jointure.

36\. Q03 : JOIN 2, part d'incidents graves par type de zone.

37\. Q04 : JOIN 3, `LEFT JOIN … IS NULL` pour trouver les orphelins.

38\. Q05 : incidents par mois.

39\. Q06 : répartition par gravité.

40\. Q07 : near-miss des 2 sources.

41\. Q08 : taux par rôle et par équipe.

42\. Q09 : sous-requête, zones au-dessus de la moyenne.

43\. Q10 : CTE + `RANK()`, type le plus récurrent par type de zone.

44\. Q11 : CTE + `LAG()`, variation d'un mois à l'autre.

45\. Q12 : observations UNSAFE face aux incidents graves par zone.

46\. Q13 : vérifier le grain (1 400 = 1 400).

47\. Q14 : chercher les doublons métier.

48\. Q15 : `EXPLAIN QUERY PLAN` pour montrer l'index.

49\. Exporter les résultats dans `03\_SQL/resultats/` et écrire une phrase d'interprétation par requête.



\## Phase 4 — Concevoir le Data Warehouse (fait)

**Responsable : Mako**



50\. Choisir le grain : 1 ligne = 1 incident, et 1 ligne = 1 observation.

51\. Lister les 9 dimensions : date, heure, zone, engin, travailleur, type d'incident, gravité, type d'observation, rôle du déclarant.

52\. Prévoir une clé de substitution entière par dimension.

53\. Choisir les mesures : `incident\_count`, `is\_serious`, `is\_near\_miss`, `severity\_weight`, `is\_unsafe`.

54\. Dessiner le schéma en étoile.



\## Phase 5 — ETL (fait, sauf 1 correction)

**Responsable : Mako**



55\. \*\*RAW\*\* : charger les CSV en texte et ajouter `\_source\_file`, `\_row\_num`, `\_run\_id`.

56\. Enregistrer le manifeste MD5 des sources.

57\. \*\*STAGING\*\* : supprimer les espaces et mettre en majuscules.

58\. DQ02 : valeurs obligatoires.

59\. DQ03 : doublons.

60\. DQ04 : format des identifiants.

61\. DQ05 : dates valides, ni avant 2020 ni dans le futur.

62\. DQ06 : valeurs autorisées.

63\. DQ07 : clés étrangères.

64\. Écrire chaque ligne refusée dans `stg\_rejects` avec sa raison.

65\. Créer les tables `stg\_\*` avec les lignes valides.

66\. DQ11 : alerte sur `home\_area`.

67\. \*\*CORE\*\* : créer `dim\_date` et `dim\_hour`.

68\. Créer `dim\_location`, `dim\_equipment` et `dim\_worker`.

69\. Créer `dim\_incident\_type`, `dim\_severity`, `dim\_observation\_type` et `dim\_reporter\_role`.

70\. Charger `fact\_incident`.

71\. Charger `fact\_safety\_observation`.

72\. Faire les 5 contrôles du TP S3 : COUNT, clés NULL, unicité, correspondances, `SUM(count)`.

73\. \*\*MART\*\* : créer les 13 tables.

74\. Créer `mart\_kpi\_summary`.

75\. DQ08 : réconciliation RAW = STAGING + REJETS = FAIT.

76\. DQ09 : fraîcheur des données.

77\. DQ10 : variation du volume mensuel.

78\. Enregistrer les résultats dans `dq\_results`.

79\. Exécuter tout le run dans une transaction, avec rollback en cas d'erreur.

80\. Tenir le journal `etl\_run\_log` (volumes, durée).

81\. Prouver l'idempotence : 2 runs donnent le même checksum.

82\. Lancer le test d'anomalies et obtenir \*\*11 rejets\*\* tracés.

83\. \*\*À FAIRE\*\* : corriger le KPI1 (140 → 144) dans `etl\_pipeline.py`, `kpi\_catalog.csv` et le texte de l'EDA.



\## Phase 6 — HDFS (fait)

**Responsable : Fatouma**



84\. `docker compose up -d` : 1 NameNode et 2 DataNodes.

85\. Ouvrir http://localhost:9870 et lancer `hdfs dfsadmin -report`.

86\. `prepare\_archive.py` : archive partitionnée par année et mois, MART en Parquet, manifeste.

87\. `docker cp` : copier du PC vers le conteneur Master.

88\. `hdfs dfs -mkdir -p` : créer l'arborescence.

89\. `hdfs dfs -put` : envoyer les fichiers.

90\. `-ls -R`, `-du -h`, `-count` : vérifier.

91\. `hdfs fsck … -files -blocks -locations` : résultat HEALTHY.

92\. `hdfs dfs -setrep -w 2` : réplication 2.

93\. `hdfs\_verify.py` : HDFS = manifeste = DWH.

94\. Faire les captures d'écran pour le rapport.

95\. `docker compose down` pour arrêter le cluster.



\## Phase 7 — Gouvernance (fait)

**Responsable : Mako**



96\. Désigner le propriétaire métier (HSE) et le propriétaire technique (data engineer).

97\. Classer les données : RAW, STAGING et CORE confidentiels ; MART internes.

98\. Écrire la matrice d'accès selon le moindre privilège.

99\. Écrire `lineage.csv`.

100\. Écrire `data\_quality\_rules.csv` (DQ01 à DQ11).

101\. Définir le SLA (fraîcheur) et les seuils d'alerte.

102\. Écrire `data\_dictionary\_enrichi.csv`.



\## Phase 8 — EDA (fait)

**Responsable : Fatouma**



103\. Faire lire \*\*uniquement\*\* les MART au notebook.

104\. Produire les 6 graphiques, chacun avec la question HSE, l'interprétation et l'action proposée.

105\. Enregistrer les PNG dans `07\_EDA/figures/`.

106\. Écrire les conclusions et les limites.



\## Phase 9 — Dashboard (À FAIRE)

**Responsable : Ensemble**



107\. Choisir l'outil et le justifier, par exemple Power BI, Looker Studio ou Streamlit.

108\. Le connecter \*\*aux tables MART uniquement\*\*, soit directement à la base SQLite, soit à un export CSV des MART.

109\. Bandeau du haut : les cartes des 8 KPI.

110\. Graphique de la tendance mensuelle, avec octobre marqué incomplet.

111\. Répartition par gravité et par type.

112\. Classement des zones par score de risque.

113\. Heatmap rôle × équipe.

114\. Ratio near-miss par incident grave.

115\. Filtres : mois, type de zone, gravité.

116\. Panneau qualité : statut DQ01 à DQ11 et date du dernier run (`dq\_results`, `etl\_run\_log`).

117\. Vérifier que les chiffres du dashboard sont identiques à `mart\_kpi\_summary`.

118\. Prévoir le rafraîchissement automatique après chaque ETL.

119\. Faire les captures pour le rapport et l'ajouter au schéma d'architecture.



\## Phase 10 — Architecture, rapport, soutenance (À FAIRE, sauf l'architecture)

**Responsable : Ensemble**



120\. Préparer les livrables finaux, dans cet ordre :

&#x20;   - Architecture : `architecture.md` et `architecture.png`. \*\*Fait.\*\*

&#x20;   - `run\_all.py` : relancer tout en une commande. \*\*Fait.\*\*

&#x20;   - Rapport de 20 à 30 pages : les 11 parties de `TRAME\_RAPPORT.md`, avec figures, tableaux et interprétation à chaque résultat. \*\*À faire.\*\*

&#x20;   - Présentation de 10 à 12 slides, pour 15 à 20 minutes, avec notes orales. \*\*À faire.\*\*

121\. Préparer la démo et la remise : un script de démo (`run\_all.py`, test d'anomalies avec ses 11 rejets, `mart\_kpi\_summary`, dashboard), des captures de secours si Docker ne démarre pas, une répétition chronométrée, un dernier push GitHub, puis la remise.







