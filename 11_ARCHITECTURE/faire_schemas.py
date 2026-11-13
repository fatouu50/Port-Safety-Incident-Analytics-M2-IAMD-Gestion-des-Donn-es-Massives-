"""
Projet 11 : dessiner les deux schémas du rapport.
  - 11_ARCHITECTURE/architecture_finale.png : architecture de bout en bout
    (d'après 06_GOVERNANCE/lineage.csv, plus HDFS, le dashboard et les décisions HSE)
  - 04_ETL/schema_etoile.png : schéma en étoile du Data Warehouse
    (d'après 04_ETL/dwh_conception.md)
Lancement depuis la racine du projet :  python 11_ARCHITECTURE/faire_schemas.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

DOSSIER_ARCHITECTURE = Path(__file__).resolve().parent
DOSSIER_ETL = DOSSIER_ARCHITECTURE.parent / "04_ETL"

# Couleurs de la charte graphique (voir README)
VIOLET_FONCE = "#4A1D6E"
VIOLET = "#7B3FA0"
ROSE = "#EE82B7"
LAVANDE = "#EDE4F5"
ROSE_PALE = "#FDEEF5"
FRAMBOISE = "#9E1F5C"
GRIS = "#6B6375"
VERT = "#2E8B57"


def boite(ax, x, y, largeur, hauteur, titre, lignes=(), fond=LAVANDE, bord=VIOLET, couleur_titre=VIOLET_FONCE,
          taille_titre=9.5, taille_texte=7.5, gauche=False):
    """Dessine une boîte arrondie avec un titre en gras et des lignes de texte (centrées ou alignées à gauche)."""
    ax.add_patch(FancyBboxPatch((x, y), largeur, hauteur, boxstyle="round,pad=0.02,rounding_size=0.12",
                                facecolor=fond, edgecolor=bord, linewidth=1.4))
    haut = y + hauteur - 0.22
    x_texte = x + 0.3 if gauche else x + largeur / 2
    alignement = "left" if gauche else "center"
    ax.text(x_texte, haut, titre, ha=alignement, va="top", fontsize=taille_titre, fontweight="bold", color=couleur_titre)
    for i, ligne in enumerate(lignes):
        ax.text(x_texte, haut - 0.5 - i * 0.36, ligne, ha=alignement, va="top", fontsize=taille_texte, color="#2B2333")


def fleche(ax, depart, arrivee, texte="", couleur=VIOLET, style="-", decalage=(0, 0.12), courbe=0.0, taille=7.5):
    """Dessine une flèche entre deux points, avec un texte au milieu."""
    ax.annotate("", xy=arrivee, xytext=depart,
                arrowprops=dict(arrowstyle="-|>", color=couleur, lw=1.5, linestyle=style,
                                connectionstyle=f"arc3,rad={courbe}", shrinkA=2, shrinkB=2))
    if texte:
        ax.text((depart[0] + arrivee[0]) / 2 + decalage[0], (depart[1] + arrivee[1]) / 2 + decalage[1],
                texte, ha="center", va="bottom", fontsize=taille, color=GRIS, style="italic")


# ---------------------------------------------------------------------
# Schéma 1 : architecture finale
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11.7, 8.3))   # A4 paysage
ax.set_xlim(0, 23.4)
ax.set_ylim(0, 16.6)
ax.axis("off")

ax.text(0.3, 16.2, "Architecture finale : des fichiers sources aux décisions du service HSE",
        fontsize=14, fontweight="bold", color=VIOLET_FONCE, va="center")

# Bandeau du Data Warehouse (derrière les 4 couches)
ax.add_patch(FancyBboxPatch((4.55, 9.0), 13.7, 6.4, boxstyle="round,pad=0.02,rounding_size=0.15",
                            facecolor="#FAF7FD", edgecolor=VIOLET_FONCE, linewidth=1.2, linestyle="--"))
ax.text(11.4, 15.0, "DATA WAREHOUSE (base SQLite), construit par 04_ETL/etl_pipeline.py",
        ha="center", va="center", fontsize=9, fontweight="bold", color=VIOLET_FONCE)

# Ligne du haut : Sources -> RAW -> STAGING -> CORE -> MART
y, h = 9.4, 5.0
boite(ax, 0.3, y, 3.6, h, "SOURCES", ["5 fichiers CSV", "(01_DATA_RAW)", "", "incidents : 1 400", "observations : 3 500",
                                    "zones : 25", "travailleurs : 350", "engins : 40", "", "Total : 5 315 lignes"],
      fond="#FFFFFF", bord=GRIS, couleur_titre=GRIS)
boite(ax, 4.9, y, 2.95, h, "RAW", ["copie fidèle,", "tout en texte", "", "5 tables raw_*", "+ raw_manifest", "5 315 lignes", "",
                                   "Règles DQ01, DQ12", "", "confidentiel"])
boite(ax, 8.3, y, 2.95, h, "STAGING", ["nettoyage", "et contrôles", "", "5 tables stg_*", "+ stg_rejects", "0 rejet", "",
                                       "Règles DQ02 à DQ07", "", "confidentiel"])
boite(ax, 11.7, y, 2.95, h, "CORE", ["schéma en étoile", "", "9 dimensions", "2 tables de faits", "1 400 incidents",
                                     "3 500 observations", "", "Règle DQ08", "", "confidentiel"])
boite(ax, 15.1, y, 2.95, h, "MART", ["tables prêtes", "pour l'analyse", "", "7 tables mart_*", "8 KPI, 75 lignes",
                                     "aucun worker_id", "", "Règles DQ09, DQ10", "", "interne"], fond=ROSE_PALE, bord=ROSE)
for x_depart, x_arrivee in [(3.9, 4.9), (7.85, 8.3), (11.25, 11.7), (14.65, 15.1)]:
    fleche(ax, (x_depart, 11.9), (x_arrivee, 11.9))

# Consommation
boite(ax, 19.0, 12.5, 4.1, 2.5, "EDA (Python)", ["07_EDA/eda_projet11.ipynb", "6 graphiques interprétés", "lit les MART seulement"],
      fond="#FFFFFF", bord=VIOLET)
boite(ax, 19.0, 9.2, 4.1, 2.9, "DASHBOARD (Streamlit)", ["12_DASHBOARD/app.py", "8 cartes KPI, 5 onglets", "dont Qualité des données",
                                                        "lit les MART et le suivi"], fond="#FFFFFF", bord=VIOLET, taille_titre=8)
fleche(ax, (18.05, 12.6), (19.0, 13.5))
fleche(ax, (18.05, 11.2), (19.0, 10.6))

# Décisions HSE
boite(ax, 19.0, 4.4, 4.1, 4.2, "DÉCISIONS HSE", ["Où : rondes en priorité", "sur LOC015 et LOC014", "Quand : cause du pic de mai",
                                                "Qui : briefings opérateurs A", "Gravité : objectif sur les", "incidents graves (22,3 %)",
                                                "Signaux faibles : near-miss"],
      fond=ROSE_PALE, bord=FRAMBOISE, couleur_titre=FRAMBOISE)
fleche(ax, (21.05, 9.2), (21.05, 8.6), couleur=FRAMBOISE)

# HDFS
boite(ax, 0.3, 4.4, 10.0, 3.6, "ARCHIVE HDFS : /port_exam/project_11/archive",
      ["Docker : 1 NameNode + 2 DataNodes (Hadoop 3.3.6), réplication 2",
       "raw/ : incidents et observations, 1 fichier par mois : 20 fichiers",
       "reference/ : zones, travailleurs, engins : 3 fichiers",
       "_manifest/manifest.csv : lignes et empreinte MD5 de chaque fichier",
       "curated/mart/ : les 7 tables MART au format Parquet",
       "Contrôle : hdfs_verify.py compare HDFS au manifeste (lignes et MD5)"],
      fond="#FFFFFF", bord=VIOLET_FONCE, gauche=True)
fleche(ax, (2.1, 9.4), (2.1, 8.0), "prepare_archive.py", decalage=(1.6, -0.15), couleur=VIOLET_FONCE)
fleche(ax, (16.2, 9.4), (9.4, 8.0), "export_mart_parquet.py", decalage=(2.6, -0.5), couleur=VIOLET_FONCE, style="--")

# Suivi qualité
boite(ax, 10.75, 4.4, 7.65, 3.3, "QUALITÉ ET SUIVI DU PIPELINE",
      ["12 règles (DQ01 à DQ12), 39 contrôles : dq_results",
       "etl_run_log : date, durée, volumes, statut du run",
       "stg_rejects : chaque ligne refusée et sa raison",
       "test_etl.py : idempotence, 11 anomalies = 11 rejets,",
       "panne simulée et rollback"],
      fond="#F3FAF6", bord=VERT, couleur_titre=VERT, gauche=True)
fleche(ax, (18.4, 6.6), (19.0, 9.6), couleur=VERT, style="--", courbe=0.15)

# Gouvernance
boite(ax, 0.3, 0.6, 22.8, 3.1, "GOUVERNANCE ET SÉCURITÉ (06_GOVERNANCE)",
      ["Propriétaire métier : service HSE.   Propriétaire technique : data engineer (le groupe).",
       "Classification : sources, RAW, STAGING et CORE confidentiels (worker_id) ; MART et suivi internes ; rapport et dashboard publics (agrégats seulement).",
       "Accès (moindre privilège) : l'EDA et le dashboard lisent seulement les MART et le suivi. Politique documentée, non appliquée techniquement (SQLite).",
       "Lineage : 36 liens source vers cible (lineage.csv).   Dictionnaire enrichi : 148 colonnes.   Rafraîchissement : un run complet après chaque livraison de sources."],
      fond="#FFFFFF", bord=GRIS, couleur_titre=VIOLET_FONCE, gauche=True)

fig.savefig(DOSSIER_ARCHITECTURE / "architecture_finale.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Schéma écrit :", DOSSIER_ARCHITECTURE / "architecture_finale.png")


# ---------------------------------------------------------------------
# Schéma 2 : schéma en étoile (2 faits, 9 dimensions)
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11.7, 8.3))
ax.set_xlim(0, 23.4)
ax.set_ylim(0, 16.6)
ax.axis("off")

ax.text(0.3, 16.2, "Schéma en étoile du Data Warehouse : 2 tables de faits, 9 dimensions",
        fontsize=14, fontweight="bold", color=VIOLET_FONCE, va="center")

Y_BAS, Y_HAUT = 5.4, 11.4        # bas et haut des deux tables de faits


def borne(valeur):
    """Garde le point de départ d'une flèche sur le côté de la table de faits."""
    return max(Y_BAS + 0.5, min(Y_HAUT - 0.5, valeur))


# Faits
boite(ax, 5.2, Y_BAS, 5.0, Y_HAUT - Y_BAS, "fact_incident",
      ["1 ligne = 1 incident", "1 400 lignes", "", "Clés : date_key, hour_key,", "location_key, equipment_key,",
       "worker_key, incident_type_key,", "severity_key", "", "Mesures : incident_count,", "is_serious, is_near_miss,",
       "severity_weight"], fond=ROSE_PALE, bord=FRAMBOISE, couleur_titre=FRAMBOISE, taille_titre=11, taille_texte=8)
boite(ax, 16.0, Y_BAS, 5.6, Y_HAUT - Y_BAS, "fact_safety_observation",
      ["1 ligne = 1 observation", "3 500 lignes", "", "Clés : date_key, hour_key,", "location_key,",
       "observation_type_key,", "reporter_role_key", "", "Mesures : observation_count,", "is_unsafe, is_near_miss"],
      fond=ROSE_PALE, bord=FRAMBOISE, couleur_titre=FRAMBOISE, taille_titre=11, taille_texte=8)

# Dimensions communes (au centre)
ax.text(13.1, 15.2, "3 dimensions communes\naux deux faits", ha="center", va="center", fontsize=9,
        color=VIOLET_FONCE, fontweight="bold")
communes = [("dim_date", ["date_key (AAAAMMJJ)", "301 jours", "mois, jours du mois"], 11.9),
            ("dim_hour", ["hour_key (0 à 23)", "24 heures", "tranche horaire"], 7.2),
            ("dim_location", ["location_key", "25 zones", "area_type, area_name"], 2.5)]
for nom, lignes, yb in communes:
    boite(ax, 11.4, yb, 3.4, 2.4, nom, lignes)
    fleche(ax, (10.2, borne(yb + 1.2)), (11.4, yb + 1.2))
    fleche(ax, (16.0, borne(yb + 1.2)), (14.8, yb + 1.2))

# Dimensions propres aux incidents (à gauche)
gauche = [("dim_equipment", ["equipment_key", "40 engins", "type, home_area"], 12.9),
          ("dim_worker", ["worker_key", "350 travailleurs", "rôle, équipe", "(table confidentielle)"], 9.3),
          ("dim_incident_type", ["incident_type_key", "6 types", "is_near_miss"], 6.0),
          ("dim_severity", ["severity_key", "4 niveaux", "poids, is_serious"], 2.7)]
for nom, lignes, yb in gauche:
    boite(ax, 0.3, yb, 3.7, 2.7, nom, lignes)
    fleche(ax, (5.2, borne(yb + 1.35)), (4.0, yb + 1.35))

# Dimensions propres aux observations (au-dessus et au-dessous du fait)
boite(ax, 16.4, 12.6, 4.8, 2.4, "dim_observation_type", ["observation_type_key", "3 types : SAFE, UNSAFE,", "NEAR_MISS"])
fleche(ax, (18.8, Y_HAUT), (18.8, 12.6))
boite(ax, 16.4, 1.8, 4.8, 2.4, "dim_reporter_role", ["reporter_role_key", "3 rôles : OPERATOR,", "SUPERVISOR, HSE"])
fleche(ax, (18.8, Y_BAS), (18.8, 4.2))

ax.text(0.3, 0.8, "Lecture : chaque flèche part d'une table de faits et pointe vers une dimension qui la décrit "
                  "(clé de substitution entière *_key).\nLes deux faits ne sont jamais joints directement : "
                  "ils se rejoignent seulement par les 3 dimensions communes.",
        fontsize=8.5, color=GRIS, va="center")

fig.savefig(DOSSIER_ETL / "schema_etoile.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Schéma écrit :", DOSSIER_ETL / "schema_etoile.png")
