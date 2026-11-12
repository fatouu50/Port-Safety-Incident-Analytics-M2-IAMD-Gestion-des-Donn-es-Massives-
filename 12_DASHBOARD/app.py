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
.bandeau { background: #4A1D6E; border-radius: 16px; padding: 22px 28px; margin-bottom: 22px; }
.bandeau h1 { color: #FFFFFF; font-size: 1.9rem; margin: 0; padding: 0; }
.bandeau p  { color: #EDE4F5; font-size: 0.95rem; margin: 6px 0 0 0; }
.section { color: #4A1D6E; font-size: 1.15rem; font-weight: 700; margin: 8px 0 10px 0; }
.carte { background: #EDE4F5; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; min-height: 120px; }
.carte .titre  { color: #4A1D6E; font-size: 0.9rem; font-weight: 600; }
.carte .valeur { color: #7B3FA0; font-size: 2.1rem; font-weight: 700; line-height: 1.3; }
.carte .unite  { color: #6B6375; font-size: 0.8rem; }
.carte.alerte  { background: #FDEEF5; }
.carte.alerte .valeur { color: #9E1F5C; }
.identite { color: #4A1D6E; font-size: 0.9rem; line-height: 1.5; }
.identite b { color: #4A1D6E; }
.a-venir { background: #FDEEF5; color: #4A1D6E; border-radius: 10px; padding: 12px 16px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Barre latérale : identité du projet
# ---------------------------------------------------------------------
with st.sidebar:
    st.image(str(LOGO), width=150)
    st.markdown("""
<div class="identite">
<b>Université de Djibouti</b><br>
Master II Artificial Intelligence &amp; Data Science<br><br>
<b>Gestion des Données Massives</b><br>
Projet 11 : Port Safety &amp; Incident Analytics<br><br>
<b>Groupe</b><br>
Mako Mohamed Aden<br>
Fatouma Soubere Mahamoud
</div>
""", unsafe_allow_html=True)
    st.divider()
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
    ["Évolution mensuelle", "Zones à risque", "Rôles et équipes", "Signaux faibles", "Qualité des données"]
)
with onglet_temps:
    col_gauche, col_droite = st.columns([3, 2])

    # Graphique 1 : incidents par mois (octobre incomplet en gris)
    mois = pd.read_sql_query("SELECT * FROM mart_incidents_month ORDER BY mois", con)
    moyenne = mois[mois["mois_complet"] == 1]["nb_incidents"].mean()
    couleurs = [VIOLET if complet == 1 else GRIS_INCOMPLET for complet in mois["mois_complet"]]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(mois["mois"].str[5:], mois["nb_incidents"], color=couleurs, label="Incidents")
    ax.bar(mois["mois"].str[5:], mois["nb_graves"], color=ROSE, label="dont graves")
    ax.axhline(moyenne, color=VIOLET_FONCE, linestyle="--", linewidth=1, label=f"Moyenne des mois complets ({moyenne:.0f})")
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
    ax.set_title("Répartition par gravité", color=VIOLET_FONCE, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    col_droite.pyplot(fig)

    st.caption("Mai est le pic (171 incidents, 27,5 % de graves). Octobre s'arrête au 28 : il n'est pas comparé aux autres mois.")
with onglet_zones:
    zones = pd.read_sql_query("SELECT * FROM mart_incidents_by_area ORDER BY score_risque DESC", con)

    # Filtre : choisir un type de zone (ou toutes)
    col_filtre, _ = st.columns([1, 3])
    choix = col_filtre.selectbox("Type de zone", ["Toutes"] + sorted(zones["area_type"].unique()))
    if choix != "Toutes":
        zones = zones[zones["area_type"] == choix]
    top = zones.head(10)

    col_gauche, col_droite = st.columns([3, 2])

    # Graphique : top 10 des zones par score de risque (la 1re en framboise)
    couleurs = [COULEURS_GRAVITE["CRITICAL"] if i == 0 else VIOLET for i in range(len(top))]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.barh(top["location_id"] + " · " + top["area_type"], top["score_risque"], color=couleurs)
    ax.invert_yaxis()
    for i, score in enumerate(top["score_risque"]):
        ax.text(score + 1, i, f"{score:g}".replace(".", ","), va="center", color=VIOLET_FONCE, fontsize=9)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Score de risque (sur 100)")
    ax.set_title(f"Top {len(top)} des zones les plus à risque ({choix.lower()})", color=VIOLET_FONCE, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    col_gauche.pyplot(fig)

    # Tableau : le détail derrière le score
    detail = top[["location_id", "nb_incidents", "nb_graves", "pct_unsafe", "score_risque"]]
    detail.columns = ["Zone", "Incidents", "Graves", "% UNSAFE", "Score"]
    col_droite.dataframe(detail, hide_index=True, width="stretch")

    st.caption("Score = 50 % volume d'incidents + 30 % incidents graves + 20 % part d'observations UNSAFE, chaque terme rapporté au maximum. LOC015 (YARD) est la zone la plus à risque.")
with onglet_equipes:
    st.markdown("<div class='a-venir'>Heatmap rôle × équipe : à venir.</div>", unsafe_allow_html=True)
with onglet_signaux:
    st.markdown("<div class='a-venir'>Near-miss et incidents graves : à venir.</div>", unsafe_allow_html=True)
with onglet_qualite:
    st.markdown("<div class='a-venir'>Statut des règles qualité et dernier run de l'ETL : partie de Mako.</div>", unsafe_allow_html=True)
