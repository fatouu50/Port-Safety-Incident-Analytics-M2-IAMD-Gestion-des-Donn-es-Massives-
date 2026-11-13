# 6. HDFS et stockage distribué

## 6.1 Objectif

Le sujet impose d'archiver l'historique des incidents et des observations dans un stockage distribué, HDFS ou S3, et d'expliquer son rôle et son lien avec le Data Warehouse. Nous avons choisi HDFS. HDFS (Hadoop Distributed File System) est un système de fichiers qui répartit les données sur plusieurs machines. *Source : sujet, étape 5 et § 5.*

## 6.2 Ce que nous avons fait

**Le cluster.** Un cluster est un groupe de machines qui travaillent ensemble. Le nôtre tourne sur un seul ordinateur, dans trois conteneurs Docker (image Apache Hadoop 3.3.6) : un NameNode et deux DataNodes. Le NameNode tient l'annuaire : il sait quel fichier est rangé où. Les DataNodes stockent le contenu. La réplication est réglée à 2 : chaque fichier est écrit en deux exemplaires, un par DataNode. *Source : `05_HDFS/docker-compose.yml` ; `05_HDFS/hadoop.env`.*

**L'archive.** Le script `prepare_archive.py` prépare l'archive à partir des fichiers sources. Il découpe les deux fichiers d'événements en un fichier par mois. C'est une partition : un rangement des données en dossiers selon une valeur, ici l'année et le mois. Exemple : les 171 incidents de mai sont dans `raw/incidents/year=2026/month=05/incidents_2026_05.csv`. *Source : `05_HDFS/prepare_archive.py`.*

**Tableau 13. Contenu de l'archive**

| Dossier | Contenu | Fichiers | Lignes |
|---|---|---|---|
| `raw/incidents/` | Incidents, 1 fichier par mois (janvier à octobre 2026) | 10 | 1 400 |
| `raw/safety_observations/` | Observations, 1 fichier par mois | 10 | 3 500 |
| `reference/` | Zones, travailleurs, engins, copiés tels quels | 3 | 415 |
| `_manifest/` | `manifest.csv` : chemin, nombre de lignes et empreinte MD5 de chaque fichier | 1 | 23 |
| `curated/mart/` | Les 7 tables MART du Data Warehouse, au format Parquet | 7 | 75 |

Le tableau 13 montre que l'archive garde trois choses : les données brutes, les tables d'analyse et un manifeste. Les 23 fichiers CSV totalisent 5 315 lignes, soit exactement le total des cinq fichiers sources. Le manifeste sert de bon de livraison : il permet de vérifier plus tard que rien n'a été perdu ni modifié. Parquet est un format de fichier en colonnes, adapté à l'analyse. *Source : `05_HDFS/prepare_archive.py`, exécuté le 13 novembre 2026 (23 fichiers, 5 315 lignes au manifeste) ; `05_HDFS/export_mart_parquet.py`.*

**Le chargement et les vérifications.** Le fichier `hdfs_commands.txt` liste les commandes, dans l'ordre.

**Tableau 14. Les étapes de chargement et de vérification dans HDFS**

| Étape | Commande | Ce qu'elle montre | Résultat |
|---|---|---|---|
| Copier l'archive dans HDFS | `hdfs dfs -put` vers `/port_exam/project_11/` | L'archive est dans le cluster | [À COMPLÉTER : sortie de `hdfs dfs -ls -R`, fournie par Fatouma] |
| Mesurer | `hdfs dfs -du -h` et `-count` | Taille et nombre de fichiers | [À COMPLÉTER : sortie de `-du -h` et `-count`] |
| Contrôler les blocs | `hdfs fsck` | État des blocs et réplication | [À COMPLÉTER : sortie de `hdfs fsck`] |
| Simuler une panne | `docker stop datanode1`, puis lecture d'un fichier | Le fichier reste lisible avec un seul DataNode | [À COMPLÉTER : résultat du test de panne] |
| Comparer au manifeste | `python hdfs_verify.py` | Lignes et MD5 identiques dans HDFS | [À COMPLÉTER : sortie de `hdfs_verify.py`] |

Le tableau 14 décrit ce que chaque commande doit prouver. Un bloc est un morceau de fichier stocké sur un DataNode. Le test de panne est le plus parlant : on arrête un DataNode et on relit un fichier. Avec une réplication de 2, l'autre DataNode en possède une copie. Le script `hdfs_verify.py` relit chaque fichier depuis HDFS, recompte ses lignes, recalcule son empreinte MD5 et compare le tout au manifeste. *Source : `05_HDFS/hdfs_commands.txt` ; `05_HDFS/hdfs_verify.py`. Les résultats d'exécution ne sont pas dans le dépôt.*

## 6.3 Pourquoi ces choix

**Le rôle de HDFS.** Le Data Warehouse ne garde que la dernière version des données : il est reconstruit à chaque run. HDFS garde l'historique brut, mois par mois. Si une règle de calcul change, on peut reconstruire le Data Warehouse à partir de l'archive. *Source : `06_GOVERNANCE/lineage.csv`, liens L33 et L34 ; `04_ETL/etl_pipeline.py`.*

**La partition par mois.** Le service HSE raisonne par mois : c'est le pas du KPI « incidents par mois ». Ranger un fichier par mois permet de relire une période sans ouvrir tout l'historique. *Déduction du groupe, à partir de `05_HDFS/prepare_archive.py` et du KPI1.*

**La réplication.** Les incidents sont des données de sécurité : les perdre empêcherait toute analyse des risques. Deux exemplaires protègent contre la panne d'une machine. *Source : `05_HDFS/hadoop.env` ; l'argument métier est une déduction du groupe.*

**L'archive part des sources.** L'archive est construite à partir des fichiers CSV, et non à partir du Data Warehouse. Elle reste donc valable même si le pipeline contient une erreur. Seules les tables MART viennent du Data Warehouse. *Source : `06_GOVERNANCE/lineage.csv`, lien L33.*

## 6.4 Résultat

L'archive locale contient 23 fichiers CSV et un manifeste. Les totaux du manifeste sont égaux à ceux des sources : 1 400 incidents, 3 500 observations, 25 zones, 350 travailleurs et 40 engins. *Source : `05_HDFS/archive/_manifest/manifest.csv`, généré le 13 novembre 2026.*

[À COMPLÉTER : résultat du chargement dans HDFS (nombre de fichiers, taille, réplication constatée, état « HEALTHY » ou non), à partir des sorties de Fatouma]

[À COMPLÉTER : capture de l'interface web du NameNode (http://localhost:9870), si Fatouma en fournit une]

## 6.5 Limites et hypothèses

- **Volume.** L'archive pèse environ 264 ko. HDFS est conçu pour des volumes beaucoup plus grands. Ici, il sert à montrer la méthode sur un historique appelé à grandir. *Source : taille du dossier `05_HDFS/archive` ; la remarque est une déduction du groupe.*
- **Un seul ordinateur.** Les trois conteneurs tournent sur la même machine. La réplication protège contre l'arrêt d'un conteneur, pas contre la panne de l'ordinateur. *Source : `05_HDFS/docker-compose.yml`.*
- **Droits d'accès désactivés.** Le cluster est configuré avec `dfs.permissions.enabled=false` : tout utilisateur peut tout lire. Or le dossier `raw/` est classé confidentiel (section 7). En production, il faudrait activer les droits et les listes d'accès. *Source : `05_HDFS/hadoop.env` ; `06_GOVERNANCE/GOVERNANCE_CHECKLIST.md`, § 2 et § 3.*
- **Archive non suivie par git.** Le dossier `archive/` est recréé par les scripts et n'est pas versionné. *Source : `.gitignore`.*
- [À COMPLÉTER : relecture de cette section par Fatouma, auteure de la partie HDFS, y compris les justifications de la section 6.3]
