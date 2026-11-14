"""
Projet 11 : tableau de bord HSE (Streamlit).
Lit uniquement les tables MART du DWH (04_ETL/project_11_dwh.db), plus le suivi qualité (en bas de page).
Si la base n'existe pas, elle est construite par 04_ETL/etl_pipeline.py au démarrage.
Lancement depuis la racine du projet :  streamlit run 12_DASHBOARD/app.py
"""
import base64
import sqlite3
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

DOSSIER_DASHBOARD = Path(__file__).resolve().parent
BASE_DWH = DOSSIER_DASHBOARD.parent / "04_ETL" / "project_11_dwh.db"
PIPELINE = DOSSIER_DASHBOARD.parent / "04_ETL" / "etl_pipeline.py"
LOGO = DOSSIER_DASHBOARD / "assets" / "logo_ud.jpg"

st.set_page_config(page_title="Projet 11 : sécurité portuaire", page_icon="⚓", layout="wide",
                   initial_sidebar_state="collapsed")


# Si la base n'existe pas (premier lancement, Streamlit Cloud), on la construit avec le pipeline.
# Ce test doit venir avant sqlite3.connect, qui créerait sinon un fichier vide.
# Une base ne contenant que le journal d'un échec (sans tables MART) compte comme absente.
def base_prete():
    if not BASE_DWH.exists():
        return False
    test = sqlite3.connect(f"file:{BASE_DWH.as_posix()}?mode=ro", uri=True)
    try:
        return test.execute("SELECT 1 FROM sqlite_master WHERE name = 'mart_kpi_summary'").fetchone() is not None
    finally:
        test.close()


if not base_prete():
    with st.spinner("Première ouverture : construction du Data Warehouse (environ 2 s)..."):
        resultat = subprocess.run([sys.executable, str(PIPELINE)], capture_output=True, text=True)
    if resultat.returncode != 0 or not base_prete():
        st.error("La construction du Data Warehouse a échoué.")
        st.code(resultat.stdout[-1500:] + resultat.stderr[-1500:])
        st.stop()

con = sqlite3.connect(BASE_DWH)

# Couleurs de la charte graphique (voir README)
VIOLET_FONCE = "#4A1D6E"
VIOLET = "#7B3FA0"
ROSE = "#EE82B7"
FRAMBOISE = "#9E1F5C"
GRIS_INCOMPLET = "#CFC8D6"
COULEURS_GRAVITE = {"LOW": "#D9C8EA", "MEDIUM": "#A77BC9", "HIGH": "#EE82B7", "CRITICAL": "#9E1F5C"}

# Style commun à tous les graphiques matplotlib
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#CFC8D6", "axes.labelcolor": VIOLET_FONCE,
                     "xtick.color": "#6B6375", "ytick.color": "#6B6375"})

# ---------------------------------------------------------------------
# Style de la page
# ---------------------------------------------------------------------
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
.stApp { background: #F7F2FB; }
.block-container { padding-top: 1.2rem; max-width: 1400px; }
.bandeau { background: linear-gradient(90deg, #4A1D6E 0%, #7B3FA0 60%, #EE82B7 100%); border-radius: 16px;
           padding: 14px 24px; display: flex; align-items: center; gap: 18px; margin-bottom: 14px; }
.bandeau img { height: 66px; background: #FFFFFF; border-radius: 10px; padding: 4px; }
.bandeau h1 { color: #FFFFFF; font-size: 1.6rem; margin: 0; padding: 0; letter-spacing: 0.5px; }
.bandeau p  { color: #FDEEF5; font-size: 0.85rem; margin: 2px 0 0 0; }
.carte { background: #FFFFFF; border: 1px solid #E4D6EF; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; }
.carte .ligne { display: flex; align-items: center; gap: 14px; }
.carte.alerte { background: #FDEEF5; }
.icone { width: 48px; height: 48px; min-width: 48px; border-radius: 50%; background: #4A1D6E;
         display: flex; align-items: center; justify-content: center; }
.carte.alerte .icone { background: #9E1F5C; }
.carte .titre  { color: #4A1D6E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.carte .valeur { color: #7B3FA0; font-size: 1.7rem; font-weight: 700; line-height: 1.2; }
.carte.alerte .valeur { color: #9E1F5C; }
.carte .unite  { color: #6B6375; font-size: 0.75rem; }
.titre-graphe { color: #4A1D6E; font-size: 0.85rem; font-weight: 700; text-transform: uppercase;
                text-align: center; margin-bottom: 4px; }
.titre-partie { color: #FFFFFF; background: #4A1D6E; border-radius: 10px; padding: 8px 16px; font-weight: 700;
                text-transform: uppercase; text-align: center; margin-top: 18px; }
.titre-filtre { color: #4A1D6E; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .titre-graphe),
[data-testid="stVerticalBlock"]:has(> [data-testid="stHorizontalBlock"] .titre-filtre) { background: #FFFFFF; border-radius: 14px; }
[data-testid="stButtonGroup"] button { background: #FFFFFF; border-color: #E4D6EF; }
[data-testid="stButtonGroup"] button p { color: #6B6375; }
[data-testid="stButtonGroup"] button[aria-pressed="true"] { background: #EE82B7 !important; border-color: #EE82B7 !important; }
[data-testid="stButtonGroup"] button[aria-pressed="true"] p { color: #4A1D6E; font-weight: 600; }
.section { color: #4A1D6E; font-size: 1.05rem; font-weight: 700; margin: 14px 0 10px 0; border-left: 5px solid #EE82B7; padding-left: 10px; }
.a-venir { background: #FDEEF5; color: #4A1D6E; border-radius: 10px; padding: 12px 16px; }
</style>
""", unsafe_allow_html=True)

# Petites icônes blanches (SVG) pour les cartes KPI
ICONES = {
    "KPI1": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><rect x='3' y='5' width='18' height='16' rx='2'/><path d='M3 10h18M8 3v4M16 3v4'/></svg>",
    "KPI2": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><path d='M12 3l10 18H2z'/><path d='M12 10v5M12 18v.5'/></svg>",
    "KPI3": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><path d='M12 22s7-7 7-12a7 7 0 0 0-14 0c0 5 7 12 7 12z'/><circle cx='12' cy='10' r='2.5'/></svg>",
    "KPI4": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><path d='M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z'/><circle cx='12' cy='12' r='3'/></svg>",
    "KPI5": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><path d='M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z'/></svg>",
    "KPI6": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><circle cx='9' cy='8' r='3'/><circle cx='17' cy='9' r='2.5'/><path d='M3 20c0-3 3-5 6-5s6 2 6 5M15 15c3 0 6 1.5 6 4'/></svg>",
    "KPI7": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><rect x='5' y='4' width='14' height='17' rx='2'/><path d='M9 4V2h6v2M9 11l6 6M15 11l-6 6'/></svg>",
    "KPI8": "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><path d='M4 20V10M10 20V4M16 20v-8M22 20H2'/></svg>",
}

# ---------------------------------------------------------------------
# Bandeau du haut : logo, titre, identité du projet
# ---------------------------------------------------------------------
logo_base64 = base64.b64encode(LOGO.read_bytes()).decode()
st.markdown(f"""
<div class="bandeau">
<img src="data:image/jpeg;base64,{logo_base64}">
<div>
<h1>SÉCURITÉ PORTUAIRE : TABLEAU DE BORD HSE</h1>
<p>Université de Djibouti · Master II Artificial Intelligence &amp; Data Science · Gestion des Données Massives</p>
<p>Projet 11 : Port Safety &amp; Incident Analytics · Mako Mohamed Aden, Fatouma Soubere Mahamoud · données du 1er janvier au 28 octobre 2026</p>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Les filtres (slicers), dans une barre sous le bandeau
# ---------------------------------------------------------------------
mois_dispo = pd.read_sql_query("SELECT mois FROM mart_incidents_month ORDER BY mois", con)["mois"].tolist()
types_zone = pd.read_sql_query("SELECT DISTINCT area_type FROM mart_incidents_by_area ORDER BY area_type", con)["area_type"].tolist()
equipes = pd.read_sql_query("SELECT DISTINCT shift FROM mart_incident_rate_shift_role ORDER BY shift", con)["shift"].tolist()

with st.container(border=True):
    filtre_1, filtre_2, filtre_3 = st.columns([2, 3, 1.5])
    with filtre_1:
        st.markdown('<div class="titre-filtre">Période</div>', unsafe_allow_html=True)
        debut, fin = st.select_slider("Période", options=mois_dispo, value=(mois_dispo[0], mois_dispo[-1]),
                                      label_visibility="collapsed")
    with filtre_2:
        st.markdown('<div class="titre-filtre">Types de zone</div>', unsafe_allow_html=True)
        zones_choisies = st.pills("Types de zone", types_zone, selection_mode="multi", default=types_zone,
                                  label_visibility="collapsed")
    with filtre_3:
        st.markdown('<div class="titre-filtre">Équipes</div>', unsafe_allow_html=True)
        equipes_choisies = st.pills("Équipes", equipes, selection_mode="multi", default=equipes,
                                    label_visibility="collapsed")

# Si on vide un filtre, on reprend toutes les valeurs (les graphiques ne sont jamais vides)
if not zones_choisies:
    zones_choisies = types_zone
if not equipes_choisies:
    equipes_choisies = equipes

# ---------------------------------------------------------------------
# Les cartes KPI
# ---------------------------------------------------------------------
titres = {
    "KPI1": "Incidents par mois", "KPI2": "Incidents graves", "KPI3": "Zone la plus à risque",
    "KPI4": "Near-miss", "KPI5": "Type le plus fréquent (SPILL)", "KPI6": "Groupe le plus exposé",
    "KPI7": "Observations UNSAFE", "KPI8": "Total des incidents",
}
kpi_alerte = ["KPI2", "KPI3"]   # icône et valeur framboise : ce qui doit attirer l'œil
kpi = pd.read_sql_query("SELECT * FROM mart_kpi_summary ORDER BY kpi_id", con).set_index("kpi_id")


def carte_kpi(colonne, kpi_id):
    """Affiche une carte : icône à gauche, titre, valeur et unité à droite."""
    ligne = kpi.loc[kpi_id]
    classe = "carte alerte" if kpi_id in kpi_alerte else "carte"
    valeur = f"{ligne['valeur']:g}".replace(".", ",")
    colonne.markdown(
        f'<div class="{classe}" title="{ligne["libelle"]}"><div class="ligne">'
        f'<div class="icone">{ICONES[kpi_id]}</div>'
        f'<div><div class="titre">{titres[kpi_id]}</div>'
        f'<div class="valeur">{valeur}</div>'
        f'<div class="unite">{ligne["unite"]}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


for colonne, kpi_id in zip(st.columns(4), ["KPI1", "KPI2", "KPI3", "KPI4"]):
    carte_kpi(colonne, kpi_id)

# ---------------------------------------------------------------------
# Ligne 1 : évolution mensuelle, near-miss, gravité
# ---------------------------------------------------------------------
case_1, case_2, case_3 = st.columns(3)

mois = pd.read_sql_query("SELECT * FROM mart_incidents_month ORDER BY mois", con)
mois = mois[(mois["mois"] >= debut) & (mois["mois"] <= fin)]          # slicer « Période »
near_miss = pd.read_sql_query("SELECT * FROM mart_near_miss ORDER BY mois", con)
near_miss = near_miss[(near_miss["mois"] >= debut) & (near_miss["mois"] <= fin)]

with case_1.container(border=True):
    st.markdown('<div class="titre-graphe">Incidents par mois</div>', unsafe_allow_html=True)
    moyenne = mois[mois["mois_complet"] == 1]["nb_incidents"].mean()
    couleurs = [ROSE if complet == 1 else GRIS_INCOMPLET for complet in mois["mois_complet"]]
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.bar(mois["mois"].str[5:], mois["nb_incidents"], color=couleurs, label="Incidents")
    ax.bar(mois["mois"].str[5:], mois["nb_graves"], color=VIOLET_FONCE, label="dont graves")
    if pd.notna(moyenne):   # pas de moyenne si la période ne contient que le mois incomplet
        ax.axhline(moyenne, color=VIOLET, linestyle="--", linewidth=1, label=f"Moyenne ({moyenne:.0f})")
    ax.set_ylim(0, mois["nb_incidents"].max() * 1.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper left")
    st.pyplot(fig)
    st.caption("Octobre (gris) s'arrête au 28 : incomplet.")

with case_2.container(border=True):
    st.markdown('<div class="titre-graphe">Near-miss et incidents graves</div>', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.plot(near_miss["mois"].str[5:], near_miss["near_miss_total"], color=ROSE, marker="o", linewidth=2, label="Near-miss")
    ax.plot(near_miss["mois"].str[5:], near_miss["incidents_graves"], color=VIOLET_FONCE, marker="o", linewidth=2, label="Incidents graves")
    ax.set_ylim(0, near_miss["near_miss_total"].max() * 1.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper left")
    st.pyplot(fig)
    ratio = near_miss["near_miss_total"].sum() / near_miss["incidents_graves"].sum()
    st.caption(f"{ratio:.1f}".replace(".", ",") + " near-miss pour 1 incident grave sur la période.")

with case_3.container(border=True):
    st.markdown('<div class="titre-graphe">Répartition par gravité</div>', unsafe_allow_html=True)
    gravite = pd.read_sql_query("SELECT * FROM mart_severity_distribution", con)
    ordre = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    gravite = gravite.set_index("severity").loc[ordre].reset_index()
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.pie(gravite["nb_incidents"], colors=[COULEURS_GRAVITE[g] for g in ordre], startangle=90,
           counterclock=False, wedgeprops={"width": 0.38, "edgecolor": "white"})
    etiquettes = [f"{g}  {p:g} %".replace(".", ",") for g, p in zip(gravite["severity"], gravite["pct"])]
    ax.legend(etiquettes, frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1, 0.5))
    st.pyplot(fig)
    st.caption("Toute la période. Graves = HIGH + CRITICAL.")

# ---------------------------------------------------------------------
# Ligne 2 : zones à risque, rôles et équipes, types d'incidents
# ---------------------------------------------------------------------
case_4, case_5, case_6 = st.columns(3)

with case_4.container(border=True):
    st.markdown('<div class="titre-graphe">Top 10 des zones à risque</div>', unsafe_allow_html=True)
    zones = pd.read_sql_query("SELECT * FROM mart_incidents_by_area ORDER BY score_risque DESC", con)
    zones = zones[zones["area_type"].isin(zones_choisies)]          # slicer « Types de zone »
    top = zones.head(10)
    couleurs = [FRAMBOISE if i == 0 else ROSE for i in range(len(top))]
    fig, ax = plt.subplots(figsize=(5, 3.6))
    ax.barh(top["location_id"] + " · " + top["area_type"], top["score_risque"], color=couleurs)
    ax.invert_yaxis()
    for i, score in enumerate(top["score_risque"]):
        ax.text(score + 1, i, f"{score:g}".replace(".", ","), va="center", color=VIOLET_FONCE, fontsize=8)
    ax.set_xlim(0, 112)
    ax.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig)
    st.caption("Score /100 : 50 % graves, 30 % volume, 20 % UNSAFE.")

with case_5.container(border=True):
    st.markdown('<div class="titre-graphe">Incidents par travailleur</div>', unsafe_allow_html=True)
    taux = pd.read_sql_query("SELECT * FROM mart_incident_rate_shift_role", con)
    taux = taux[taux["shift"].isin(equipes_choisies)]               # slicer « Équipes »
    tableau = taux.pivot(index="role", columns="shift", values="incidents_par_travailleur")
    fig, ax = plt.subplots(figsize=(5, 3.6))
    ax.imshow(tableau, cmap="RdPu", aspect="auto")
    ax.set_xticks(range(len(tableau.columns)), [f"Équipe {e}" for e in tableau.columns])
    ax.set_yticks(range(len(tableau.index)), tableau.index)
    for i in range(len(tableau.index)):
        for j in range(len(tableau.columns)):
            v = tableau.iloc[i, j]
            ax.text(j, i, f"{v:.2f}".replace(".", ","), ha="center", va="center",
                    color="white" if v > tableau.values.mean() else VIOLET_FONCE)
    st.pyplot(fig)
    st.caption("Incidents divisés par le nombre de travailleurs du groupe.")

with case_6.container(border=True):
    st.markdown('<div class="titre-graphe">Types d\'incidents</div>', unsafe_allow_html=True)
    types = pd.read_sql_query("SELECT * FROM mart_recurring_incident_type ORDER BY rang", con)
    fig, ax = plt.subplots(figsize=(5, 3.6))
    couleurs = [FRAMBOISE if i == 0 else VIOLET for i in range(len(types))]
    ax.bar(types["incident_type"], types["nb_incidents"], color=couleurs)
    for i, (n, pct) in enumerate(zip(types["nb_incidents"], types["pct"])):
        ax.text(i, n + 4, f"{pct:g} %".replace(".", ","), ha="center", color=VIOLET_FONCE, fontsize=8)
    ax.set_ylim(0, types["nb_incidents"].max() * 1.15)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig)
    st.caption("Toute la période. Les 6 types sont proches : aucun ne domine.")

# ---------------------------------------------------------------------
# Bande du bas : les 4 autres KPI
# ---------------------------------------------------------------------
for colonne, kpi_id in zip(st.columns(4), ["KPI5", "KPI6", "KPI7", "KPI8"]):
    carte_kpi(colonne, kpi_id)


# =====================================================================
# Qualité des données (partie de Mako) : règles DQ, rejets, dernier run de l'ETL
# =====================================================================
st.markdown('<div class="titre-partie">Qualité des données</div>', unsafe_allow_html=True)

# Couleurs des statuts qualité (OK et ALERTE : charte ; ECHEC : framboise ; REJETS : violet)
COULEURS_STATUT = {"OK": "#2E8B57", "ALERTE": "#D99A1B", "ECHEC": "#9E1F5C", "REJETS": "#7B3FA0"}
GRAVITE_STATUT = ["OK", "REJETS", "ALERTE", "ECHEC"]   # du moins grave au plus grave

# Lecture seule (SELECT) : jamais la colonne « record » de stg_rejects (elle contient le worker_id)
dq = pd.read_sql_query(
    "SELECT regle, table_name, nb_controles, nb_echecs, statut, detail FROM dq_results ORDER BY regle, table_name", con)
nb_rejets = pd.read_sql_query("SELECT COUNT(*) AS n FROM stg_rejects", con)["n"][0]
dernier_run = pd.read_sql_query(
    "SELECT debut, duree_s, statut, nb_raw, nb_faits, nb_lignes_mart, message FROM etl_run_log ORDER BY debut DESC LIMIT 1", con)

# Une ligne par règle : le pire statut de ses contrôles
dq["gravite"] = dq["statut"].map(GRAVITE_STATUT.index)
regles = dq.groupby("regle").agg(
    tables=("table_name", "nunique"), echecs=("nb_echecs", "sum"), gravite=("gravite", "max")).reset_index()
regles["statut"] = regles["gravite"].map(lambda g: GRAVITE_STATUT[g])
alertes = dq[dq["statut"] == "ALERTE"].drop_duplicates("regle").set_index("regle")["detail"]
regles["detail"] = regles["regle"].map(alertes).fillna("")
nb_regles = len(regles)
nb_ok = int((regles["statut"] == "OK").sum())
nb_alertes = int((regles["statut"] == "ALERTE").sum())

# --- 3 cartes : règles OK, rejets, alertes ---
st.markdown('<div class="section">Résultat des contrôles</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.markdown(
    f'<div class="carte"><div class="titre">Règles OK</div>'
    f'<div class="valeur">{nb_ok} sur {nb_regles}</div><div class="unite">règles DQ01 à DQ12</div></div>',
    unsafe_allow_html=True)
classe_rejets = "carte alerte" if nb_rejets > 0 else "carte"
c2.markdown(
    f'<div class="{classe_rejets}"><div class="titre">Rejets</div>'
    f'<div class="valeur">{nb_rejets}</div><div class="unite">lignes dans stg_rejects</div></div>',
    unsafe_allow_html=True)
if nb_rejets == 0:
    c2.caption("0 rejet sur les données officielles, qui sont propres. Les contrôles sont prouvés par test_etl.py, "
               "qui injecte 11 anomalies et obtient 11 rejets tracés.")
else:
    c2.caption(f"{nb_rejets} lignes refusées : voir stg_rejects. Les contrôles sont prouvés par test_etl.py, "
               "qui injecte 11 anomalies et obtient 11 rejets tracés.")
classe_alertes = "carte alerte" if nb_alertes > 0 else "carte"
c3.markdown(
    f'<div class="{classe_alertes}"><div class="titre">Alertes</div>'
    f'<div class="valeur">{nb_alertes}</div><div class="unite">à analyser, le run continue</div></div>',
    unsafe_allow_html=True)

# --- Tableau des règles, statut en couleur ---
st.markdown('<div class="section">Règles qualité DQ01 à DQ12</div>', unsafe_allow_html=True)


def colorier(statut):
    return f"background-color: {COULEURS_STATUT[statut]}; color: white; font-weight: 600"


tableau_regles = regles[["regle", "tables", "echecs", "statut", "detail"]]
tableau_regles.columns = ["Règle", "Tables contrôlées", "Échecs", "Statut", "Détail"]
st.dataframe(tableau_regles.style.map(colorier, subset=["Statut"]), hide_index=True, width="stretch")

with st.expander("Voir les contrôles ligne par ligne"):
    tableau_dq = dq[["regle", "table_name", "nb_controles", "nb_echecs", "statut", "detail"]]
    tableau_dq.columns = ["Règle", "Table", "Contrôles", "Échecs", "Statut", "Détail"]
    st.dataframe(tableau_dq.style.map(colorier, subset=["Statut"]), hide_index=True, width="stretch")

# --- Dernier run de l'ETL ---
st.markdown('<div class="section">Dernier run de l\'ETL</div>', unsafe_allow_html=True)
if dernier_run.empty:
    st.markdown("<div class='a-venir'>Aucun run enregistré : lancer 04_ETL/etl_pipeline.py.</div>", unsafe_allow_html=True)
else:
    run = dernier_run.iloc[0]
    date_run = pd.to_datetime(run["debut"]).strftime("%d/%m/%Y %H:%M:%S")
    duree = f"{run['duree_s']:.2f}".replace(".", ",")
    couleur_statut = COULEURS_STATUT["OK"] if run["statut"] == "SUCCES" else COULEURS_STATUT["ECHEC"]
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(
        f'<div class="carte"><div class="titre">Date du run</div>'
        f'<div class="valeur" style="font-size:1.5rem">{date_run}</div><div class="unite">début</div></div>',
        unsafe_allow_html=True)
    r2.markdown(
        f'<div class="carte"><div class="titre">Durée</div>'
        f'<div class="valeur">{duree}</div><div class="unite">secondes</div></div>',
        unsafe_allow_html=True)
    r3.markdown(
        f'<div class="carte"><div class="titre">Statut</div>'
        f'<div class="valeur" style="color:{couleur_statut}">{run["statut"]}</div><div class="unite">publication de la base</div></div>',
        unsafe_allow_html=True)
    r4.markdown(
        f'<div class="carte"><div class="titre">Lignes traitées</div>'
        f'<div class="valeur" style="font-size:1.5rem">{run["nb_raw"]:,} → {run["nb_faits"]:,}'.replace(",", " ") +
        f'</div><div class="unite">RAW → faits ({run["nb_lignes_mart"]} lignes MART)</div></div>',
        unsafe_allow_html=True)
    if run["message"]:
        st.caption(f"Message : {run['message']}")

# --- Note sur les 2 alertes connues ---
detail_dq10 = alertes.get("DQ10", "2026-05 +29.5 % vs 2026-04").replace(".", ",")
st.markdown('<div class="section">Les 2 alertes connues</div>', unsafe_allow_html=True)
st.markdown(
    "<div class='a-venir'>"
    f"<b>DQ10 : variation mensuelle ({detail_dq10}).</b> Mai dépasse le seuil de 25 % fixé par le groupe. "
    "C'est un signal que le HSE doit analyser, pas une erreur de données : le pic de mai se voit aussi dans le graphique « Incidents par mois ».<br><br>"
    "<b>DQ11 : home_area des engins.</b> Les valeurs (Yxx) ne correspondent à aucune zone (LOCxxx) : on ne peut pas relier les engins aux zones. "
    "C'est une limite des données, connue et documentée ; les engins restent dans le Data Warehouse, sans lien vers les zones."
    "</div>", unsafe_allow_html=True)

st.caption("Source : tables MART et suivi qualité du Data Warehouse (données synthétiques). "
           "Les filtres s'appliquent aux graphiques ; les cartes KPI portent sur toute la période.")
