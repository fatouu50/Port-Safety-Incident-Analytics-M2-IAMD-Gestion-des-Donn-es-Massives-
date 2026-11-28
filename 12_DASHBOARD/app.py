"""
Projet 11 : tableau de bord HSE (Streamlit).
Lit uniquement les tables MART du DWH (04_ETL/project_11_dwh.db), plus le suivi qualité (en bas de page).
Si la base n'existe pas, elle est construite par 04_ETL/etl_pipeline.py au démarrage.
Lancement depuis la racine du projet :  streamlit run 12_DASHBOARD/app.py
"""
import base64
import html
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
CATALOGUE_REGLES = DOSSIER_DASHBOARD.parent / "06_GOVERNANCE" / "data_quality_rules.csv"
LOGO = DOSSIER_DASHBOARD / "assets" / "logo_ud.jpg"
FOND = DOSSIER_DASHBOARD / "assets" / "fond_port.jpg"
BATEAU = DOSSIER_DASHBOARD / "assets" / "bateau.jpg"

st.set_page_config(page_title="Projet 11 – Port Safety & Incident Analytics", page_icon="⚓", layout="wide",
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

@st.cache_data(ttl=600)
def lire(requete):
    """Lit une requête SQL dans le DWH. Le résultat est gardé en cache 10 min :
    un clic sur un filtre ne relit pas la base."""
    with sqlite3.connect(BASE_DWH) as connexion:
        return pd.read_sql_query(requete, connexion)


def afficher(fig):
    """Affiche une figure matplotlib puis la ferme (sinon la mémoire grossit à chaque clic)."""
    st.pyplot(fig)
    plt.close(fig)


def filtre_info(texte):
    """Petite mention sous le titre d'un graphique : quel filtre agit dessus."""
    st.markdown(f'<div class="filtre-info">{texte}</div>', unsafe_allow_html=True)


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
# Photo de fond : un voile clair par-dessus garde les graphiques lisibles
fond_base64 = base64.b64encode(FOND.read_bytes()).decode()
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(rgba(247, 242, 251, 0.82), rgba(247, 242, 251, 0.82)),
         url("data:image/jpeg;base64,{fond_base64}") center / cover fixed no-repeat; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
/* Barre Streamlit du haut (Fork, GitHub, menu) : masquée, car en ligne elle recouvre le haut de la bannière */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stMainMenu"],
[data-testid="stAppDeployButton"], #MainMenu { display: none !important; }
.block-container { padding-top: 1.8rem; max-width: 1400px; }
.bandeau { background: linear-gradient(90deg, #4A1D6E 0%, #7B3FA0 60%, #EE82B7 100%); border-radius: 16px;
           padding: 14px 24px; display: flex; align-items: center; gap: 18px; margin-bottom: 14px; }
.bandeau .texte { flex: 1; }
.bandeau img.photo { height: 74px; width: 132px; object-fit: cover; border-radius: 10px; border: 2px solid #FFFFFF; }
.bandeau .photo-vide { height: 74px; width: 132px; border-radius: 10px; border: 2px solid #FFFFFF; font-size: 2.4rem;
                       display: flex; align-items: center; justify-content: center; }
.bandeau img.logo { height: 74px; background: #FFFFFF; border-radius: 10px; padding: 4px; }
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
.filtre-info { color: #9E1F5C; font-size: 0.72rem; text-align: center; margin: -2px 0 4px 0; }
.titre-filtre { color: #4A1D6E; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .titre-graphe),
[data-testid="stVerticalBlock"]:has(> [data-testid="stHorizontalBlock"] .titre-filtre),
[data-testid="stVerticalBlock"]:has(> [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] .titre-filtre) { background: #FFFFFF; border-radius: 14px; }
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
if BATEAU.exists():
    photo = f'<img class="photo" src="data:image/jpeg;base64,{base64.b64encode(BATEAU.read_bytes()).decode()}">'
else:   # tant que l'image n'est pas dans assets/, une ancre la remplace
    photo = '<div class="photo-vide">⚓</div>'
st.markdown(f"""
<div class="bandeau">
{photo}
<div class="texte">
<h1>SÉCURITÉ PORTUAIRE : TABLEAU DE BORD HSE</h1>
<p>Université de Djibouti · Master 2 IAMD · Gestion des Données Massives</p>
<p>Groupe 8 · Mako Mohamed Aden &amp; Fatouma Soubere Mahamoud</p>
<p>Projet 11 – Port Safety &amp; Incident Analytics · données du 1er janvier au 28 octobre 2026</p>
</div>
<img class="logo" src="data:image/jpeg;base64,{logo_base64}">
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Les filtres (slicers), dans une barre sous le bandeau
# ---------------------------------------------------------------------
mois_dispo = lire("SELECT mois FROM mart_incidents_month ORDER BY mois")["mois"].tolist()
types_zone = lire("SELECT DISTINCT area_type FROM mart_incidents_by_area ORDER BY area_type")["area_type"].tolist()
equipes = lire("SELECT DISTINCT shift FROM mart_incident_rate_shift_role ORDER BY shift")["shift"].tolist()

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
    st.caption("Aucun type de zone choisi : tous les types sont affichés.")
if not equipes_choisies:
    equipes_choisies = equipes
    st.caption("Aucune équipe choisie : toutes les équipes sont affichées.")

# ---------------------------------------------------------------------
# Les 3 KPI du haut, issus de la partie SQL (Q05 bis, Q06, Q07)
# Mêmes calculs, lus dans les tables MART
# ---------------------------------------------------------------------
mois_tous = lire("SELECT * FROM mart_incidents_month ORDER BY mois")
nm_tous = lire("SELECT * FROM mart_near_miss ORDER BY mois")

kpi_moyenne = mois_tous[mois_tous["mois_complet"] == 1]["nb_incidents"].mean()          # Q05 bis
kpi_graves = 100 * mois_tous["nb_graves"].sum() / mois_tous["nb_incidents"].sum()       # Q06
kpi_near_miss = nm_tous["near_miss_total"].sum()                                         # Q07


def carte_kpi(colonne, icone, titre, valeur, unite, alerte=False):
    """Affiche une carte : icône à gauche, titre, valeur et unité à droite."""
    classe = "carte alerte" if alerte else "carte"
    colonne.markdown(
        f'<div class="{classe}"><div class="ligne">'
        f'<div class="icone">{ICONES[icone]}</div>'
        f'<div><div class="titre">{titre}</div>'
        f'<div class="valeur">{valeur}</div>'
        f'<div class="unite">{unite}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


k1, k2, k3 = st.columns(3)
carte_kpi(k1, "KPI1", "Incidents par mois", f"{kpi_moyenne:.1f}".replace(".", ","), "moyenne des 9 mois complets (Q05 bis)")
carte_kpi(k2, "KPI2", "Incidents graves", f"{kpi_graves:.1f}".replace(".", ",") + " %", "HIGH + CRITICAL (Q06)", alerte=True)
carte_kpi(k3, "KPI4", "Near-miss", f"{kpi_near_miss}", "incidents + observations (Q07)")

# ---------------------------------------------------------------------
# Les 6 graphiques de l'EDA (07_EDA/eda_projet11.ipynb), sur 2 lignes de 3
# ---------------------------------------------------------------------
mois = mois_tous[(mois_tous["mois"] >= debut) & (mois_tous["mois"] <= fin)]   # slicer « Période »
nm = nm_tous[(nm_tous["mois"] >= debut) & (nm_tous["mois"] <= fin)].copy()    # slicer « Période »

case_1, case_2, case_3 = st.columns(3)

# Graphique 1 : incidents par mois
with case_1.container(border=True):
    st.markdown('<div class="titre-graphe">Incidents par mois en 2026</div>', unsafe_allow_html=True)
    filtre_info("filtré par : période")
    moyenne = mois[mois["mois_complet"] == 1]["nb_incidents"].mean()
    couleurs = [ROSE if complet == 1 else GRIS_INCOMPLET for complet in mois["mois_complet"]]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(mois["mois"], mois["nb_incidents"], color=couleurs, label="Incidents")
    ax.bar(mois["mois"], mois["nb_graves"], color=VIOLET_FONCE, label="dont graves (HIGH + CRITICAL)")
    if pd.notna(moyenne):   # pas de moyenne si la période ne contient que le mois incomplet
        ax.axhline(moyenne, color=VIOLET, linestyle="--", label=f"Moyenne des mois complets ({moyenne:.0f})")
    ax.set_ylabel("Nombre d'incidents")
    ax.set_ylim(0, mois["nb_incidents"].max() * 1.35)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    afficher(fig)

# Graphique 2 : répartition par gravité
with case_2.container(border=True):
    st.markdown('<div class="titre-graphe">Répartition des incidents par gravité</div>', unsafe_allow_html=True)
    filtre_info("toute la période, sans filtre")
    gravite = lire("SELECT * FROM mart_severity_distribution")
    ordre = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    gravite = gravite.set_index("severity").loc[ordre].reset_index()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(gravite["severity"], gravite["nb_incidents"], color=[COULEURS_GRAVITE[g] for g in ordre])
    for i, ligne in gravite.iterrows():
        ax.text(i, ligne["nb_incidents"] + 10, f"{ligne['pct']} %", ha="center", color=VIOLET_FONCE)
    ax.set_ylabel("Nombre d'incidents")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    afficher(fig)

# Graphique 3 : top 10 des zones par score de risque
with case_3.container(border=True):
    st.markdown('<div class="titre-graphe">Top 10 des zones par score de risque (/100)</div>', unsafe_allow_html=True)
    filtre_info("filtré par : types de zone")
    zones = lire("SELECT * FROM mart_incidents_by_area ORDER BY score_risque DESC")
    zones = zones[zones["area_type"].isin(zones_choisies)].head(10)               # slicer « Types de zone »
    zones = zones.sort_values("score_risque")       # pour barh : la plus risquée en haut
    etiquettes = zones["location_id"] + " (" + zones["area_type"] + ")"
    couleurs = [ROSE] * (len(zones) - 1) + [FRAMBOISE]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.barh(etiquettes, zones["score_risque"], color=couleurs)
    for i, (score, graves) in enumerate(zip(zones["score_risque"], zones["nb_graves"])):
        ax.text(score + 1, i, f"{graves} graves", va="center", color=VIOLET_FONCE)
    ax.set_xlabel("Score de risque")
    ax.set_xlim(0, 125)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    afficher(fig)

case_4, case_5, case_6 = st.columns(3)

# Graphique 4 : heatmap rôle × équipe
with case_4.container(border=True):
    st.markdown('<div class="titre-graphe">Incidents par travailleur, par rôle et par équipe</div>', unsafe_allow_html=True)
    filtre_info("filtré par : équipes")
    taux = lire("SELECT * FROM mart_incident_rate_shift_role")
    taux = taux[taux["shift"].isin(equipes_choisies)]                               # slicer « Équipes »
    tableau = taux.pivot(index="role", columns="shift", values="incidents_par_travailleur")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    image = ax.imshow(tableau.values, cmap="RdPu")
    fig.colorbar(image, ax=ax, label="Incidents par travailleur")
    ax.set_xticks(range(len(tableau.columns)), tableau.columns)
    ax.set_yticks(range(len(tableau.index)), tableau.index)
    moyenne_cases = tableau.values.mean()
    for ligne in range(tableau.shape[0]):
        for colonne in range(tableau.shape[1]):
            valeur = tableau.values[ligne, colonne]
            couleur_texte = "white" if valeur > moyenne_cases else VIOLET_FONCE
            ax.text(colonne, ligne, f"{valeur:.2f}", ha="center", va="center", color=couleur_texte)
    ax.set_xlabel("Équipe")
    fig.tight_layout()
    afficher(fig)

# Graphique 5 : near-miss et incidents graves par mois
with case_5.container(border=True):
    st.markdown('<div class="titre-graphe">Near-miss et incidents graves par mois</div>', unsafe_allow_html=True)
    filtre_info("filtré par : période")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(nm["mois"], nm["near_miss_total"], marker="o", linewidth=2, color=ROSE, label="Near-miss (incidents + observations)")
    ax.plot(nm["mois"], nm["incidents_graves"], marker="s", linewidth=2, color=VIOLET_FONCE, label="Incidents graves")
    ax.set_ylabel("Nombre")
    ax.set_ylim(0, nm["near_miss_total"].max() * 1.2)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    afficher(fig)
    ratio = nm["near_miss_total"].sum() / nm["incidents_graves"].sum()
    st.caption(f"{ratio:.1f}".replace(".", ",") + " near-miss pour 1 incident grave sur la période.")

# Graphique 6 : observations UNSAFE et incidents graves, par zone
with case_6.container(border=True):
    st.markdown('<div class="titre-graphe">Observations UNSAFE et incidents graves, par zone</div>', unsafe_allow_html=True)
    filtre_info("filtré par : types de zone")
    zones_toutes = lire("SELECT * FROM mart_incidents_by_area")
    zones_toutes = zones_toutes[zones_toutes["area_type"].isin(zones_choisies)]    # slicer « Types de zone »
    top4 = zones_toutes.nlargest(4, "nb_graves")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(zones_toutes["pct_unsafe"], zones_toutes["nb_graves"], s=60, color=ROSE)
    ax.scatter(top4["pct_unsafe"], top4["nb_graves"], s=80, color=FRAMBOISE)
    for _, zone in top4.iterrows():
        ax.annotate(zone["location_id"], (zone["pct_unsafe"], zone["nb_graves"]),
                    xytext=(5, 4), textcoords="offset points", color=VIOLET_FONCE)
    ax.set_xlabel("% d'observations UNSAFE de la zone")
    ax.set_ylabel("Incidents graves de la zone")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    afficher(fig)
    st.caption(f"Corrélation % UNSAFE / incidents graves : {zones_toutes['pct_unsafe'].corr(zones_toutes['nb_graves']):.2f}".replace(".", ","))


# ---------------------------------------------------------------------
# Télécharger les données affichées, avec les filtres appliqués
# ---------------------------------------------------------------------
st.markdown('<div class="section">Télécharger les données filtrées (CSV)</div>', unsafe_allow_html=True)
t1, t2, t3 = st.columns(3)
t1.download_button("Incidents et near-miss par mois", mois.merge(nm, on="mois", how="left").to_csv(index=False).encode("utf-8"),
                   file_name=f"incidents_par_mois_{debut}_{fin}.csv", mime="text/csv", width="stretch")
t2.download_button("Zones et score de risque", zones_toutes.sort_values("score_risque", ascending=False).to_csv(index=False).encode("utf-8"),
                   file_name="zones_score_risque.csv", mime="text/csv", width="stretch")
t3.download_button("Incidents par rôle et par équipe", taux.to_csv(index=False).encode("utf-8"),
                   file_name="incidents_role_equipe.csv", mime="text/csv", width="stretch")


# =====================================================================
# Qualité des données (partie de Mako) : règles DQ, rejets, dernier run de l'ETL
# =====================================================================
st.markdown('<div class="titre-partie">Qualité des données</div>', unsafe_allow_html=True)

# Couleurs des statuts qualité (OK et ALERTE : charte ; ECHEC : framboise ; REJETS : violet)
COULEURS_STATUT = {"OK": "#2E8B57", "ALERTE": "#D99A1B", "ECHEC": "#9E1F5C", "REJETS": "#7B3FA0"}
# Style du tableau des règles (placé ici pour ne toucher qu'à cette section)
st.markdown("""
<style>
table.regles { width: 100%; table-layout: fixed; border-collapse: collapse; background: #FFFFFF; font-size: 0.85rem; }
table.regles th, table.regles td { border: 1px solid #E4D6EF; padding: 6px 8px; text-align: left; vertical-align: middle;
                                   white-space: normal; overflow-wrap: break-word; color: #2B2333; }
table.regles th { background: #EDE4F5; color: #4A1D6E; font-weight: 700; overflow-wrap: normal; }
table.regles td.nombre { text-align: right; }
</style>
""", unsafe_allow_html=True)
GRAVITE_STATUT = ["OK", "REJETS", "ALERTE", "ECHEC"]   # du moins grave au plus grave

# Lecture seule (SELECT) : jamais la colonne « record » de stg_rejects (elle contient le worker_id)
dq = lire("SELECT regle, table_name, nb_controles, nb_echecs, statut, detail FROM dq_results ORDER BY regle, table_name")
nb_rejets = lire("SELECT COUNT(*) AS n FROM stg_rejects")["n"][0]
dernier_run = lire("SELECT debut, duree_s, statut, nb_raw, nb_faits, nb_lignes_mart, message FROM etl_run_log ORDER BY debut DESC LIMIT 1")

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
# Hauteur fixée pour afficher les 12 lignes sans barre de défilement (35 px par ligne, plus l'en-tête)
st.dataframe(tableau_regles.style.map(colorier, subset=["Statut"]), hide_index=True, width="stretch",
             height=35 * (len(tableau_regles) + 1) + 3,
             column_config={"Règle": st.column_config.TextColumn(width="small"),
                            "Tables contrôlées": st.column_config.NumberColumn(width="small"),
                            "Échecs": st.column_config.NumberColumn(width="small"),
                            "Statut": st.column_config.TextColumn(width="small"),
                            "Détail": st.column_config.TextColumn(width="large")})

with st.expander("Voir les contrôles ligne par ligne"):
    tableau_dq = dq[["regle", "table_name", "nb_controles", "nb_echecs", "statut", "detail"]]
    tableau_dq.columns = ["Règle", "Table", "Contrôles", "Échecs", "Statut", "Détail"]
    st.dataframe(tableau_dq.style.map(colorier, subset=["Statut"]), hide_index=True, width="stretch",
                 column_config={"Détail": st.column_config.TextColumn(width="large")})

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
           "Les filtres s'appliquent aux graphiques ; les 3 KPI et la répartition par gravité portent sur toute la période.")
