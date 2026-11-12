"""
Projet 11 : tableau de bord HSE (Streamlit).
Lit uniquement les tables MART du DWH (04_ETL/project_11_dwh.db).
Lancement depuis la racine du projet :  streamlit run 12_DASHBOARD/app.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER_DASHBOARD = Path(__file__).resolve().parent
BASE_DWH = DOSSIER_DASHBOARD.parent / "04_ETL" / "project_11_dwh.db"
LOGO = DOSSIER_DASHBOARD / "assets" / "logo_ud.jpg"

con = sqlite3.connect(BASE_DWH)

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
.carte { background: #EDE4F5; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; height: 120px; }
.carte .titre  { color: #4A1D6E; font-size: 0.9rem; font-weight: 600; }
.carte .valeur { color: #7B3FA0; font-size: 2.1rem; font-weight: 700; line-height: 1.3; }
.carte .unite  { color: #6B6375; font-size: 0.8rem; }
.carte.alerte  { background: #FDEEF5; }
.carte.alerte .valeur { color: #9E1F5C; }
.identite { color: #4A1D6E; font-size: 0.9rem; line-height: 1.5; }
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
# Les onglets d'analyse (les graphiques arrivent aux étapes suivantes)
# ---------------------------------------------------------------------
st.markdown('<div class="section">Analyses</div>', unsafe_allow_html=True)

onglet_temps, onglet_zones, onglet_equipes, onglet_signaux, onglet_qualite = st.tabs(
    ["Évolution mensuelle", "Zones à risque", "Rôles et équipes", "Signaux faibles", "Qualité des données"]
)
with onglet_temps:
    st.markdown("<div class='a-venir'>Tendance mensuelle et répartition par gravité : étape suivante.</div>", unsafe_allow_html=True)
with onglet_zones:
    st.markdown("<div class='a-venir'>Classement des zones par score de risque : à venir.</div>", unsafe_allow_html=True)
with onglet_equipes:
    st.markdown("<div class='a-venir'>Heatmap rôle × équipe : à venir.</div>", unsafe_allow_html=True)
with onglet_signaux:
    st.markdown("<div class='a-venir'>Near-miss et incidents graves : à venir.</div>", unsafe_allow_html=True)
with onglet_qualite:
    st.markdown("<div class='a-venir'>Statut des règles qualité et dernier run de l'ETL : partie de Mako.</div>", unsafe_allow_html=True)
