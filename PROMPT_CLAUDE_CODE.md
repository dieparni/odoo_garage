# Prompt initial pour Claude Code Cloud

## Comment utiliser

### Option A — Claude Code Cloud (interface web)
Copier-coller le prompt ci-dessous dans Claude Code Cloud.
En cas de timeout ou interruption, coller le **prompt de reprise** à la place.

### Option B — CLI avec auto-restart
```bash
chmod +x launch_garage_build.sh
./launch_garage_build.sh --loop
```

---

## 🚀 PROMPT INITIAL (première exécution)

```
Tu es l'architecte principal du projet Garage Pro, un module Odoo 17 complet pour la gestion d'atelier carrosserie/peinture/mécanique.

## Contexte
Les spécifications techniques complètes sont dans `garage-odoo-specs/`. Le plan d'exécution par agents est dans `garage-odoo-specs/CLAUDE_CODE_PLAN.md`. Le fichier `CLAUDE.md` contient toutes les conventions du projet.

## Ta mission
Construire le module `garage_pro` complet en suivant ce cycle pour chaque agent (1 à 11) :

1. **LIRE** la spec du module dans `garage-odoo-specs/modules/`
2. **IMPLÉMENTER** : modèles Python → vues XML → sécurité → données
3. **TESTER** : écrire des tests dans `garage_pro/tests/`, les exécuter
4. **CHALLENGER** : utilise un subagent `reviewer` pour relire le code et le comparer aux specs. Cherche les failles, les champs manquants, les cas non gérés. Ne te fais pas de cadeau.
5. **VALIDER** : vérifier que le module s'installe (`odoo -d garage_test -u garage_pro --stop-after-init`)
6. **DOCUMENTER** : mettre à jour `PROGRESS.md` après chaque agent

## Règles critiques
- Lis TOUJOURS la spec AVANT de coder. Chaque ligne compte.
- Lis TOUJOURS PROGRESS.md au démarrage pour savoir où tu en es
- Utilise `_inherit` pour étendre les modules Odoo natifs (fleet.vehicle, res.partner, account.move, stock.move), ne recrée RIEN qui existe
- Si un test échoue → corrige le CODE, pas le test (sauf si le test est objectivement faux)
- Mets à jour PROGRESS.md après CHAQUE agent terminé avec un résumé clair
- Si tu approches de la limite de contexte, ARRÊTE-TOI PROPREMENT : écris des notes ultra-détaillées dans PROGRESS.md (fichiers créés, ce qui reste, problèmes rencontrés) pour que la session suivante puisse reprendre sans rien perdre

## Gestion des erreurs
- Si l'installation Odoo échoue → lis le traceback ENTIER, corrige, réessaie (max 3 fois)
- Si tu ne trouves pas un module Odoo natif → vérifie qu'il est dans les `depends` du manifest
- Si un champ `fleet.vehicle` n'existe pas → c'est peut-être `vin_sn` au lieu de `vin`, vérifie avec `grep -r "vin" /path/to/odoo/addons/fleet/`
- Si tu bloques sur un problème > 10 minutes → note-le dans PROGRESS.md section "Problèmes connus" et passe au suivant

## Ordre strict
Agent 1 (véhicules+clients) → Agent 2 (assurances) → Agent 3 (devis/OR) → Agent 4 (métiers) → Agent 5 (planning) → Agent 6 (stock) → Agent 7 (sous-trait+courtoisie) → Agent 8 (facturation) → Agent 9 (comm+QC+docs) → Agent 10 (reporting) → Agent 11 (CarVertical)

## Commence maintenant
1. Lis PROGRESS.md
2. Lis CLAUDE.md
3. Lis garage-odoo-specs/CLAUDE_CODE_PLAN.md
4. Lance l'Agent 1 (ou le prochain selon PROGRESS.md)

Sois méthodique, rigoureux, et ne laisse rien de cassé derrière toi.
```

---

## 🔄 PROMPT DE REPRISE (après timeout / interruption / nouvelle session)

```
Reprends le travail sur le projet Garage Pro (module Odoo 17).

## PREMIÈRE CHOSE À FAIRE
Lis PROGRESS.md. C'est ton journal de bord. Il dit EXACTEMENT où tu en es, ce qui est fait, ce qui reste, et les problèmes connus.

## Étapes de reprise
1. Lis PROGRESS.md entièrement
2. Lis la section "Notes pour le prochain agent"
3. Lis la section "Problèmes connus" 
4. Identifie le prochain agent selon la section "À faire"
5. Si un module était 🔧 "en cours", TERMINE-LE en priorité
6. Lis sa spec dans garage-odoo-specs/modules/
7. Continue l'implémentation

## Règles de reprise
- Ne recommence JAMAIS un module marqué ✅
- Ne recrée JAMAIS un fichier qui existe déjà — lis-le d'abord et modifie-le
- Vérifie que le module s'installe avant d'avancer
- Utilise un subagent reviewer pour challenger ton code
- Mets à jour PROGRESS.md à la fin

## Objectif
Continue la construction jusqu'à complétion de tous les agents. Si tu approches de la limite de contexte, écris des notes TRÈS détaillées dans PROGRESS.md pour la prochaine reprise.
```

---

## 🎯 PROMPT AGENT SPÉCIFIQUE (pour forcer un agent précis)

Remplacer `[N]` par le numéro d'agent (1-11) :

```
Exécute l'Agent [N] du projet Garage Pro (module Odoo 17).

1. Lis PROGRESS.md pour le contexte global
2. Lis la spec correspondante dans garage-odoo-specs/modules/
3. Vérifie ce qui existe déjà dans garage_pro/ pour ne rien écraser
4. Implémente TOUT ce que la spec demande pour cet agent
5. Écris les tests unitaires
6. Vérifie l'installation du module
7. Utilise un subagent reviewer pour challenger le code
8. Mets à jour PROGRESS.md

Agents :
1 = Fondation (manifest, sécurité, véhicule, client)
2 = Assurances & Sinistres
3 = Devis & Ordres de Réparation
4 = Métiers (Carrosserie, Peinture, Mécanique)
5 = Planning & Ressources
6 = Pièces & Stock
7 = Sous-traitance & Courtoisie
8 = Facturation multi-payeur
9 = Communication, Qualité, Documentation
10 = Reporting & Dashboards
11 = CarVertical
```

---

## 🏥 PROMPT DE DIAGNOSTIC (si ça ne s'installe plus)

```
Le module garage_pro ne s'installe plus. Diagnostique et corrige.

1. Lance : odoo -d garage_test -u garage_pro --stop-after-init 2>&1 | tail -100
2. Lis le traceback ENTIER
3. Identifie la cause racine (XML invalide, import manquant, champ inexistant, etc.)
4. Corrige le problème
5. Vérifie la cohérence :
   - models/__init__.py importe tous les fichiers
   - __manifest__.py liste tous les data/views
   - ir.model.access.csv a tous les modèles
   - Pas de référence à un modèle non encore créé
6. Relance l'installation
7. Mets à jour PROGRESS.md section "Problèmes connus"
```
