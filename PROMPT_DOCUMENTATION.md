# Prompt Claude Code — Documentation + Migration Odoo 19

## À coller dans Claude Code sur le serveur

```
Tu as deux missions :

## MISSION 1 — Documentation utilisateur complète

Génère une documentation utilisateur professionnelle pour le module Garage Pro. Elle doit être COMPLÈTE, claire, et destinée à des utilisateurs non-techniques (réceptionnistes, chefs d'atelier, comptables, gérants).

### Étapes
1. Lis TOUS les fichiers dans garage_pro/models/ pour lister chaque modèle, chaque champ, chaque workflow
2. Lis garage_pro/security/ pour comprendre les droits par groupe
3. Lis garage_pro/views/ pour comprendre les menus et la navigation
4. Lis garage_pro/data/ pour les séquences, templates email, crons

### Structure de la documentation (fichier docs/USER_GUIDE.md)

La documentation doit couvrir :

#### 1. Présentation générale
- À quoi sert le module
- Les 5 profils utilisateur (Réceptionniste, Technicien, Chef d'atelier, Comptable, Gérant)
- Schéma du flux principal (client arrive → devis → OR → facturation)

#### 2. Gestion des accès et sécurité
Pour CHAQUE groupe de sécurité défini dans security/ :
- Nom du groupe
- Ce qu'il peut VOIR (lecture)
- Ce qu'il peut FAIRE (écrire, créer, supprimer)
- Ce qu'il ne peut PAS faire
- Tableau récapitulatif : modèle × groupe × permissions (R/W/C/D)
- Comment modifier les accès : expliquer comment aller dans Configuration > Utilisateurs > modifier le groupe d'un utilisateur

#### 3. Guide par module fonctionnel
Pour chaque section (Véhicules, Clients, Assurances, Devis, OR, Planning, Pièces, Sous-traitance, Courtoisie, Facturation, Qualité, Documentation, Reporting) :
- Comment y accéder (menu exact)
- Explication de chaque champ du formulaire (nom, à quoi il sert, obligatoire ou non)
- Les statuts/workflow avec explication de chaque transition
- Les boutons d'action et ce qu'ils font
- Les cas particuliers et pièges à éviter
- Captures d'écran : NON (pas possible), mais décrire la navigation précise

#### 4. Scénarios pas à pas
Écrire des tutoriels détaillés pour :
- Scénario A : "Un particulier vient pour une réparation mécanique simple"
- Scénario B : "Un client arrive après un accident avec sinistre assurance"
- Scénario C : "Gestion d'un sinistre grêle sur 10 véhicules"
- Scénario D : "Facturation split assurance + franchise"
- Scénario E : "Véhicule de courtoisie : attribution et restitution"
- Scénario F : "Supplément en cours de réparation"
- Scénario G : "Client mauvais payeur — blocage et déblocage"
- Scénario H : "Gestion d'une flotte entreprise"

#### 5. Configuration et paramétrage
- Taux horaires par défaut (où les modifier)
- Création des compagnies d'assurance et barèmes
- Configuration des postes de travail
- Systèmes de peinture
- Modèles d'email (comment les personnaliser)
- Tâches automatiques (cron) : lesquelles, quand, comment les activer/désactiver

#### 6. FAQ et dépannage
- "Le module ne s'affiche pas" → vérifier installation et droits
- "Je ne vois pas le menu Assurances" → vérifier le groupe
- "Le devis ne se convertit pas en OR" → vérifier le statut
- "La facture assurance n'est pas générée" → vérifier le sinistre lié
- etc.

### Format
- Fichier Markdown dans docs/USER_GUIDE.md
- Titre principal, sections numérotées, sous-sections
- Tableaux pour les permissions et les champs
- Encadrés (blockquotes) pour les astuces et avertissements
- Le tout en FRANÇAIS

---

## MISSION 2 — Analyse de compatibilité Odoo 19

Odoo 19 est sorti (septembre 2025). Analyse le code actuel de garage_pro et produis un rapport de migration.

### Étapes
1. Lis le code actuel et identifie tout ce qui pourrait casser en Odoo 19
2. Cherche les changements breaking entre Odoo 17 et 19 (utilise ta connaissance + les release notes)
3. Produis le rapport dans docs/MIGRATION_ODOO19.md

### Points à vérifier
- Changements d'API Python (deprecated methods, new API)
- Changements de vues XML (attrs deprecated dès v17, autres changements v18/v19)
- Changements dans les modules natifs hérités (fleet, stock, account)
- Changements OWL (si on a du JS custom)
- Changements PostgreSQL requis
- Changements dans le mécanisme de sécurité (ir.rule, ir.model.access)
- Nouveaux modules natifs Odoo 19 qui pourraient remplacer du code custom
- Impact des AI agents Odoo 19 sur notre module

### Format du rapport
```markdown
# Migration Garage Pro — Odoo 17 → 19

## Résumé exécutif
- Niveau de risque global : [Faible/Moyen/Élevé]
- Effort estimé : [X jours-homme]
- Recommandation : [migrer maintenant / attendre 19.1 / ...]

## Changements breaking
| Fichier | Ligne | Problème | Correction |
|---------|-------|----------|------------|
| ... | ... | ... | ... |

## Changements recommandés (non-breaking)
...

## Nouvelles fonctionnalités Odoo 19 à exploiter
...

## Plan de migration étape par étape
1. ...
2. ...

## Tests à exécuter après migration
...
```

---

## Exécution
1. Commence par la MISSION 1 (documentation)
2. Puis MISSION 2 (migration)
3. Mets à jour PROGRESS.md
4. Git add + commit + push les docs/
```
