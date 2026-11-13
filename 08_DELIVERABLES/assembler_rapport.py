"""
Projet 11 : assembler les sections du rapport (fichiers .md) en un seul PDF.
Page de garde, sommaire avec numéros de page, sections, annexes.
Lancement depuis la racine du projet :  python 08_DELIVERABLES/assembler_rapport.py
Besoins : le paquet Python mistune (pip install mistune) et Google Chrome ou Microsoft Edge
(utilisé sans fenêtre pour imprimer la page HTML en PDF).
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import mistune

DOSSIER_RAPPORT = Path(__file__).resolve().parent
PDF_FINAL = DOSSIER_RAPPORT / "rapport_final_projet11.pdf"
LOGO = DOSSIER_RAPPORT.parent / "12_DASHBOARD" / "assets" / "logo_ud.jpg"

# Les sections, dans l'ordre du rapport
SECTIONS = [
    "00_resume.md",
    "01_contexte.md",
    "02_sources_5v.md",
    "03_sql.md",
    "04_data_warehouse.md",
    "05_etl.md",
    "06_hdfs.md",
    "07_gouvernance.md",
    "08_eda.md",
    "09_kpi.md",
    "10_architecture.md",
    "11_recommandations.md",
    "12_annexes.md",
]
# Sections qui commencent sur une nouvelle page (les autres s'enchaînent)
NOUVELLE_PAGE = ["00_resume.md", "01_contexte.md", "12_annexes.md"]

NAVIGATEURS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

# ---------------------------------------------------------------------
# Mise en page (couleurs de la charte graphique du README)
# ---------------------------------------------------------------------
STYLE = """
@page { size: A4; margin: 2cm 2cm 2.1cm 2cm;
        @bottom-center { content: counter(page); font-family: 'Segoe UI', Arial, sans-serif; font-size: 9pt; color: #6B6375; }
        @top-right { content: "Projet 11 : Port Safety & Incident Analytics"; font-family: 'Segoe UI', Arial, sans-serif; font-size: 8pt; color: #9A93A3; } }
@page :first { @bottom-center { content: none; } @top-right { content: none; } }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 10pt; line-height: 1.38; color: #2B2333; margin: 0; }
h1 { font-size: 17pt; color: #4A1D6E; border-bottom: 3px solid #EE82B7; padding-bottom: 5px; margin: 26px 0 10px 0; break-after: avoid; }
h1.nouvelle-page { break-before: page; margin-top: 0; }
h1 + h2 { margin-top: 6px; }
h1 + h2 + p, h1 + p { break-inside: avoid; }
h2 { font-size: 12pt; color: #4A1D6E; margin: 11px 0 5px 0; break-after: avoid; }
p { margin: 0 0 6px 0; text-align: justify; orphans: 3; widows: 3; }
ul { margin: 0 0 6px 0; padding-left: 20px; }
li { margin-bottom: 3px; text-align: justify; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 9pt; color: #4A1D6E; background: #F4EFF9; padding: 0 2px; border-radius: 2px; }
em.source { font-size: 8.5pt; color: #6B6375; }
table { border-collapse: collapse; width: 100%; margin: 3px 0 7px 0; font-size: 8.6pt; line-height: 1.25; }
th { background: #4A1D6E; color: #FFFFFF; text-align: left; padding: 4px 6px; font-weight: 600; }
td { border-bottom: 1px solid #D9C8EA; padding: 3px 6px; vertical-align: top; }
tr { break-inside: avoid; }
tr:nth-child(even) td { background: #FAF7FD; }
td code, th code { font-size: 8.3pt; background: none; padding: 0; }
p.legende { margin: 7px 0 3px 0; break-after: avoid; }
p.legende strong { color: #7B3FA0; }
table + p.legende, p.figure + p.legende { break-after: auto; }
p.figure { text-align: center; margin: 10px 0 4px 0; break-after: avoid; break-inside: avoid; }
p.figure img { max-width: 100%; max-height: 10.8cm; }
p.deux-figures img { width: 49%; max-height: 6.2cm; object-fit: contain; vertical-align: top; }
span.marqueur { background: #FFE98A; color: #7A4B00; font-weight: 700; padding: 1px 4px; border-radius: 3px; }
/* Page de garde */
.garde { height: 25cm; display: flex; flex-direction: column; text-align: center; }
.garde .haut { color: #4A1D6E; font-size: 11pt; letter-spacing: 0.5px; }
.garde img { height: 3.2cm; margin: 0 auto 12px auto; display: block; }
.garde .bandeau { background: linear-gradient(90deg, #4A1D6E 0%, #7B3FA0 60%, #EE82B7 100%); color: #FFFFFF; border-radius: 14px; padding: 34px 26px; margin-top: 3.2cm; }
.garde .bandeau .projet { font-size: 12pt; letter-spacing: 2px; }
.garde .bandeau .titre { font-size: 26pt; font-weight: 700; margin: 10px 0; line-height: 1.2; }
.garde .bandeau .sous-titre { font-size: 13pt; color: #EDE4F5; }
.garde .type { font-size: 15pt; color: #4A1D6E; font-weight: 600; margin-top: 1.6cm; }
.garde .auteurs { margin-top: 1.4cm; font-size: 12pt; line-height: 1.8; }
.garde .auteurs b { color: #4A1D6E; }
.garde .bas { margin-top: auto; font-size: 10.5pt; color: #6B6375; line-height: 1.7; }
/* Sommaire */
.sommaire h1 { break-before: page; margin-top: 0; }
.sommaire table { font-size: 11pt; line-height: 1.5; }
.sommaire td { border-bottom: 1px dotted #C9BCD8; padding: 7px 4px; background: none !important; }
.sommaire td.page { text-align: right; width: 2cm; color: #4A1D6E; font-weight: 600; }
"""

PAGE_DE_GARDE = f"""
<div class="garde">
  <img src="{LOGO.as_uri()}" alt="Logo">
  <div class="haut">Université de Djibouti<br>Master 2 IAMD · Gestion des Données Massives · Examen final</div>
  <div class="bandeau">
    <div class="projet">PROJET 11</div>
    <div class="titre">Port Safety &amp; Incident Analytics</div>
    <div class="sous-titre">Incidents, near-miss et zones à risque</div>
  </div>
  <div class="type">Rapport final</div>
  <div class="auteurs">
    Présenté par<br>
    <b>Mako Mohamed Aden</b><br>
    <b>Fatouma Soubere Mahamoud</b>
  </div>
  <div class="bas">
    Enseignant : <span class="marqueur">[À COMPLÉTER : nom de l'enseignant]</span><br>
    Soutenance du 16 novembre 2026<br>
    Toutes les données sont synthétiques : aucune donnée personnelle réelle n'est utilisée.
  </div>
</div>
"""

markdown = mistune.create_markdown(plugins=["table"])


def en_html(texte_md):
    """Convertit une section Markdown en HTML et applique les classes de mise en page."""
    html = markdown(texte_md)
    # Marqueurs visibles
    html = re.sub(r"\[À COMPLÉTER : [^\]]*\]", lambda m: f'<span class="marqueur">{m.group(0)}</span>', html)
    # Titres numérotés des tableaux et des figures
    html = re.sub(r"<p>(<strong>(?:Tableau|Figure) \d+\.)", r'<p class="legende">\1', html)
    # Paragraphes d'images : une image seule, ou deux images côte à côte
    html = re.sub(r"<p>(<img [^>]*>\s*<img [^>]*>)</p>", r'<p class="figure deux-figures">\1</p>', html)
    html = re.sub(r"<p>(<img [^>]*>)</p>", r'<p class="figure">\1</p>', html)
    # Sources et déductions, en petit
    html = re.sub(r"<em>((?:Source|Déduction)[^<]*(?:<code>[^<]*</code>[^<]*)*)</em>", r'<em class="source">\1</em>', html)
    return html


def page_html(corps):
    return f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>Rapport Projet 11</title><style>{STYLE}</style></head><body>{corps}</body></html>'


def trouver_navigateur():
    for chemin in NAVIGATEURS:
        if Path(chemin).exists():
            return chemin
    sys.exit("Chrome ou Edge introuvable : impossible de produire le PDF.")


def imprimer_pdf(navigateur, corps, fichier_html, fichier_pdf, profil):
    """Écrit la page HTML puis l'imprime en PDF avec le navigateur, sans fenêtre."""
    fichier_html.write_text(page_html(corps), encoding="utf-8")
    subprocess.run([navigateur, "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                    f"--user-data-dir={profil}", f"--print-to-pdf={fichier_pdf}", fichier_html.as_uri()],
                   check=True, capture_output=True, timeout=180)
    return compter_pages(fichier_pdf)


def compter_pages(fichier_pdf):
    """Compte les pages d'un PDF (objets /Type /Page, sans les /Pages)."""
    return len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", fichier_pdf.read_bytes()))


def sommaire_html(titres, pages):
    lignes = "".join(f'<tr><td>{titre}</td><td class="page">{page}</td></tr>' for titre, page in zip(titres, pages))
    return f'<div class="sommaire"><h1>Sommaire</h1><table>{lignes}</table></div>'


navigateur = trouver_navigateur()

# 1. Convertir chaque section
sections_html = []
titres = []
for nom in SECTIONS:
    texte = (DOSSIER_RAPPORT / nom).read_text(encoding="utf-8")
    titres.append(re.search(r"^# (.+)$", texte, re.MULTILINE).group(1))
    html = en_html(texte)
    if nom in NOUVELLE_PAGE:
        html = html.replace("<h1>", '<h1 class="nouvelle-page">', 1)
    sections_html.append(html)

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    profil = temp / "profil"

    # Les fichiers HTML temporaires sont écrits dans 08_DELIVERABLES pour que les images
    # (chemins relatifs ../07_EDA/figures/...) soient trouvées.
    brouillon = DOSSIER_RAPPORT / "_brouillon.html"
    try:
        # 2. Page de début de chaque section. On imprime le document coupé juste après le titre,
        #    le premier sous-titre et le premier paragraphe de la section (ils restent toujours
        #    sur la même page) : le nombre de pages obtenu est le numéro de la page du titre.
        sommaire_provisoire = sommaire_html(titres, ["0"] * len(titres))
        pages_debut = []
        for i, html in enumerate(sections_html):
            fin_du_debut = html.index("</p>") + len("</p>")
            corps = PAGE_DE_GARDE + sommaire_provisoire + "".join(sections_html[:i]) + html[:fin_du_debut]
            pages_debut.append(imprimer_pdf(navigateur, corps, brouillon, temp / f"debut_{i}.pdf", profil))

        # 3. Le document complet
        corps = PAGE_DE_GARDE + sommaire_html(titres, pages_debut) + "".join(sections_html)
        total = imprimer_pdf(navigateur, corps, brouillon, PDF_FINAL, profil)
    finally:
        if brouillon.exists():
            brouillon.unlink()

for titre, debut in zip(titres, pages_debut):
    print(f"  page {debut:>2} : {titre}")
print()
print(f"PDF écrit : {PDF_FINAL.name}, {total} pages")
if not 20 <= total <= 30:
    print("ATTENTION : le sujet demande un dossier de 20 à 30 pages.")
marqueurs = sum(len(re.findall(r"\[À COMPLÉTER", (DOSSIER_RAPPORT / nom).read_text(encoding="utf-8"))) for nom in SECTIONS)
print(f"Marqueurs [À COMPLÉTER] restants dans les sections : {marqueurs} (plus 1 sur la page de garde)")
