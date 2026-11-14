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

# Police plus étroite que la police par défaut : le texte tient dans les boîtes (repli sur la police par défaut)
plt.rcParams["font.family"] = ["Segoe UI", "Arial", "DejaVu Sans"]

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
          taille_titre=8.5, taille_texte=7, gauche=False):
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
fig, ax = plt.subplots(figsize=(9.4, 6.5))   # taille réelle sur une page A4 paysage (le rapport l'imprime sans l'agrandir)
ax.set_xlim(0, 23.4)
ax.set_ylim(1.9, 16.6)
ax.axis("off")

ax.text(0.3, 16.2, "Architecture finale : des fichiers sources aux décisions du service HSE",
        fontsize=12, fontweight="bold", color=VIOLET_FONCE, va="center")

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
                                   "DQ01 et DQ12", "", "confidentiel"])
boite(ax, 8.3, y, 2.95, h, "STAGING", ["nettoyage", "et contrôles", "", "5 tables stg_*", "+ stg_rejects", "0 rejet", "",
                                       "DQ02 à DQ07", "", "confidentiel"])
boite(ax, 11.7, y, 2.95, h, "CORE", ["schéma en étoile", "", "9 dimensions", "2 tables de faits", "1 400 incidents",
                                     "3 500 observations", "", "DQ08", "", "confidentiel"])
boite(ax, 15.1, y, 2.95, h, "MART", ["tables prêtes", "pour l'analyse", "", "7 tables mart_*", "8 KPI, 75 lignes",
                                     "aucun worker_id", "", "DQ09 et DQ10", "", "interne"], fond=ROSE_PALE, bord=ROSE)
for x_depart, x_arrivee in [(3.9, 4.9), (7.85, 8.3), (11.25, 11.7), (14.65, 15.1)]:
    fleche(ax, (x_depart, 11.9), (x_arrivee, 11.9))

# Consommation
boite(ax, 19.0, 12.5, 4.1, 2.5, "EDA (Python)", ["07_EDA/eda_projet11.ipynb", "6 graphiques interprétés", "lit les MART seulement"],
      fond="#FFFFFF", bord=VIOLET)
boite(ax, 19.0, 9.2, 4.1, 2.9, "DASHBOARD", ["Streamlit, une seule page", "12_DASHBOARD/app.py", "8 cartes KPI, 6 graphiques,",
                                           "section Qualité des données", "lit les MART et le suivi"], fond="#FFFFFF", bord=VIOLET)
fleche(ax, (18.05, 12.6), (19.0, 13.5))
fleche(ax, (18.05, 11.2), (19.0, 10.6))

# Décisions HSE
boite(ax, 19.0, 4.9, 4.1, 3.7, "DÉCISIONS HSE", ["Où : rondes en priorité", "sur LOC015 et LOC014", "Quand : cause du pic de mai",
                                                "Qui : briefings opérateurs A", "Gravité : objectif sur les", "incidents graves (22,3 %)",
                                                "Signaux faibles : near-miss"],
      fond=ROSE_PALE, bord=FRAMBOISE, couleur_titre=FRAMBOISE)
fleche(ax, (21.05, 9.2), (21.05, 8.6), couleur=FRAMBOISE)

# HDFS
boite(ax, 0.3, 4.9, 10.0, 3.1, "ARCHIVE HDFS : /port_exam/project_11/archive",
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
boite(ax, 10.75, 4.9, 7.65, 2.8, "QUALITÉ ET SUIVI DU PIPELINE",
      ["12 règles (DQ01 à DQ12), 39 contrôles : dq_results",
       "etl_run_log : date, durée, volumes, statut du run",
       "stg_rejects : chaque ligne refusée et sa raison",
       "test_etl.py : idempotence, 11 anomalies = 11 rejets,",
       "panne simulée et rollback"],
      fond="#F3FAF6", bord=VERT, couleur_titre=VERT, gauche=True)
fleche(ax, (18.4, 6.8), (19.0, 9.6), couleur=VERT, style="--", courbe=0.15)

# Gouvernance
boite(ax, 0.3, 2.1, 22.8, 2.3, "GOUVERNANCE ET SÉCURITÉ (06_GOVERNANCE)",
      ["Propriétaire métier : service HSE.   Propriétaire technique : data engineer (le groupe).",
       "Classification : sources, RAW, STAGING et CORE confidentiels (worker_id) ; MART et suivi internes ; rapport et dashboard publics.",
       "Accès (moindre privilège) : l'EDA et le dashboard lisent seulement les MART et le suivi (politique écrite, non appliquée par SQLite).",
       "Lineage : 36 liens source vers cible.   Dictionnaire enrichi : 148 colonnes.   Rafraîchissement : un run complet à chaque livraison de sources."],
      fond="#FFFFFF", bord=GRIS, couleur_titre=VIOLET_FONCE, gauche=True)

fig.savefig(DOSSIER_ARCHITECTURE / "architecture_finale.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Schéma écrit :", DOSSIER_ARCHITECTURE / "architecture_finale.png")


# ---------------------------------------------------------------------
# Schéma 2 : schéma en étoile (2 faits, 9 dimensions)
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.4, 6.5))
ax.set_xlim(0, 23.4)
ax.set_ylim(0, 16.6)
ax.axis("off")

ax.text(0.3, 16.2, "Schéma en étoile du Data Warehouse : 2 tables de faits, 9 dimensions",
        fontsize=12, fontweight="bold", color=VIOLET_FONCE, va="center")

Y_BAS, Y_HAUT = 5.4, 11.4        # bas et haut des deux tables de faits


def borne(valeur):
    """Garde le point de départ d'une flèche sur le côté de la table de faits."""
    return max(Y_BAS + 0.5, min(Y_HAUT - 0.5, valeur))


# Faits
boite(ax, 5.2, Y_BAS, 5.0, Y_HAUT - Y_BAS, "fact_incident",
      ["1 ligne = 1 incident", "1 400 lignes", "", "Clés : date_key, hour_key,", "location_key, equipment_key,",
       "worker_key, incident_type_key,", "severity_key", "", "Mesures : incident_count,", "is_serious, is_near_miss,",
       "severity_weight"], fond=ROSE_PALE, bord=FRAMBOISE, couleur_titre=FRAMBOISE, taille_titre=9.5, taille_texte=7)
boite(ax, 16.0, Y_BAS, 5.6, Y_HAUT - Y_BAS, "fact_safety_observation",
      ["1 ligne = 1 observation", "3 500 lignes", "", "Clés : date_key, hour_key,", "location_key,",
       "observation_type_key,", "reporter_role_key", "", "Mesures : observation_count,", "is_unsafe, is_near_miss"],
      fond=ROSE_PALE, bord=FRAMBOISE, couleur_titre=FRAMBOISE, taille_titre=9.5, taille_texte=7)

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
        fontsize=7.5, color=GRIS, va="center")

fig.savefig(DOSSIER_ETL / "schema_etoile.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Schéma écrit :", DOSSIER_ETL / "schema_etoile.png")


# ---------------------------------------------------------------------
# Schéma 3 : architecture simplifiée pour la présentation orale (6 blocs)
#   -> 09_PRESENTATION/architecture_simplifiee.png (n'écrase pas architecture_finale.png du rapport)
# ---------------------------------------------------------------------
DOSSIER_PRESENTATION = DOSSIER_ARCHITECTURE.parent / "09_PRESENTATION"
FOND_SLIDE = "#F7F2FB"

fig, ax = plt.subplots(figsize=(12.2, 5.0))
ax.set_xlim(0, 24.4)
ax.set_ylim(0, 10)
ax.axis("off")


def gros_bloc(x, y, l, h, titre, mot, fond, bord, couleur_texte="#FFFFFF", couleur_mot="#FFFFFF"):
    ax.add_patch(FancyBboxPatch((x, y), l, h, boxstyle="round,pad=0.05,rounding_size=0.5",
                                facecolor=fond, edgecolor=bord, linewidth=2))
    ax.text(x + l / 2, y + h * 0.60, titre, ha="center", va="center", fontsize=17, fontweight="bold", color=couleur_texte)
    ax.text(x + l / 2, y + h * 0.27, mot, ha="center", va="center", fontsize=14, color=couleur_mot)


def grosse_fleche(depart, arrivee, couleur=VIOLET_FONCE, style="-", courbe=0.0):
    ax.annotate("", xy=arrivee, xytext=depart,
                arrowprops=dict(arrowstyle="simple,head_width=1.1,head_length=1.0,tail_width=0.45", color=couleur,
                                linestyle=style, connectionstyle=f"arc3,rad={courbe}", shrinkA=3, shrinkB=3))


gros_bloc(0.2, 3.6, 4.2, 2.8, "Sources", "5 fichiers CSV", "#FFFFFF", GRIS, VIOLET_FONCE, GRIS)
gros_bloc(6.0, 3.6, 5.8, 2.8, "Data Warehouse", "4 couches", VIOLET_FONCE, VIOLET_FONCE)
gros_bloc(6.0, 0.1, 5.8, 2.2, "Archive HDFS", "historique brut", VIOLET, VIOLET)
gros_bloc(13.4, 6.9, 4.8, 2.8, "EDA", "6 graphiques", ROSE, ROSE, VIOLET_FONCE, VIOLET_FONCE)
gros_bloc(13.4, 3.6, 4.8, 2.8, "Dashboard", "en ligne", VIOLET, VIOLET)
gros_bloc(19.8, 3.6, 4.4, 2.8, "Décisions HSE", "agir", FRAMBOISE, FRAMBOISE)

grosse_fleche((4.5, 5.0), (5.9, 5.0))
grosse_fleche((2.3, 3.5), (5.9, 1.4), VIOLET, "-", 0.25)
grosse_fleche((11.9, 6.0), (13.3, 8.0), ROSE, "-", -0.1)
grosse_fleche((11.9, 5.0), (13.3, 5.0))
grosse_fleche((18.3, 5.0), (19.7, 5.0), FRAMBOISE)
grosse_fleche((18.3, 8.2), (22.0, 6.5), FRAMBOISE, "-", -0.25)

fig.savefig(DOSSIER_PRESENTATION / "architecture_simplifiee.png", dpi=200, bbox_inches="tight", facecolor=FOND_SLIDE)
plt.close(fig)
print("Schéma écrit :", DOSSIER_PRESENTATION / "architecture_simplifiee.png")


# ---------------------------------------------------------------------
# Schéma 4 : schéma en étoile simplifié pour la présentation orale (noms seulement)
#   -> 09_PRESENTATION/schema_etoile_simplifie.png (n'écrase pas schema_etoile.png du rapport)
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12.2, 5.3))
ax.set_xlim(0, 16.6)
ax.set_ylim(-0.3, 8.4)
ax.axis("off")


def bloc_nom(x, y, l, h, nom, fond_, bord, couleur, taille=14):
    ax.add_patch(FancyBboxPatch((x, y), l, h, boxstyle="round,pad=0.04,rounding_size=0.25",
                                facecolor=fond_, edgecolor=bord, linewidth=2, zorder=3))
    ax.text(x + l / 2, y + h / 2, nom, ha="center", va="center", fontsize=taille, fontweight="bold", color=couleur, zorder=4)


def trait(p1, p2, couleur=VIOLET):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=couleur, lw=2, zorder=1)


X_FI, X_FO, Y_F, L_F, H_F = 3.9, 9.9, 3.4, 2.2, 1.6
centre_fi = (X_FI, Y_F + H_F / 2)
centre_fo = (X_FO + L_F, Y_F + H_F / 2)
# dimensions propres aux incidents (à gauche)
for i, nom in enumerate(["dim_equipment", "dim_worker", "dim_incident_type", "dim_severity"]):
    y = 6.9 - i * 2.3
    trait((3.1, y + 0.6), (X_FI, Y_F + H_F / 2))
    bloc_nom(0.1, y, 3.0, 1.2, nom, LAVANDE, VIOLET, VIOLET_FONCE)
# dimensions communes (au milieu, en rose) reliées aux deux faits
for nom, y in zip(["dim_date", "dim_hour", "dim_location"], [6.9, 3.6, 0.3]):
    trait((6.8, y + 0.6), (X_FI + L_F, Y_F + H_F / 2))
    trait((9.2, y + 0.6), (X_FO, Y_F + H_F / 2))
    bloc_nom(6.8, y, 2.4, 1.2, nom, ROSE, ROSE, VIOLET_FONCE)
# dimensions propres aux observations (à droite)
for nom, y in zip(["dim_observation_type", "dim_reporter_role"], [5.6, 1.6]):
    trait((X_FO + L_F, Y_F + H_F / 2), (12.9, y + 0.6))
    bloc_nom(12.9, y, 3.6, 1.2, nom, LAVANDE, VIOLET, VIOLET_FONCE, 13)
bloc_nom(X_FI, Y_F, L_F, H_F, "fact_incident", FRAMBOISE, FRAMBOISE, "#FFFFFF", 15)
bloc_nom(X_FO, Y_F, L_F, H_F, "fact_safety_\nobservation", FRAMBOISE, FRAMBOISE, "#FFFFFF", 15)

fig.savefig(DOSSIER_PRESENTATION / "schema_etoile_simplifie.png", dpi=200, bbox_inches="tight", facecolor=FOND_SLIDE)
plt.close(fig)
print("Schéma écrit :", DOSSIER_PRESENTATION / "schema_etoile_simplifie.png")
