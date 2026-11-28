# Résumé

Le service HSE (Hygiène, Sécurité, Environnement) d'un terminal portuaire veut savoir où, quand, comment et à qui arrivent les incidents. Il dispose de cinq fichiers synthétiques : 1 400 incidents, 3 500 observations de sécurité, 25 zones, 350 travailleurs et 40 engins, du 1er janvier au 28 octobre 2026.

Nous avons construit une chaîne de traitement complète. Une base SQL vérifie d'abord la cohérence des fichiers. Un programme Python, le pipeline, charge ensuite les 5 315 lignes dans un Data Warehouse, à travers quatre couches : copie brute, données contrôlées, modèle en étoile, tables d'analyse. Il applique 12 règles de qualité à chaque exécution. Trois tests prouvent qu'il donne le même résultat quand on le relance, qu'il écarte et explique les lignes fausses, et qu'il conserve la base précédente en cas de panne. L'historique est archivé par mois dans un stockage distribué HDFS. Une politique de gouvernance fixe les responsables, les accès et le chemin de chaque chiffre. Aucun identifiant de travailleur ne sort des couches confidentielles.

Huit indicateurs résument les résultats. Le terminal enregistre 144 incidents par mois complet, avec un pic en mai (171). Parmi les incidents, 22,3 % sont graves. Le risque se concentre sur le parc à conteneurs : la zone LOC015 obtient le score le plus élevé (95,4 sur 100). On compte 759 presque-accidents (near-miss). Le type d'incident le plus fréquent, le déversement, ne pèse que 18,1 % : aucun type ne domine. Les opérateurs de l'équipe A sont le groupe le plus exposé (4,84 incidents par travailleur).

Nous recommandons au service HSE de renforcer les rondes sur le parc à conteneurs, de chercher la cause du pic de mai, de fixer un objectif sur les incidents graves et d'encourager la déclaration des presque-accidents. Un dashboard en ligne affiche ces indicateurs et l'état de la qualité des données.

Les données sont synthétiques et de petit volume. Plusieurs définitions, comme « incident grave » ou le score de risque, sont des hypothèses du groupe, signalées dans chaque section.
