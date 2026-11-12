"""
Projet 11 : tableau de bord HSE (Streamlit).
Lit uniquement les tables MART du DWH (04_ETL/project_11_dwh.db).
Lancement depuis la racine du projet :  streamlit run 12_DASHBOARD/app.py
"""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

DOSSIER_DASHBOARD = Path(__file__).resolve().parent
BASE_DWH = DOSSIER_DASHBOARD.parent / "04_ETL" / "project_11_dwh.db"
LOGO = DOSSIER_DASHBOARD / "assets" / "logo_ud.jpg"

con = sqlite3.connect(BASE_DWH)

# Couleurs de la charte graphique (voir README)
VIOLET_FONCE = "#4A1D6E"
VIOLET = "#7B3FA0"
ROSE = "#EE82B7"
GRIS_INCOMPLET = "#CFC8D6"
COULEURS_GRAVITE = {"LOW": "#D9C8EA", "MEDIUM": "#A77BC9", "HIGH": "#EE82B7", "CRITICAL": "#9E1F5C"}

st.set_page_config(page_title="Projet 11 : sécurité portuaire", page_icon="⚓", layout="wide")

# ---------------------------------------------------------------------
# Style de la page (couleurs de la charte)
# ---------------------------------------------------------------------
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #4A1D6E 0%, #7B3FA0 100%); }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color: #FFFFFF; }
section[data-testid="stSidebar"] [data-testid="stImage"] img { background: #FFFFFF; border-radius: 14px; padding: 8px; }
.titre-sidebar { color: #EE82B7; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; margin: 14px 0 4px 0; }
.bandeau { background: linear-gradient(90deg, #4A1D6E 0%, #7B3FA0 60%, #EE82B7 100%); border-radius: 16px; padding: 22px 28px; margin-bottom: 22px; }
.bandeau h1 { color: #FFFFFF; font-size: 1.9rem; margin: 0; padding: 0; }
.bandeau p  { color: #EDE4F5; font-size: 0.95rem; margin: 6px 0 0 0; }
.section { color: #4A1D6E; font-size: 1.15rem; font-weight: 700; margin: 8px 0 10px 0; border-left: 5px solid #EE82B7; padding-left: 10px; }
.carte { background: #EDE4F5; border-left: 5px solid #EE82B7; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; min-height: 120px; }
.carte .titre  { color: #4A1D6E; font-size: 0.9rem; font-weight: 600; }
.carte .valeur { color: #7B3FA0; font-size: 2.1rem; font-weight: 700; line-height: 1.3; }
.carte .unite  { color: #6B6375; font-size: 0.8rem; }
.carte.alerte  { background: #FDEEF5; }
.carte.alerte .valeur { color: #9E1F5C; }
.identite { color: #FFFFFF; font-size: 0.88rem; line-height: 1.5; }
.identite b { color: #FFFFFF; }
.stTabs [aria-selected="true"] { color: #9E1F5C; }
.a-venir { background: #FDEEF5; color: #4A1D6E; border-radius: 10px; padding: 12px 16px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Barre latérale : identité du projet et filtres (slicers)
# ---------------------------------------------------------------------
mois_dispo = pd.read_sql_query("SELECT mois FROM mart_incidents_month ORDER BY mois", con)["mois"].tolist()
types_zone = pd.read_sql_query("SELECT DISTINCT area_type FROM mart_incidents_by_area ORDER BY area_type", con)["area_type"].tolist()
equipes = pd.read_sql_query("SELECT DISTINCT shift FROM mart_incident_rate_shift_role ORDER BY shift", con)["shift"].tolist()

with st.sidebar:
    st.image(str(LOGO), width=120)
    st.markdown("""
<div class="identite">
<b>Université de Djibouti</b><br>
Master II Artificial Intelligence &amp; Data Science<br>
Gestion des Données Massives
</div>
<div class="titre-sidebar">PROJET 11</div>
<div class="identite">Port Safety &amp; Incident Analytics<br>Mako Mohamed Aden · Fatouma Soubere Mahamoud</div>
<div class="titre-sidebar">FILTRES</div>
""", unsafe_allow_html=True)

    # Slicer 1 : la période (onglets 1 et 4)
    debut, fin = st.select_slider("Période", options=mois_dispo, value=(mois_dispo[0], mois_dispo[-1]))
    # Slicer 2 : les types de zone (onglet 2)
    zones_choisies = st.multiselect("Types de zone", types_zone, default=types_zone)
    # Slicer 3 : les équipes (onglet 3)
    equipes_choisies = st.multiselect("Équipes", equipes, default=equipes)

    # Si on vide un filtre, on reprend toutes les valeurs (les graphiques ne sont jamais vides)
    if not zones_choisies:
        zones_choisies = types_zone
    if not equipes_choisies:
        equipes_choisies = equipes

    st.caption("Source : tables MART du Data Warehouse (données synthétiques).")

# ---------------------------------------------------------------------
# Bandeau du haut
# ---------------------------------------------------------------------
st.markdown("""
<div class="bandeau">
<h1>Sécurité portuaire : tableau de bord HSE</h1>
<p>Incidents, near-miss et zones à risque du terminal · du 1er janvier au 28 octobre 2026</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Les 8 KPI, sur 2 lignes de 4 cartes
# ---------------------------------------------------------------------
st.markdown('<div class="section">Indicateurs clés</div>', unsafe_allow_html=True)

titres = {
    "KPI1": "Incidents par mois",
    "KPI2": "Incidents graves",
    "KPI3": "Zone la plus à risque",
    "KPI4": "Near-miss",
    "KPI5": "Type le plus fréquent (SPILL)",
    "KPI6": "Groupe le plus exposé",
    "KPI7": "Observations UNSAFE",
    "KPI8": "Total des incidents",
}
kpi_alerte = ["KPI2", "KPI3"]   # fond rose : ce qui doit attirer l'œil

kpi = pd.read_sql_query("SELECT * FROM mart_kpi_summary ORDER BY kpi_id", con)

colonnes = st.columns(4) + st.columns(4)
for colonne, (_, ligne) in zip(colonnes, kpi.iterrows()):
    classe = "carte alerte" if ligne["kpi_id"] in kpi_alerte else "carte"
    valeur = f"{ligne['valeur']:g}".replace(".", ",")
    colonne.markdown(
        f'<div class="{classe}" title="{ligne["libelle"]}">'
        f'<div class="titre">{titres[ligne["kpi_id"]]}</div>'
        f'<div class="valeur">{valeur}</div>'
        f'<div class="unite">{ligne["unite"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------
# Les onglets d'analyse
# ---------------------------------------------------------------------
st.markdown('<div class="section">Analyses</div>', unsafe_allow_html=True)

onglet_temps, onglet_zones, onglet_equipes, onglet_signaux, onglet_qualite = st.tabs(
    ["Évolution mensuelle", "Zones à risque", "Rôles et équipes", "Signaux faibles et types", "Qualité des données"]
)
with onglet_temps:
    col_gauche, col_droite = st.columns([3, 2])

    # Graphique 1 : incidents par mois (octobre incomplet en gris)
    mois = pd.read_sql_query("SELECT * FROM mart_incidents_month ORDER BY mois", con)
    mois = mois[(mois["mois"] >= debut) & (mois["mois"] <= fin)]
    moyenne = mois[mois["mois_complet"] == 1]["nb_incidents"].mean()
    couleurs = [ROSE if complet == 1 else GRIS_INCOMPLET for complet in mois["mois_complet"]]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(mois["mois"].str[5:], mois["nb_incidents"], color=couleurs, label="Incidents")
    ax.bar(mois["mois"].str[5:], mois["nb_graves"], color=VIOLET_FONCE, label="dont graves")
    if pd.notna(moyenne):   # pas de moyenne si la période ne contient que le mois incomplet
        ax.axhline(moyenne, color=VIOLET, linestyle="--", linewidth=1, label=f"Moyenne des mois complets ({moyenne:.0f})")
    ax.set_title("Incidents par mois en 2026 (octobre incomplet, en gris)", color=VIOLET_FONCE, loc="left")
    ax.set_xlabel("Mois")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, mois["nb_incidents"].max() * 1.25)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    col_gauche.pyplot(fig)

    # Graphique 2 : répartition par gravité
    gravite = pd.read_sql_query("SELECT * FROM mart_severity_distribution", con)
    ordre = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    gravite = gravite.set_index("severity").loc[ordre].reset_index()

    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.bar(gravite["severity"], gravite["nb_incidents"], color=[COULEURS_GRAVITE[g] for g in ordre])
    for i, ligne in gravite.iterrows():
        ax.text(i, ligne["nb_incidents"] + 10, f"{ligne['pct']:g} %".replace(".", ","), ha="center", color=VIOLET_FONCE)
    ax.set_ylim(0, gravite["nb_incidents"].max() * 1.15)
    ax.set_title("Répartition par gravité (toute la période)", color=VIOLET_FONCE, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    col_droite.pyplot(fig)

    st.caption("Mai est le pic (171 incidents, 27,5 % de graves). Octobre s'arrête au 28 : il n'est pas comparé aux autres mois.")
with onglet_zones:
    zones = pd.read_sql_query("SELECT * FROM mart_incidents_by_area ORDER BY score_risque DESC", con)

    zones = zones[zones["area_type"].isin(zones_choisies)]   # slicer « Types de zone »
    top = zones.head(10)

    col_gauche, col_droite = st.columns([3, 2])

    # Graphique : top 10 des zones par score de risque (la 1re en framboise)
    couleurs = [COULEURS_GRAVITE["CRITICAL"] if i == 0 else ROSE for i in range(len(top))]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.barh(top["location_id"] + " · " + top["area_type"], top["score_risque"], color=couleurs)
    ax.invert_yaxis()
    for i, score in enumerate(top["score_risque"]):
        ax.text(score + 1, i, f"{score:g}".replace(".", ","), va="center", color=VIOLET_FONCE, fontsize=9)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Score de risque (sur 100)")
    ax.set_title(f"Top {len(top)} des zones les plus à risque", color=VIOLET_FONCE, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    col_gauche.pyplot(fig)

    # Tableau : le détail derrière le score
    detail = top[["location_id", "nb_incidents", "nb_graves", "pct_unsafe", "score_risque"]]
    detail.columns = ["Zone", "Incidents", "Graves", "% UNSAFE", "Score"]
    col_droite.dataframe(detail, hide_index=True, width="stretch")

    st.caption("Score = 50 % incidents graves + 30 % nombre d'incidents + 20 % part d'observations UNSAFE, chaque terme rapporté au maximum. LOC015 (YARD) est la zone la plus à risque.")
with onglet_equipes:
    taux = pd.read_sql_query("SELECT * FROM mart_incident_rate_shift_role", con)
    taux = taux[taux["shift"].isin(equipes_choisies)]   # slicer « Équipes »
    tableau = taux.pivot(index="role", columns="shift", values="incidents_par_travailleur")

    col_gauche, col_droite = st.columns([3, 2])

    # Heatmap : incidents par travailleur, pour chaque rôle et chaque équipe
    fig, ax = plt.subplots(figsize=(7, 4.2))
    image = ax.imshow(tableau, cmap="RdPu")
    ax.set_xticks(range(len(tableau.columns)), [f"Équipe {e}" for e in tableau.columns])
    ax.set_yticks(range(len(tableau.index)), tableau.index)
    for i in range(len(tableau.index)):
        for j in range(len(tableau.columns)):
            v = tableau.iloc[i, j]
            ax.text(j, i, f"{v:.2f}".replace(".", ","), ha="center", va="center",
                    color="white" if v > tableau.values.mean() else VIOLET_FONCE)
    fig.colorbar(image, ax=ax, label="Incidents par travailleur")
    ax.set_title("Incidents par travailleur, selon le rôle et l'équipe", color=VIOLET_FONCE, loc="left")
    col_gauche.pyplot(fig)

    # Tableau : les groupes du plus exposé au moins exposé
    classement = taux.sort_values("incidents_par_travailleur", ascending=False)
    classement = classement[["role", "shift", "nb_incidents", "incidents_par_travailleur"]]
    classement.columns = ["Rôle", "Équipe", "Incidents", "Par travailleur"]
    col_droite.dataframe(classement, hide_index=True, width="stretch")

    st.caption("On divise par le nombre de travailleurs pour comparer des groupes de tailles différentes. Les opérateurs de l'équipe A sont les plus exposés (4,84 incidents par personne).")
with onglet_signaux:
    near_miss = pd.read_sql_query("SELECT * FROM mart_near_miss ORDER BY mois", con)

    near_miss = near_miss[(near_miss["mois"] >= debut) & (near_miss["mois"] <= fin)]

    col_gauche, col_droite = st.columns([3, 2])

    # Graphique 1 : near-miss (barres roses) et incidents graves (ligne violette)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(near_miss["mois"].str[5:], near_miss["near_miss_total"], color=ROSE, label="Near-miss (incidents + observations)")
    ax.plot(near_miss["mois"].str[5:], near_miss["incidents_graves"], color=VIOLET_FONCE, marker="o", label="Incidents graves")
    ax.set_ylim(0, near_miss["near_miss_total"].max() * 1.25)
    ax.set_xlabel("Mois")
    ax.set_title("Near-miss et incidents graves par mois", color=VIOLET_FONCE, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
    col_gauche.pyplot(fig)

    # Graphique 2 : les types d'incidents, du plus fréquent au moins fréquent
    types = pd.read_sql_query("SELECT * FROM mart_recurring_incident_type ORDER BY rang", con)
    couleurs = [COULEURS_GRAVITE["CRITICAL"] if i == 0 else VIOLET for i in range(len(types))]
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.barh(types["incident_type"], types["pct"], color=couleurs)
    ax.invert_yaxis()
    for i, pct in enumerate(types["pct"]):
        ax.text(pct + 0.3, i, f"{pct:g} %".replace(".", ","), va="center", color=VIOLET_FONCE, fontsize=9)
    ax.set_xlim(0, types["pct"].max() * 1.25)
    ax.set_title("Types d'incidents (toute la période)", color=VIOLET_FONCE, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    col_droite.pyplot(fig)

    ratio = near_miss["near_miss_total"].sum() / near_miss["incidents_graves"].sum()
    ratio_texte = f"{ratio:.1f}".replace(".", ",")
    st.caption(f"Sur la période choisie : {ratio_texte} near-miss pour 1 incident grave. Les types sont très proches (15 à 18 %) : aucun ne domine, il faut agir sur tous.")
with onglet_qualite:
    st.markdown("<div class='a-venir'>Statut des règles qualité et dernier run de l'ETL : partie de Mako.</div>", unsafe_allow_html=True)
