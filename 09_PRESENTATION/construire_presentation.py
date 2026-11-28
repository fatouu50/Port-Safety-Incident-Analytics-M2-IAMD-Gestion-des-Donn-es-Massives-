"""
Projet 11 : construit la présentation de soutenance (12 slides, trame du professeur) avec python-pptx.
Sortie : 09_PRESENTATION/presentation_projet11.pptx
Lancement depuis la racine du projet :  python 09_PRESENTATION/construire_presentation.py
Les chiffres viennent du dépôt (base project_11_dwh.db, kpi_catalog.csv, rapport) ; la liste des vérifications est donnée dans la réponse de livraison.
"""
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RACINE = Path(__file__).resolve().parent.parent
SORTIE = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "09_PRESENTATION" / "presentation_projet11.pptx"

# Couleurs de la charte du dashboard (12_DASHBOARD/app.py)
VIOLET_FONCE, VIOLET, ROSE, FRAMBOISE = "4A1D6E", "7B3FA0", "EE82B7", "9E1F5C"
LAVANDE, ROSE_PALE, FOND, BLANC, GRIS, TEXTE = "EDE4F5", "FDEEF5", "F7F2FB", "FFFFFF", "6B6375", "2B2333"
VIOLET_CLAIR = "A77BC9"
POLICE = "Calibri"


def rgb(h):
    return RGBColor.from_string(h)


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
VIDE = prs.slide_layouts[6]


# ------------------------------------------------------------------ outils
def fond(slide, couleur):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = rgb(couleur)


def forme(slide, x, y, w, h, couleur=BLANC, bord=None, type_=MSO_SHAPE.ROUNDED_RECTANGLE, epaisseur=1.5, pointille=False, rayon=0.08):
    s = slide.shapes.add_shape(type_, Inches(x), Inches(y), Inches(w), Inches(h))
    if couleur is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(couleur)
    if bord:
        s.line.color.rgb = rgb(bord)
        s.line.width = Pt(epaisseur)
        if pointille:
            s.line.dash_style = 4  # MSO_LINE.DASH
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if type_ == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = rayon
    return s


def texte(shape_or_slide, paragraphes, x=None, y=None, w=None, h=None, taille=20, couleur=TEXTE, gras=False,
          align=PP_ALIGN.LEFT, ancrage=MSO_ANCHOR.MIDDLE, marge=0.08, italique=False):
    """paragraphes : str, ou liste de paragraphes ; un paragraphe est un str ou une liste de (texte, {options})."""
    if x is not None:
        tb = shape_or_slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        cible = tb
    else:
        cible = shape_or_slide
        tf = cible.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = ancrage
    tf.margin_left = tf.margin_right = Inches(marge)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    if isinstance(paragraphes, str):
        paragraphes = [paragraphes]
    for i, par in enumerate(paragraphes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        runs = [(par, {})] if isinstance(par, str) else par
        for t, opt in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = POLICE
            f.size = Pt(opt.get("taille", taille))
            f.bold = opt.get("gras", gras)
            f.italic = opt.get("italique", italique)
            f.color.rgb = rgb(opt.get("couleur", couleur))
    return cible


def titre(slide, grand, sous, couleur=VIOLET_FONCE, couleur_sous=FRAMBOISE):
    """Titre de la trame du professeur (grand) et phrase-message (sous-titre, plus petit, en rose)."""
    texte(slide, grand, 0.6, 0.18, 12.13, 0.62, taille=32, couleur=couleur, gras=True)
    texte(slide, sous, 0.6, 0.78, 12.13, 0.45, taille=22, couleur=couleur_sous, gras=True)


def fleche(slide, x, y, w, h, couleur=VIOLET_FONCE, type_=MSO_SHAPE.RIGHT_ARROW):
    return forme(slide, x, y, w, h, couleur, type_=type_)


def ligne(slide, x1, y1, x2, y2, couleur=VIOLET, epaisseur=3):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(couleur)
    c.line.width = Pt(epaisseur)
    return c


def image(slide, chemin, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(RACINE / chemin), Inches(x), Inches(y), **kw)


def chiffre(slide, x, y, w, h, grand, label, fond_=BLANC, c_grand=VIOLET, c_label=GRIS, taille=60, bord=LAVANDE, unite=None):
    forme(slide, x, y, w, h, fond_, bord)
    runs = [(grand, {"taille": taille, "gras": True, "couleur": c_grand})]
    if unite:
        runs.append((unite, {"taille": taille * 0.55, "gras": True, "couleur": c_grand}))
    texte(slide, [runs], x, y + 0.05, w, h * 0.58, align=PP_ALIGN.CENTER, marge=0.03)
    texte(slide, label, x, y + h * 0.58, w, h * 0.40, taille=18, couleur=c_label, align=PP_ALIGN.CENTER, ancrage=MSO_ANCHOR.TOP, marge=0.08)


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


def nouvelle(couleur_fond=FOND):
    s = prs.slides.add_slide(VIDE)
    fond(s, couleur_fond)
    return s


# ------------------------------------------------------------------ 1. titre (Mako, 0,5 min)
s = nouvelle(VIOLET_FONCE)
forme(s, 0.8, 0.8, 1.5, 1.5, BLANC, type_=MSO_SHAPE.ROUNDED_RECTANGLE)
image(s, "12_DASHBOARD/assets/logo_ud.jpg", 0.9, 0.9, w=1.3)
texte(s, "PROJET 11", 2.6, 0.85, 8, 0.5, taille=22, couleur=ROSE, gras=True)
texte(s, "Master 2 IAMD · Gestion des Données Massives · Université de Djibouti", 2.6, 1.4, 10, 0.5, taille=20, couleur="D9C8EA")
texte(s, "Port Safety & Incident Analytics", 0.8, 2.6, 11.8, 1.3, taille=54, couleur=BLANC, gras=True)
texte(s, "Des fichiers CSV aux décisions du service HSE", 0.8, 3.9, 11.8, 0.7, taille=28, couleur=ROSE)
forme(s, 0.8, 5.0, 11.7, 1.55, "5E2A85", type_=MSO_SHAPE.ROUNDED_RECTANGLE)
texte(s, [[("Mako Mohamed Aden  et  Fatouma Soubere Mahamoud", {"gras": True, "taille": 26})],
          [("Enseignant : Mr. MOHAMED ADEN  ·  Soutenance du 16 novembre 2026", {"taille": 20, "couleur": "D9C8EA"})]],
      1.1, 5.05, 11.2, 1.45, couleur=BLANC)
notes(s, "Mako, 0,5 min.\n"
         "Bonjour, nous présentons le projet 11, Port Safety & Incident Analytics, réalisé avec Fatouma en Master 2 IAMD. "
         "Je présente le contexte, l'architecture, le Data Warehouse, l'ETL avec la qualité des données, et la gouvernance. Fatouma présente les données, le SQL, HDFS et l'analyse. "
         "Nous vous montrerons aussi le dashboard en ligne.\n"
         "Répartition du temps : Mako environ 10,5 minutes, Fatouma environ 8 minutes, soit 18,5 minutes en tout, puis 5 minutes de questions.")

# ------------------------------------------------------------------ 2. problématique (Mako, 1 min)
s = nouvelle()
titre(s, "Problématique métier", "Le service HSE a des fichiers, pas encore de réponses")
noms = ["incidents.csv", "safety_observations.csv", "locations.csv", "workers_synthetic.csv", "equipment.csv"]
for i, n in enumerate(noms):
    y = 1.75 + i * 0.98
    forme(s, 0.6, y, 4.3, 0.8, BLANC, VIOLET, type_=MSO_SHAPE.ROUNDED_RECTANGLE)
    forme(s, 0.75, y + 0.15, 0.5, 0.5, VIOLET, type_=MSO_SHAPE.FLOWCHART_DOCUMENT)
    texte(s, n, 1.4, y, 3.4, 0.8, taille=20, couleur=VIOLET_FONCE, gras=True)
fleche(s, 5.15, 3.75, 0.9, 0.7, ROSE)
forme(s, 6.3, 1.75, 6.43, 4.8, VIOLET_FONCE)
texte(s, [[("Où, quand, comment et à qui arrivent les incidents ?", {"taille": 36, "gras": True})]], 6.6, 2.0, 5.85, 3.2, couleur=BLANC)
texte(s, "Service HSE : Hygiène, Sécurité, Environnement", 6.6, 5.3, 5.85, 0.9, taille=20, couleur=ROSE)
notes(s, "Mako, 1 min.\n"
         "Le service HSE est chargé de la sécurité des personnes sur un terminal portuaire. Il dispose de cinq fichiers CSV : deux listent des événements, "
         "les incidents et les observations, et trois décrivent le site, les zones, les travailleurs et les engins. "
         "Tels quels, ils ne répondent à rien. Notre question est donc : où, quand, comment et à qui arrivent les incidents ?")

# ------------------------------------------------------------------ 3. architecture (Mako, 1,5 min)
s = nouvelle()
titre(s, "Architecture générale", "Des fichiers CSV aux décisions HSE, en six blocs")
image(s, "09_PRESENTATION/architecture_simplifiee.png", 0.5, 1.6, w=12.33)
notes(s, "Mako, 1,5 min.\n"
         "Voici toute la chaîne en six blocs. Les cinq fichiers CSV alimentent le Data Warehouse, qui compte quatre couches. "
         "Les mêmes sources sont aussi archivées dans HDFS pour garder l'historique brut. "
         "À partir du Data Warehouse, on fait deux choses : l'analyse exploratoire en Python et le dashboard en ligne. "
         "Tout cela sert un seul but : les décisions du service HSE. Je passe maintenant la parole à Fatouma, qui va présenter les données.")

# ------------------------------------------------------------------ 4. données et 5V (Fatouma, 1 min)
s = nouvelle()
titre(s, "Données et 5V", "5 315 lignes : un petit jeu d'enseignement, assumé")
forme(s, 0.6, 1.5, 12.13, 1.65, VIOLET_FONCE)
texte(s, [[("5 315", {"taille": 80, "gras": True})]], 0.8, 1.5, 3.8, 1.65, couleur=BLANC)
texte(s, [[("lignes, 260,5 ko", {"taille": 28, "gras": True, "couleur": ROSE})],
          [("Les méthodes du cours, sur des données synthétiques", {"taille": 20})]], 4.6, 1.5, 8.0, 1.65, couleur=BLANC)
elements = [("1 400", "incidents"), ("3 500", "observations"), ("25", "zones"), ("350", "travailleurs"), ("40", "engins")]
for i, (n, l) in enumerate(elements):
    chiffre(s, 0.6 + i * 2.5, 3.35, 2.3, 1.95, n, l, taille=60)
cinq_v = [("Volume", "faible"), ("Vélocité", "par lot (hypothèse)"), ("Variété", "5 CSV structurés"), ("Véracité", "12 règles de contrôle"), ("Valeur", "6 KPI du sujet")]
for i, (v, t) in enumerate(cinq_v):
    forme(s, 0.6 + i * 2.5, 5.5, 2.3, 1.3, LAVANDE)
    texte(s, [[(v, {"gras": True, "couleur": VIOLET_FONCE, "taille": 20})], [(t, {"taille": 18, "couleur": TEXTE})]], 0.6 + i * 2.5, 5.5, 2.3, 1.3, align=PP_ALIGN.CENTER)
notes(s, "Fatouma, 1 min.\n"
         "Merci Mako. Nos données comptent 5 315 lignes : 1 400 incidents, 3 500 observations, 25 zones, 350 travailleurs et 40 engins. "
         "Soyons francs : le volume est petit, 260 kilo-octets, c'est un jeu d'enseignement et non du vrai Big Data. "
         "Nous appliquons donc les méthodes du cours, avec une architecture pensée pour un historique qui grandit. "
         "Sur les 5V, la vélocité est une hypothèse de notre part : le jeu est statique, nous traitons par lot.")

# ------------------------------------------------------------------ 5. SQL / modèle source (Fatouma, 1,5 min)
s = nouvelle()
titre(s, "SQL et modèle source", "Cinq tables reliées par des clés, interrogées en SQL")


def table_sql(x, y, w, h, nom, cle, fk=None):
    forme(s, x, y, w, h, BLANC, VIOLET, epaisseur=2)
    paras = [[(nom, {"taille": 20, "gras": True, "couleur": VIOLET_FONCE})], [("clé : " + cle, {"taille": 18, "couleur": GRIS})]]
    if fk:
        paras.append([(fk, {"taille": 18, "couleur": FRAMBOISE, "gras": True})])
    texte(s, paras, x, y, w, h, align=PP_ALIGN.CENTER)


# liens d'abord (les tables passent au-dessus)
ligne(s, 4.0, 3.55, 2.1, 2.55)      # incidents -> workers_synthetic
ligne(s, 5.3, 3.55, 5.9, 2.55)      # incidents -> equipment
ligne(s, 6.6, 3.55, 9.4, 2.55)      # incidents -> locations
ligne(s, 10.9, 3.55, 10.9, 2.55)    # safety_observations -> locations
table_sql(0.6, 1.5, 3.2, 1.05, "workers_synthetic", "worker_id")
table_sql(4.4, 1.5, 3.0, 1.05, "equipment", "equipment_id")
table_sql(9.2, 1.5, 3.0, 1.05, "locations", "location_id")
table_sql(2.4, 3.5, 4.4, 1.5, "incidents", "incident_id", "liens : zone, engin, travailleur")
table_sql(8.7, 3.5, 4.0, 1.5, "safety_observations", "observation_id", "lien : zone")
tags = [("Jointures", ["1 400 lignes avant et après : aucun doublon"]), ("Agrégations", ["144,0 incidents par mois"]),
        ("CTE", ["WITH mensuel AS … LAG()", "mai +29,5 %"]), ("KPI", ["22,3 % d'incidents graves"])]
for i, (t, d) in enumerate(tags):
    x = 0.6 + i * 3.06
    forme(s, x, 5.3, 2.9, 1.65, VIOLET_FONCE if i % 2 == 0 else VIOLET)
    texte(s, [[(t, {"taille": 26, "gras": True, "couleur": ROSE})]] + [[(ligne_, {"taille": 18})] for ligne_ in d], x, 5.3, 2.9, 1.65, couleur=BLANC, align=PP_ALIGN.CENTER)
notes(s, "Fatouma, 1,5 min.\n"
         "Avant le Data Warehouse, nous avons chargé les cinq fichiers dans une base relationnelle SQLite. Chaque table a une clé primaire, et les incidents sont reliés aux zones, aux engins et aux travailleurs par des clés étrangères ; les observations sont reliées aux zones. "
         "La base refuse toute ligne qui enfreint ces règles : au chargement, les 5 315 lignes sont acceptées. "
         "Nous avons écrit 15 requêtes, qui couvrent les quatre techniques du sujet. Les jointures (requête Q02 bis) : on vérifie qu'une jointure ne multiplie pas les lignes, 1 400 avant et après, donc aucun doublon. "
         "Les agrégations (requête Q05 bis) : 144,0 incidents par mois complet. Les CTE (requête Q11) : on compare chaque mois au précédent avec la fonction LAG, et on trouve +29,5 % en mai. "
         "Enfin, le KPI de gravité (requête Q06) : 22,3 % d'incidents graves. Ces chiffres sont ensuite retrouvés à l'identique dans le Data Warehouse, c'est une vérification croisée.\n"
         "Je passe maintenant la parole à Mako, qui va présenter le Data Warehouse.\n"
         "Source : 03_SQL/schema_sources.sql, 03_SQL/starter_queries.sql, section 3 du rapport.")

# ------------------------------------------------------------------ 6. Data Warehouse (Mako, 1,5 min)
s = nouvelle()
titre(s, "Data Warehouse", "Un schéma en étoile : 2 tables de faits, 9 dimensions")
forme(s, 0.6, 1.55, 8.9, 4.0, FOND, LAVANDE)
image(s, "09_PRESENTATION/schema_etoile_simplifie.png", 0.75, 1.65, w=8.6)
chiffre(s, 9.7, 1.55, 3.03, 1.9, "2", "tables de faits", taille=60)
chiffre(s, 9.7, 3.65, 3.03, 1.9, "9", "dimensions", taille=60)
forme(s, 0.6, 5.8, 12.13, 1.0, VIOLET_FONCE)
texte(s, [[("Grain : ", {"taille": 26, "couleur": ROSE, "gras": True}), ("1 ligne = 1 événement", {"taille": 26, "gras": True})]],
      0.6, 5.8, 12.13, 1.0, couleur=BLANC, align=PP_ALIGN.CENTER)
notes(s, "Mako, 1,5 min.\n"
         "Merci Fatouma. Nous avons choisi un schéma en étoile, avec deux tables de faits au centre : les incidents et les observations de sécurité. "
         "Autour d'elles, neuf dimensions. Trois sont communes aux deux faits, en rose : la date, l'heure et la zone. "
         "Les incidents en ont quatre en propre : l'engin, le travailleur, le type et la gravité ; les observations en ont deux : le type d'observation et le rôle du déclarant. "
         "Le grain est le plus fin possible : une ligne par événement. Les deux faits ne sont jamais joints directement, ils se rejoignent par les dimensions communes.\n"
         "Détail si on nous interroge (source : 04_ETL/dwh_conception.md) : fact_incident, 1 400 lignes, clés date, heure, zone, engin, travailleur, type, gravité, "
         "mesures incident_count, is_serious, is_near_miss, severity_weight. fact_safety_observation, 3 500 lignes, clés date, heure, zone, type d'observation, rôle du déclarant, "
         "mesures observation_count, is_unsafe, is_near_miss. Dimensions : dim_date 301 jours ; dim_hour 24 heures ; dim_location 25 zones ; dim_equipment 40 engins ; "
         "dim_worker 350 travailleurs ; dim_incident_type 6 types ; dim_severity 4 niveaux ; dim_observation_type 3 types ; dim_reporter_role 3 rôles.")

# ------------------------------------------------------------------ 7. ETL et qualité (Mako, 3 min)
s = nouvelle()
titre(s, "ETL et qualité des données", "Chaque ligne rejetée est tracée")
couches = [("RAW", "5 315 lignes", VIOLET_FONCE, BLANC), ("STAGING", "5 315 propres", VIOLET, BLANC),
           ("CORE", "4 900 faits", VIOLET_CLAIR, BLANC), ("MART", "75 lignes", ROSE, VIOLET_FONCE)]
for i, (nom, v, c, ct) in enumerate(couches):
    x = 0.6 + i * 3.1
    forme(s, x, 1.45, 2.75, 1.3, c)
    paras = [[(nom, {"taille": 18, "gras": True})], [(v, {"taille": 24, "gras": True})]]
    if nom == "STAGING":
        paras.append([("0 rejet", {"taille": 18, "gras": True})])
    texte(s, paras, x, 1.45, 2.75, 1.3, couleur=ct, align=PP_ALIGN.CENTER)
    if i < 3:
        fleche(s, x + 2.8, 1.9, 0.27, 0.4, FRAMBOISE)
texte(s, "4 900 faits = 1 400 incidents + 3 500 observations ; les 415 autres lignes alimentent les dimensions",
      0.6, 2.8, 12.13, 0.6, taille=18, couleur=GRIS, align=PP_ALIGN.CENTER)
chiffre(s, 0.6, 3.5, 3.9, 1.7, "12", "règles de qualité, DQ01 à DQ12", taille=60, fond_=VIOLET_FONCE, c_grand=ROSE, c_label=BLANC)
chiffre(s, 4.7, 3.5, 3.9, 1.7, "11 = 11", "anomalies injectées, rejets tracés", taille=60)
forme(s, 8.8, 3.5, 3.93, 1.7, BLANC, LAVANDE)
texte(s, [[("Idempotence", {"taille": 26, "gras": True, "couleur": VIOLET})], [("2 runs, même base", {"taille": 18})],
          [("Rollback", {"taille": 26, "gras": True, "couleur": VIOLET})], [("panne : l'ancienne base reste", {"taille": 18})]],
      8.8, 3.5, 3.93, 1.7, align=PP_ALIGN.CENTER)
alertes = [("ALERTE DQ10", "+29,5 %", "mai : 171 incidents contre 132 en avril"), ("ALERTE DQ11", "40 / 40", "engins : home_area sans lien avec les zones")]
for i, (a, g, l) in enumerate(alertes):
    x = 0.6 + i * 6.2
    forme(s, x, 5.4, 5.93, 1.6, ROSE_PALE, FRAMBOISE)
    texte(s, a, x + 0.2, 5.45, 5.5, 0.45, taille=20, couleur=FRAMBOISE, gras=True)
    texte(s, g, x + 0.2, 5.9, 3.0, 1.0, taille=60, couleur=FRAMBOISE, gras=True)
    texte(s, l, x + 3.2, 5.9, 2.65, 1.0, taille=18, couleur=TEXTE)
notes(s, "Mako, 3 min.\n"
         "Notre ETL est un seul script Python qui fait passer les données par quatre couches. RAW garde une copie fidèle des 5 315 lignes. "
         "STAGING nettoie et contrôle : les 5 315 lignes sont valides, aucune n'est rejetée. CORE construit le schéma en étoile avec 4 900 faits : "
         "1 400 incidents plus 3 500 observations ; les 415 autres lignes, zones, travailleurs et engins, alimentent les dimensions. MART calcule 75 lignes prêtes pour l'analyse. "
         "À chaque run, une réconciliation vérifie que les lignes reçues égalent les lignes rejetées plus les lignes chargées : un écart arrête le run.\n"
         "Nous appliquons 12 règles de qualité, de DQ01 à DQ12, alors que le sujet en demandait 6. Les données fournies sont propres, elles ne produisent aucun rejet. "
         "Pour prouver que les contrôles marchent, notre script de test injecte 11 anomalies et obtient 11 rejets tracés, chacun avec sa raison. "
         "Il prouve aussi que deux runs donnent la même base, c'est l'idempotence, et qu'après une panne l'ancienne base reste en place, c'est le rollback.\n"
         "Deux alertes restent. DQ10 : mai compte 171 incidents contre 132 en avril, soit plus 29,5 pour cent ; ce n'est pas une erreur, c'est un signal métier. "
         "DQ11 : le champ home_area des 40 engins ne correspond à aucune zone ; c'est une limite des données sources.")

# ------------------------------------------------------------------ 8. HDFS (Fatouma, 1,5 min)
s = nouvelle()
titre(s, "Archivage HDFS", "L'archive HDFS garde l'historique brut en deux exemplaires")
chiffre(s, 0.6, 1.55, 3.4, 1.7, "23", "fichiers archivés", taille=60)
chiffre(s, 0.6, 3.45, 3.4, 1.7, "2", "copies de chaque fichier", taille=60)
forme(s, 4.25, 1.55, 8.48, 3.6, LAVANDE, VIOLET, pointille=True)
texte(s, "Docker", 4.4, 1.6, 2, 0.45, taille=20, couleur=VIOLET, gras=True)
forme(s, 6.5, 2.05, 4.0, 1.0, VIOLET_FONCE)
texte(s, "NameNode", 6.5, 2.05, 4.0, 1.0, taille=28, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
for x in (4.7, 8.5):
    ligne(s, 8.5, 3.05, x + 1.75, 3.55, epaisseur=4)
    forme(s, x, 3.55, 3.5, 1.0, VIOLET)
    texte(s, "DataNode", x, 3.55, 3.5, 1.0, taille=28, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
texte(s, "réplication 2", 4.7, 4.6, 7.3, 0.5, taille=22, couleur=FRAMBOISE, gras=True, align=PP_ALIGN.CENTER)
pastilles = ["prepare_archive.py", "HDFS", "hdfs_verify.py : MD5", "Parquet : 7 MART"]
largeurs = [2.8, 1.6, 3.3, 2.7]
x = 0.6
for i, (p, w) in enumerate(zip(pastilles, largeurs)):
    forme(s, x, 5.5, w, 1.0, VIOLET_FONCE if i != 1 else VIOLET)
    texte(s, p, x, 5.5, w, 1.0, taille=20, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
    if i < 3:
        fleche(s, x + w + 0.07, 5.8, 0.33, 0.4, FRAMBOISE)
    x += w + 0.47
notes(s, "Fatouma, 1,5 min.\n"
         "HDFS garde l'historique brut, car le Data Warehouse, lui, est reconstruit à chaque run. Notre cluster tourne sous Docker : un NameNode, qui tient l'annuaire, et deux DataNodes, qui stockent les données. "
         "La réplication est réglée à 2 : chaque fichier existe en deux exemplaires. Notre script prépare une archive de 23 fichiers, un par mois, avec un manifeste d'empreintes MD5. "
         "Un autre script, hdfs_verify, compare ce qui est dans HDFS au manifeste, et les sept tables MART sont exportées en Parquet.\n"
         "Attention : ne citer aucun résultat d'exécution (fsck, test d'arrêt d'un DataNode) tant qu'il n'est pas dans le rapport.")

# ------------------------------------------------------------------ 9. KPI et EDA (Fatouma, 2 min)
s = nouvelle()
titre(s, "KPI et analyse exploratoire", "Plus d'un incident sur cinq est grave")
hauteur = 2.2
x = 0.6
for chemin, w in [("07_EDA/figures/01_tendance_mensuelle.png", 4.89), ("07_EDA/figures/03_zones_risque.png", 3.52), ("07_EDA/figures/02_gravite.png", 3.42)]:
    forme(s, x - 0.05, 1.5, w + 0.1, hauteur + 0.1, BLANC, LAVANDE)
    image(s, chemin, x, 1.55, h=hauteur)
    x += w + 0.25
kpis = [("144,0", None, "incidents par mois"), ("22,3", " %", "incidents graves"), ("95,4", None, "score de la zone LOC015"),
        ("18,1", " %", "SPILL, type le plus fréquent"), ("4,84", None, "incidents par opérateur, équipe A")]
for i, (g, u, l) in enumerate(kpis):
    chiffre(s, 0.6 + i * 2.5, 4.05, 2.3, 2.75, g, l, taille=60, unite=u, fond_=VIOLET_FONCE if i == 1 else BLANC,
            c_grand=ROSE if i == 1 else VIOLET, c_label=BLANC if i == 1 else GRIS)
notes(s, "Fatouma, 2 min.\n"
         "Notre analyse en Python lit seulement les tables MART. Voici trois de nos six graphiques : les incidents par mois, les zones à plus fort risque et la répartition par gravité. "
         "En moyenne, 144 incidents par mois sur les mois complets, octobre étant exclu car il s'arrête au 28. "
         "22,3 pour cent des incidents sont graves. La zone LOC015, un parc à conteneurs, a le score de risque le plus élevé, 95,4. "
         "Le type le plus fréquent est le déversement, SPILL, à 18,1 pour cent, et le groupe le plus touché est celui des opérateurs de l'équipe A, avec 4,84 incidents par travailleur. "
         "Ce dernier chiffre est un signal à vérifier, pas une preuve.")

# ------------------------------------------------------------------ 10. gouvernance (Mako, 1,5 min)
s = nouvelle()
titre(s, "Gouvernance, sécurité et lineage", "Le worker_id ne quitte jamais la couche confidentielle")
niveaux = [("Confidentiel", "RAW · STAGING · CORE", "contiennent worker_id", FRAMBOISE, BLANC),
           ("Interne", "MART et suivi", "agrégats, 0 worker_id", VIOLET, BLANC),
           ("Public", "rapport, présentation", "agrégats seulement", ROSE, VIOLET_FONCE)]
for i, (n, a, b, c, ct) in enumerate(niveaux):
    x = 0.6 + i * 4.2
    forme(s, x, 1.65, 3.7, 2.5, c)
    texte(s, [[(n, {"taille": 30, "gras": True})], [(a, {"taille": 20})], [(b, {"taille": 18})]], x, 1.65, 3.7, 2.5, couleur=ct, align=PP_ALIGN.CENTER)
    if i < 2:
        fleche(s, x + 3.76, 2.65, 0.38, 0.5, VIOLET_FONCE)
chiffre(s, 0.6, 4.45, 3.7, 2.35, "36", "liens de lineage, de la source au chiffre", taille=60)
forme(s, 4.8, 4.45, 3.7, 2.35, BLANC, LAVANDE)
texte(s, [[("Moindre privilège", {"taille": 26, "gras": True, "couleur": VIOLET})], [("Politique écrite : SQLite ne l'applique pas", {"taille": 18, "couleur": FRAMBOISE, "gras": True})]],
      4.8, 4.45, 3.7, 2.35, align=PP_ALIGN.CENTER)
forme(s, 9.0, 4.45, 3.73, 2.35, BLANC, LAVANDE)
texte(s, [[("2 propriétaires", {"taille": 26, "gras": True, "couleur": VIOLET})], [("HSE (métier)", {"taille": 20})], [("data engineer (technique)", {"taille": 20})]],
      9.0, 4.45, 3.73, 2.35, align=PP_ALIGN.CENTER)
notes(s, "Mako, 1,5 min.\n"
         "Une seule colonne est sensible : worker_id, l'identifiant du travailleur. Elle reste dans les couches confidentielles. "
         "Les tables MART et le dashboard ne contiennent que des agrégats. Nous appliquons le moindre privilège, mais disons-le clairement : "
         "c'est une politique écrite, SQLite ne gère pas les droits par utilisateur. Le lineage décrit 36 liens, ce qui permet de retrouver l'origine de chaque chiffre. "
         "Le propriétaire métier est le service HSE, le propriétaire technique est le data engineer.")

# ------------------------------------------------------------------ 11. démonstration (Fatouma 1 min puis Mako 1 min)
s = nouvelle()
titre(s, "Démonstration technique", "Le dashboard est en ligne : démonstration en deux minutes")
forme(s, 0.55, 1.5, 7.2, 3.45, BLANC, LAVANDE)
image(s, "08_DELIVERABLES/images/dashboard_haut.png", 0.65, 1.6, h=3.25)
forme(s, 8.0, 1.5, 4.78, 3.45, BLANC, LAVANDE)
image(s, "08_DELIVERABLES/images/dashboard_qualite_cartes_tableau.png", 8.1, 1.6, h=3.25)
etapes = [("1", "Filtres"), ("2", "8 cartes KPI"), ("3", "Qualité des données")]
for i, (n, t) in enumerate(etapes):
    x = 0.6 + i * 2.65
    forme(s, x, 5.2, 0.7, 0.7, FRAMBOISE, type_=MSO_SHAPE.OVAL)
    texte(s, n, x, 5.2, 0.7, 0.7, taille=24, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
    texte(s, t, x + 0.75, 5.2, 1.85, 0.7, taille=18, couleur=VIOLET_FONCE, gras=True)
forme(s, 8.6, 5.2, 4.13, 0.7, VIOLET_FONCE)
texte(s, "Plan B : ces captures et le PDF", 8.6, 5.2, 4.13, 0.7, taille=20, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
forme(s, 0.6, 6.15, 12.13, 0.75, ROSE_PALE, ROSE)
texte(s, "https://projet11-port-safety.streamlit.app/", 0.6, 6.15, 12.13, 0.75, taille=28, couleur=VIOLET_FONCE, gras=True, align=PP_ALIGN.CENTER)
notes(s, "Fatouma 1 min, puis Mako 1 min (2 min en tout).\n"
         "Fatouma : nous ouvrons le dashboard à l'adresse affichée. En haut, trois filtres, la période, les types de zone et les équipes, puis les huit cartes KPI et les six graphiques. "
         "Je change la période et je montre que les graphiques suivent.\n"
         "Mako : tout en bas, la section Qualité des données montre les 12 règles avec leur statut en couleur, le dernier run de l'ETL et l'explication des deux alertes. "
         "Plan B si le réseau coupe : nous montrons les captures de cette slide, qui sont celles du dashboard, et nous avons le PDF de la présentation.")

# ------------------------------------------------------------------ 12. conclusion (Fatouma 1 min puis Mako 0,5 min)
s = nouvelle(VIOLET_FONCE)
titre(s, "Conclusion et recommandations", "Cinq actions pour le service HSE, et des limites assumées", BLANC, ROSE)
actions = [("OÙ", "Rondes renforcées sur LOC015 et LOC014"), ("QUAND", "Chercher la cause du pic de mai"),
           ("QUI", "Briefings pour les opérateurs de l'équipe A"), ("GRAVITÉ", "Réduire la part de 22,3 % d'incidents graves"),
           ("SIGNAUX FAIBLES", "Encourager la déclaration des near-miss")]
for i, (t, d) in enumerate(actions):
    x = 0.6 + i * 2.5
    forme(s, x, 1.55, 2.3, 3.1, BLANC)
    texte(s, t, x, 1.65, 2.3, 0.9, taille=22, couleur=FRAMBOISE, gras=True, align=PP_ALIGN.CENTER)
    texte(s, d, x, 2.6, 2.3, 1.9, taille=20, couleur=VIOLET_FONCE, align=PP_ALIGN.CENTER, ancrage=MSO_ANCHOR.TOP)
forme(s, 0.6, 4.9, 12.13, 1.3, "5E2A85")
texte(s, "Limites", 0.8, 4.9, 1.8, 1.3, taille=24, couleur=ROSE, gras=True)
for i, (t, w) in enumerate([("données synthétiques", 3.0), ("petit volume", 2.3), ("home_area sans lien avec les zones", 4.4)]):
    x = 2.7 + [0, 3.15, 5.65][i]
    forme(s, x, 5.15, w, 0.8, LAVANDE)
    texte(s, t, x, 5.15, w, 0.8, taille=18, couleur=VIOLET_FONCE, gras=True, align=PP_ALIGN.CENTER)
texte(s, "Merci de votre attention. Questions ?", 0.6, 6.25, 12.13, 0.7, taille=28, couleur=ROSE, gras=True, align=PP_ALIGN.CENTER)
notes(s, "Fatouma 1 min (les actions), puis Mako 0,5 min (les limites et la conclusion) ; 1,5 min en tout.\n"
         "Fatouma : nos données conduisent à cinq actions. Où : renforcer les rondes sur LOC015 et LOC014, les deux parcs à conteneurs. Quand : chercher la cause du pic de mai. "
         "Qui : un briefing renforcé pour les opérateurs de l'équipe A. Gravité : réduire la part de 22,3 pour cent d'incidents graves. Signaux faibles : encourager la déclaration des near-miss.\n"
         "Mako : les limites sont claires. Les données sont synthétiques, le volume est petit, et le champ home_area des engins ne correspond à aucune zone. "
         "Ces recommandations montrent le type de décision que le dispositif permet. Merci, nous sommes prêtes à répondre à vos questions.")

# ------------------------------------------------------------------ transitions (fondu)
NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
for sl in prs.slides:
    el = etree.SubElement(sl._element, f"{{{NS}}}transition", spd="med")
    etree.SubElement(el, f"{{{NS}}}fade")

# numéros de slide : petits, discrets, en bas à droite (slides 2 à 12)
n_total = len(prs.slides)
for k, sl in enumerate(prs.slides, 1):
    if k >= 2:
        sombre = (k == n_total)
        texte(sl, f"{k} / {n_total}", 11.73, 7.08, 1.0, 0.3, taille=12, couleur="D9C8EA" if sombre else GRIS, align=PP_ALIGN.RIGHT)

prs.save(SORTIE)
print("Présentation écrite :", SORTIE)
