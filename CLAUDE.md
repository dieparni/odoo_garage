# CLAUDE.md — Garage Pro (Odoo 17)

## Identité projet

Module Odoo 17 custom pour gestion complète d'un atelier carrosserie/peinture/mécanique.
Nom technique : `garage_pro`. Auteur : Volpe Services.

## Règle absolue

> **Lis les specs AVANT de coder.** Chaque module a sa fiche technique dans `garage-odoo-specs/modules/`. Ne code JAMAIS un modèle sans avoir lu sa spec en entier. Le plan d'exécution est dans `garage-odoo-specs/CLAUDE_CODE_PLAN.md`.

## Architecture

```
garage_pro/                  ← Module Odoo unique
├── __init__.py
├── __manifest__.py
├── security/
├── data/
├── models/
├── views/
├── wizard/
├── report/
├── static/src/{css,js,xml}
├── controllers/
├── tests/
└── demo/
```

## Stack & conventions

- **Python** : 3.10+, PEP 8, type hints, docstrings FR
- **Odoo** : v17, hériter (`_inherit`) plutôt que recréer
- **XML** : indentation 4 espaces, IDs préfixés `garage_`
- **Modèles** : toujours `mail.thread` + `mail.activity.mixin`
- **Champs** : `string=` FR, `tracking=True` sur les champs importants
- **Tests** : `TransactionCase` minimum par modèle, dans `tests/`
- **Pas de SQL brut** dans les compute, sauf pour les vues reporting (`_auto = False`)

## Commandes utiles

```bash
# Installer/MAJ le module (DB de test)
odoo -d garage_test -u garage_pro --stop-after-init

# Lancer en mode dev
odoo -d garage_test --dev=all

# Lancer les tests
odoo -d garage_test --test-enable --test-tags garage_pro --stop-after-init

# Vérifier XML
xmllint --noout garage_pro/views/*.xml

# Vérifier Python
python -c "import ast; ast.parse(open('garage_pro/models/vehicle.py').read())"

# Lint
flake8 garage_pro/ --max-line-length=120 --ignore=E501,W503
```

## Workflow de développement

Chaque agent/session suit ce cycle :

1. **LIRE** — Ouvrir la spec du module concerné dans `garage-odoo-specs/modules/`
2. **VÉRIFIER L'ÉTAT** — Lire `PROGRESS.md` pour savoir ce qui est déjà fait
3. **PLANIFIER** — Écrire le plan dans le scratchpad (`/tmp/scratchpad.md`)
4. **IMPLÉMENTER** — Coder modèle → vues → sécurité → tests
5. **TESTER** — Lancer les tests Odoo, vérifier la syntaxe
6. **CHALLENGER** — Relire le code en mode review, chercher les bugs
7. **DOCUMENTER** — Mettre à jour `PROGRESS.md` avec ce qui a été fait et ce qui reste

## PROGRESS.md — État du projet (CRITIQUE)

Le fichier `PROGRESS.md` à la racine du repo est le **journal de bord**. Il DOIT être mis à jour à chaque fin de session. Format :

```markdown
# Garage Pro — Progression

## Dernier agent : [numéro] — [date ISO]
## Statut global : [Phase X en cours]

### ✅ Terminé
- Agent 1 : Fondation & Véhicules (date)
  - Models: vehicle.py, customer.py
  - Views: vehicle_views.xml, customer_views.xml
  - Security: groups, access CSV
  - Tests: test_vehicle.py ✅

### 🔧 En cours
- Agent 3 : Devis & OR
  - quotation.py ✅
  - quotation_line.py ✅
  - repair_order.py 🔧 (workflow actions manquantes)

### 📋 À faire
- Agent 4, 5, 6, 7, 8, 9, 10, 11

### ⚠️ Problèmes connus
- fleet.vehicle n'a pas de champ `vin` dans Odoo 17 CE, utiliser `vin_sn`
- ...

### 📝 Notes pour le prochain agent
- Le module s'installe OK avec agents 1-2
- Penser à vérifier la fiscal position Luxembourg
```

## Stratégie de reprise (anti-timeout)

Si tu reprends après une interruption :
1. Lis `PROGRESS.md` en premier
2. Lis la section "Notes pour le prochain agent"
3. Continue exactement là où ça s'est arrêté
4. Ne recommence JAMAIS un module déjà marqué ✅

## Modules Odoo natifs — NE PAS RECRÉER

| Besoin | Utiliser | Comment |
|--------|----------|---------|
| Contacts | `res.partner` | `_inherit` + champs garage |
| Véhicules | `fleet.vehicle` | `_inherit` + champs garage |
| Stock | `stock.*` | Tel quel + catégories |
| Achats | `purchase.order` | Tel quel, lier aux OR |
| Factures | `account.move` | `_inherit` pour multi-payeur |
| Planning | `calendar.event` | Base du planning |
| Emails | `mail.template` | Templates custom |
| Portail | `portal` | Étendre |

## Ordre d'implémentation (par agent)

```
Phase 1 : Agent 1 (véhicules+clients) → Agent 2 (assurances) → Agent 3 (devis/OR)
Phase 2 : Agent 4 (métiers) → Agent 5 (planning) → Agent 6 (stock)
Phase 3 : Agent 7 (sous-trait+courtoisie) → Agent 8 (facturation) → Agent 9 (comm+QC+docs)
Phase 4 : Agent 10 (reporting)
Phase 5 : Agent 11 (CarVertical)
```

## Checklist validation par agent

Avant de marquer un agent ✅ dans PROGRESS.md :
- [ ] Le module s'installe sans erreur (`--stop-after-init`)
- [ ] Les modèles sont créés en DB (vérifier via `\dt garage_*` en psql)
- [ ] Les vues form/tree/search s'affichent sans erreur XML
- [ ] Les workflows (transitions de statut) fonctionnent
- [ ] Les tests passent
- [ ] La sécurité (ir.model.access.csv) est à jour
- [ ] Le manifest liste tous les fichiers data/views

## Pièges connus Odoo 17

- `attrs` est deprecated en Odoo 17, utiliser `invisible="field_name == 'value'"` directement
- `fleet.vehicle` a `vin_sn` pas `vin` — vérifier la version
- Pour le multi-company : toujours `company_id` avec `default=lambda self: self.env.company`
- `api.multi` n'existe plus, le défaut est multi
- Les vues XML doivent avoir des `id` uniques dans tout le module
- `web.assets_backend` (pas `web.assets_common`) pour le JS/CSS
