"""
Projet 11 : construit la présentation de soutenance (12 slides) avec python-pptx.
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


def titre(slide, t, couleur=VIOLET_FONCE):
    texte(slide, t, 0.6, 0.35, 12.13, 1.0, taille=34, couleur=couleur, gras=True)


def etiquette(slide, nom, couleur=GRIS):
    texte(slide, nom, 0.6, 7.0, 4, 0.3, taille=12, couleur=couleur)


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


# ------------------------------------------------------------------ 1. titre
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
notes(s, "Durée prévue : 30 secondes. Qui parle : Mako.\n"
         "Bonjour, nous présentons le projet 11, Port Safety & Incident Analytics, réalisé avec Fatouma en Master 2 IAMD. "
         "Je m'appelle Mako et je vais présenter le Data Warehouse, l'ETL et la gouvernance ; Fatouma présentera HDFS et l'analyse. "
         "Nous vous montrerons aussi le dashboard en ligne.")

# ------------------------------------------------------------------ 2. contexte
s = nouvelle()
titre(s, "Le service HSE a des fichiers, pas encore de réponses")
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
etiquette(s, "Mako · 1 min")
notes(s, "Durée prévue : 1 minute. Qui parle : Mako.\n"
         "Le service HSE est chargé de la sécurité des personnes sur un terminal portuaire. Il dispose de cinq fichiers CSV : deux listent des événements, "
         "les incidents et les observations, et trois décrivent le site, les zones, les travailleurs et les engins. "
         "Tels quels, ils ne répondent à rien. Notre question est donc : où, quand, comment et à qui arrivent les incidents ?")

# ------------------------------------------------------------------ 3. données et 5V
s = nouvelle()
titre(s, "5 315 lignes : un petit jeu d'enseignement, assumé")
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
etiquette(s, "Fatouma · 1 min")
notes(s, "Durée prévue : 1 minute. Qui parle : Fatouma.\n"
         "Nos données comptent 5 315 lignes : 1 400 incidents, 3 500 observations, 25 zones, 350 travailleurs et 40 engins. "
         "Soyons francs : le volume est petit, 260 kilo-octets, c'est un jeu d'enseignement et non du vrai Big Data. "
         "Nous appliquons donc les méthodes du cours avec une architecture pensée pour un historique qui grandit. "
         "Sur les 5V, la vélocité est une hypothèse de notre part : le jeu est statique, nous traitons par lot.")

# ------------------------------------------------------------------ 4. architecture
s = nouvelle()
titre(s, "Des fichiers CSV aux décisions HSE, en six blocs")
image(s, "09_PRESENTATION/architecture_simplifiee.png", 0.5, 1.6, w=12.33)
etiquette(s, "Mako · 1,5 min")
notes(s, "Durée prévue : 1 minute 30. Qui parle : Mako.\n"
         "Voici toute la chaîne en six blocs. Les cinq fichiers CSV alimentent le Data Warehouse, qui compte quatre couches. "
         "Les mêmes sources sont aussi archivées dans HDFS pour garder l'historique brut. "
         "À partir du Data Warehouse, on fait deux choses : l'analyse exploratoire en Python et le dashboard en ligne. "
         "Tout cela sert un seul but : les décisions du service HSE.")

# ------------------------------------------------------------------ 5. data warehouse
s = nouvelle()
titre(s, "Un schéma en étoile : 2 tables de faits, 9 dimensions")
forme(s, 0.6, 1.55, 8.9, 4.0, FOND, LAVANDE)
image(s, "09_PRESENTATION/schema_etoile_simplifie.png", 0.75, 1.65, w=8.6)
chiffre(s, 9.7, 1.55, 3.03, 1.9, "2", "tables de faits", taille=60)
chiffre(s, 9.7, 3.65, 3.03, 1.9, "9", "dimensions", taille=60)
forme(s, 0.6, 5.8, 12.13, 1.0, VIOLET_FONCE)
texte(s, [[("Grain : ", {"taille": 26, "couleur": ROSE, "gras": True}), ("1 ligne = 1 événement", {"taille": 26, "gras": True})]],
      0.6, 5.8, 12.13, 1.0, couleur=BLANC, align=PP_ALIGN.CENTER)
etiquette(s, "Mako · 1,5 min")
notes(s, "Durée prévue : 1 minute 30. Qui parle : Mako.\n"
         "Nous avons choisi un schéma en étoile, avec deux tables de faits au centre : les incidents et les observations de sécurité. "
         "Autour d'elles, neuf dimensions. Trois sont communes aux deux faits, en rose : la date, l'heure et la zone. "
         "Les incidents en ont quatre en propre : l'engin, le travailleur, le type et la gravité ; les observations en ont deux : le type d'observation et le rôle du déclarant. "
         "Le grain est le plus fin possible : une ligne par événement. Les deux faits ne sont jamais joints directement, ils se rejoignent par les dimensions communes.\n"
         "Détail si on nous interroge (source : 04_ETL/dwh_conception.md) : fact_incident, 1 400 lignes, clés date, heure, zone, engin, travailleur, type, gravité, "
         "mesures incident_count, is_serious, is_near_miss, severity_weight. fact_safety_observation, 3 500 lignes, clés date, heure, zone, type d'observation, rôle du déclarant, "
         "mesures observation_count, is_unsafe, is_near_miss. Dimensions : dim_date 301 jours ; dim_hour 24 heures ; dim_location 25 zones ; dim_equipment 40 engins ; "
         "dim_worker 350 travailleurs ; dim_incident_type 6 types ; dim_severity 4 niveaux ; dim_observation_type 3 types ; dim_reporter_role 3 rôles.")

# ------------------------------------------------------------------ 6. ETL
s = nouvelle()
titre(s, "Quatre couches, et aucune ligne perdue en route")
couches = [("RAW", "5 315", "lignes copiées", VIOLET_FONCE, BLANC), ("STAGING", "0", "rejet", VIOLET, BLANC),
           ("CORE", "4 900", "faits", VIOLET_CLAIR, BLANC), ("MART", "75", "lignes d'analyse", ROSE, VIOLET_FONCE)]
for i, (nom, n, l, c, ct) in enumerate(couches):
    x = 0.6 + i * 3.2
    forme(s, x, 1.65, 2.7, 3.0, c)
    texte(s, nom, x, 1.7, 2.7, 0.6, taille=26, couleur=ct, gras=True, align=PP_ALIGN.CENTER)
    texte(s, n, x, 2.3, 2.7, 1.5, taille=66, couleur=ct, gras=True, align=PP_ALIGN.CENTER)
    texte(s, l, x, 3.8, 2.7, 0.7, taille=20, couleur=ct, align=PP_ALIGN.CENTER)
    if i < 3:
        fleche(s, x + 2.78, 2.85, 0.34, 0.55, FRAMBOISE)
forme(s, 0.6, 5.0, 12.13, 1.8, BLANC, VIOLET)
texte(s, [[("Réconciliation : RAW = STAGING + rejets", {"taille": 26, "gras": True, "couleur": VIOLET_FONCE})],
          [("5 315 = 5 315 + 0", {"taille": 44, "gras": True, "couleur": FRAMBOISE})]], 0.6, 5.0, 12.13, 1.8, align=PP_ALIGN.CENTER)
etiquette(s, "Mako · 2 min")
notes(s, "Durée prévue : 2 minutes. Qui parle : Mako.\n"
         "Notre ETL est un seul script Python qui fait passer les données par quatre couches. RAW garde une copie fidèle : 5 315 lignes. "
         "STAGING nettoie et contrôle : aucune ligne n'est rejetée sur les données fournies. CORE construit le schéma en étoile avec 4 900 faits. "
         "MART calcule 75 lignes prêtes pour l'analyse. À chaque run, une réconciliation vérifie que les lignes reçues égalent les lignes rejetées plus les lignes chargées : "
         "si un écart apparaît, le run s'arrête.")

# ------------------------------------------------------------------ 7. qualité
s = nouvelle()
titre(s, "Chaque ligne rejetée est tracée")
forme(s, 0.6, 1.55, 3.5, 2.75, VIOLET_FONCE)
texte(s, [[("12", {"taille": 88, "gras": True})], [("règles de qualité", {"taille": 20, "couleur": ROSE, "gras": True})], [("DQ01 à DQ12", {"taille": 18})]],
      0.6, 1.55, 3.5, 2.75, couleur=BLANC, align=PP_ALIGN.CENTER)
preuves = [("11 = 11", "anomalies injectées, 11 rejets tracés"), ("2 runs", "idempotence : même base"), ("Rollback", "panne : l'ancienne base reste")]
for i, (g, l) in enumerate(preuves):
    x = 4.3 + i * 2.86
    forme(s, x, 1.55, 2.66, 2.75, BLANC, LAVANDE)
    texte(s, g, x, 1.65, 2.66, 1.2, taille=40, couleur=VIOLET, gras=True, align=PP_ALIGN.CENTER)
    texte(s, l, x, 2.9, 2.66, 1.3, taille=20, couleur=TEXTE, align=PP_ALIGN.CENTER, ancrage=MSO_ANCHOR.TOP)
alertes = [("ALERTE DQ10", "+29,5 %", "mai : 171 incidents contre 132 en avril"), ("ALERTE DQ11", "40 / 40", "engins : home_area sans lien avec les zones")]
for i, (a, g, l) in enumerate(alertes):
    x = 0.6 + i * 6.2
    forme(s, x, 4.6, 5.93, 2.2, ROSE_PALE, FRAMBOISE)
    texte(s, a, x + 0.2, 4.68, 5.5, 0.5, taille=20, couleur=FRAMBOISE, gras=True)
    texte(s, g, x + 0.2, 5.15, 2.9, 1.1, taille=60, couleur=FRAMBOISE, gras=True)
    texte(s, l, x + 3.1, 5.15, 2.7, 1.5, taille=18, couleur=TEXTE)
etiquette(s, "Mako · 2 min")
notes(s, "Durée prévue : 2 minutes. Qui parle : Mako.\n"
         "Nous appliquons 12 règles de qualité, de DQ01 à DQ12, alors que le sujet en demandait 6. Les données fournies sont propres, elles ne produisent aucun rejet. "
         "Pour prouver que les contrôles marchent, notre script de test injecte 11 anomalies et obtient 11 rejets tracés, chacun avec sa raison. "
         "Il prouve aussi que deux runs donnent la même base, et qu'après une panne l'ancienne base reste en place. "
         "Deux alertes restent : DQ10, le pic de mai à plus 29,5 pour cent, qui est un signal métier, et DQ11, le champ home_area des engins qui ne correspond à aucune zone.")

# ------------------------------------------------------------------ 8. gouvernance
s = nouvelle()
titre(s, "Le worker_id ne quitte jamais la couche confidentielle")
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
etiquette(s, "Mako · 1,5 min")
notes(s, "Durée prévue : 1 minute 30. Qui parle : Mako.\n"
         "Une seule colonne est sensible : worker_id, l'identifiant du travailleur. Elle reste dans les couches confidentielles. "
         "Les tables MART et le dashboard ne contiennent que des agrégats. Nous appliquons le moindre privilège, mais disons-le clairement : "
         "c'est une politique écrite, SQLite ne gère pas les droits par utilisateur. Le lineage décrit 36 liens, ce qui permet de retrouver l'origine de chaque chiffre. "
         "Le propriétaire métier est le service HSE, le propriétaire technique est le data engineer.")

# ------------------------------------------------------------------ 9. HDFS
s = nouvelle()
titre(s, "L'archive HDFS garde l'historique brut en deux exemplaires")
chiffre(s, 0.6, 1.55, 3.4, 1.7, "23", "fichiers archivés", taille=60)
chiffre(s, 0.6, 3.45, 3.4, 1.7, "2", "copies de chaque fichier", taille=60)
forme(s, 4.25, 1.55, 5.3, 3.6, LAVANDE, VIOLET, pointille=True)
texte(s, "Docker", 4.35, 1.58, 2, 0.4, taille=18, couleur=VIOLET, gras=True)
forme(s, 5.5, 2.0, 2.8, 0.85, VIOLET_FONCE)
texte(s, "NameNode", 5.5, 2.0, 2.8, 0.85, taille=22, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
for x in (4.5, 7.1):
    ligne(s, 6.9, 2.85, x + 1.1, 3.55)
    forme(s, x, 3.55, 2.2, 0.85, VIOLET)
    texte(s, "DataNode", x, 3.55, 2.2, 0.85, taille=22, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
texte(s, "réplication 2", 4.5, 4.45, 4.8, 0.55, taille=20, couleur=FRAMBOISE, gras=True, align=PP_ALIGN.CENTER)
forme(s, 9.8, 1.55, 2.93, 3.6, ROSE_PALE, FRAMBOISE, pointille=True)
texte(s, [[("CAPTURE À AJOUTER", {"taille": 20, "gras": True, "couleur": FRAMBOISE})], [("résultat de fsck ou page du NameNode (Fatouma)", {"taille": 18, "couleur": TEXTE})]],
      9.8, 1.55, 2.93, 3.6, align=PP_ALIGN.CENTER)
pastilles = ["prepare_archive.py", "HDFS", "hdfs_verify.py : MD5", "Parquet : 7 MART"]
largeurs = [2.8, 1.6, 3.3, 2.7]
x = 0.6
for i, (p, w) in enumerate(zip(pastilles, largeurs)):
    forme(s, x, 5.5, w, 1.0, VIOLET_FONCE if i != 1 else VIOLET)
    texte(s, p, x, 5.5, w, 1.0, taille=20, couleur=BLANC, gras=True, align=PP_ALIGN.CENTER)
    if i < 3:
        fleche(s, x + w + 0.07, 5.8, 0.33, 0.4, FRAMBOISE)
    x += w + 0.47
etiquette(s, "Fatouma · 1,5 min")
notes(s, "Durée prévue : 1 minute 30. Qui parle : Fatouma.\n"
         "HDFS garde l'historique brut, car le Data Warehouse, lui, est reconstruit à chaque run. Notre cluster tourne sous Docker : un NameNode, qui tient l'annuaire, et deux DataNodes, qui stockent les données. "
         "La réplication est réglée à 2. Notre script prépare une archive de 23 fichiers, un par mois, avec un manifeste d'empreintes MD5. "
         "Un autre script, hdfs_verify, compare ce qui est dans HDFS au manifeste, et les sept tables MART sont exportées en Parquet. "
         "[À compléter par Fatouma : commenter la capture des résultats fsck et du test d'arrêt d'un DataNode, une fois ajoutée.]")

# ------------------------------------------------------------------ 10. EDA et KPI
s = nouvelle()
titre(s, "Plus d'un incident sur cinq est grave")
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
etiquette(s, "Fatouma · 2 min")
notes(s, "Durée prévue : 2 minutes. Qui parle : Fatouma.\n"
         "Notre analyse en Python lit seulement les tables MART. Voici trois de nos six graphiques : les incidents par mois, les zones à plus fort risque et la répartition par gravité. "
         "En moyenne, 144 incidents par mois sur les mois complets, octobre étant exclu car il s'arrête au 28. "
         "22,3 pour cent des incidents sont graves. La zone LOC015, un parc à conteneurs, a le score de risque le plus élevé, 95,4. "
         "Le type le plus fréquent est le déversement, SPILL, à 18,1 pour cent, et le groupe le plus touché est celui des opérateurs de l'équipe A, avec 4,84 incidents par travailleur. "
         "Ce dernier chiffre est un signal à vérifier, pas une preuve.")

# ------------------------------------------------------------------ 11. démo
s = nouvelle()
titre(s, "Le dashboard est en ligne : démonstration en deux minutes")
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
etiquette(s, "Fatouma puis Mako · 2 min")
notes(s, "Durée prévue : 2 minutes. Qui parle : Fatouma pour les filtres et les cartes, puis Mako pour la section qualité.\n"
         "Nous ouvrons le dashboard à l'adresse affichée. Fatouma : en haut, trois filtres, la période, les types de zone et les équipes, puis les huit cartes KPI et les six graphiques. "
         "Mako : tout en bas, la section Qualité des données montre les 12 règles avec leur statut en couleur, le dernier run et l'explication des deux alertes. "
         "Plan B si le réseau coupe : nous montrons les captures de cette slide, qui sont celles du dashboard, et nous avons le PDF de la présentation.")

# ------------------------------------------------------------------ 12. recommandations
s = nouvelle(VIOLET_FONCE)
titre(s, "Cinq actions pour le service HSE, et des limites assumées", BLANC)
actions = [("OÙ", "Rondes renforcées sur LOC015 et LOC014"), ("QUAND", "Chercher la cause du pic de mai"),
           ("QUI", "Briefings pour les opérateurs de l'équipe A"), ("GRAVITÉ", "Objectif de baisse des 22,3 % de graves"),
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
etiquette(s, "Fatouma (actions), Mako (limites et conclusion) · 1,5 min", "D9C8EA")
notes(s, "Durée prévue : 1 minute 30. Qui parle : Fatouma pour les actions, Mako pour les limites et la conclusion.\n"
         "Fatouma : nos données conduisent à cinq actions. Où : renforcer les rondes sur LOC015 et LOC014, les deux parcs à conteneurs. Quand : chercher la cause du pic de mai. "
         "Qui : un briefing renforcé pour les opérateurs de l'équipe A. Gravité : fixer un objectif sur les 22,3 pour cent d'incidents graves. Signaux faibles : encourager la déclaration des near-miss.\n"
         "Mako : les limites sont claires. Les données sont synthétiques, le volume est petit, et le champ home_area des engins ne correspond à aucune zone. "
         "Ces recommandations montrent le type de décision que le dispositif permet. Merci, nous sommes prêtes à répondre à vos questions.")

# ------------------------------------------------------------------ transitions (fondu)
NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
for sl in prs.slides:
    el = etree.SubElement(sl._element, f"{{{NS}}}transition", spd="med")
    etree.SubElement(el, f"{{{NS}}}fade")

prs.save(SORTIE)
print("Présentation écrite :", SORTIE)
