# Claude Code — Plan d'exécution et délégation par agents

## Philosophie

Le projet est trop large pour être traité en une seule session. Il doit être découpé en **agents spécialisés** qui travaillent de manière autonome sur des périmètres bien définis, puis intégrés progressivement.

---

## Prérequis environnement

```bash
# Odoo 17 (Community ou Enterprise) installé et fonctionnel
# Base de données de test créée
# Modules natifs installés : contacts, fleet, stock, purchase, account, calendar, mail, portal, web
# Python 3.10+, PostgreSQL 14+
```

### Structure du module à générer

```
garage_pro/
├── __init__.py
├── __manifest__.py
├── security/
│   ├── garage_pro_groups.xml
│   └── ir.model.access.csv
├── data/
│   ├── garage_sequences.xml
│   ├── garage_mail_templates.xml
│   └── garage_cron.xml
├── models/
│   ├── __init__.py
│   ├── vehicle.py
│   ├── customer.py
│   ├── insurance_company.py
│   ├── insurance_claim.py
│   ├── quotation.py
│   ├── quotation_line.py
│   ├── repair_order.py
│   ├── repair_order_line.py
│   ├── bodywork_operation.py
│   ├── paint_operation.py
│   ├── paint_formula.py
│   ├── mechanic_operation.py
│   ├── workshop_post.py
│   ├── technician.py
│   ├── planning_slot.py
│   ├── subcontractor.py
│   ├── subcontract_order.py
│   ├── courtesy_vehicle.py
│   ├── courtesy_loan.py
│   ├── documentation.py
│   ├── quality_checklist.py
│   ├── quality_check_item.py
│   └── carvertical_connector.py
├── views/
│   ├── vehicle_views.xml
│   ├── customer_views.xml
│   ├── insurance_views.xml
│   ├── claim_views.xml
│   ├── quotation_views.xml
│   ├── repair_order_views.xml
│   ├── bodywork_views.xml
│   ├── paint_views.xml
│   ├── mechanic_views.xml
│   ├── planning_views.xml
│   ├── parts_views.xml
│   ├── subcontract_views.xml
│   ├── courtesy_views.xml
│   ├── documentation_views.xml
│   ├── quality_views.xml
│   ├── billing_views.xml
│   ├── reporting_views.xml
│   └── menus.xml
├── wizard/
│   ├── __init__.py
│   ├── claim_supplement_wizard.py
│   ├── courtesy_return_wizard.py
│   ├── quotation_to_repair_wizard.py
│   └── carvertical_lookup_wizard.py
├── report/
│   ├── quotation_report.xml
│   ├── repair_order_report.xml
│   ├── invoice_garage_report.xml
│   └── quality_checklist_report.xml
├── static/
│   └── src/
│       ├── css/
│       ├── js/
│       └── xml/          # Vues Owl (kanban custom, planning)
└── controllers/
    ├── __init__.py
    ├── portal.py          # Extension portail client
    └── carvertical_api.py
```

---

## Découpage en agents

### Agent 1 — Fondation & Véhicules
**Périmètre** : `__manifest__.py`, sécurité, séquences, modèle `garage.vehicle`, extension `res.partner`
**Spec** : `modules/01_vehicle.md` + `modules/02_customer.md`
**Dépendances** : aucune (c'est la base)
**Critères de validation** :
- Le module s'installe sans erreur
- On peut créer un véhicule avec tous les champs
- On peut créer un contact avec les champs garage
- Les groupes de sécurité existent
- Les séquences fonctionnent

### Agent 2 — Assurances & Sinistres
**Périmètre** : `garage.insurance.company`, `garage.insurance.claim`, workflow sinistre
**Spec** : `modules/03_insurance.md`
**Dépendances** : Agent 1 (véhicule + client)
**Critères de validation** :
- Création d'une compagnie d'assurance avec barèmes
- Création d'un sinistre lié à un véhicule et un client
- Workflow statut sinistre fonctionnel
- Gestion VEI

### Agent 3 — Devis & Ordres de Réparation
**Périmètre** : `garage.quotation`, `garage.quotation.line`, `garage.repair.order`, `garage.repair.order.line`
**Spec** : `modules/04_quotation_repair.md`
**Dépendances** : Agent 1 + Agent 2
**Critères de validation** :
- Création devis multi-ligne (MO, pièces, sous-traitance)
- Workflow devis (brouillon → envoyé → accepté → OR)
- Gestion des suppléments/avenants
- Conversion devis → OR
- Lien avec sinistre si applicable

### Agent 4 — Métiers (Carrosserie, Peinture, Mécanique)
**Périmètre** : opérations spécialisées, formules peinture, diagnostics, schéma dommages
**Spec** : `modules/05_bodywork.md` + `modules/06_paint.md` + `modules/07_mechanic.md`
**Dépendances** : Agent 3 (OR)
**Critères de validation** :
- Opérations carrosserie liées à un OR
- Gestion formules teinte peinture
- Planning cabine
- Diagnostic OBD enregistrable
- Plan d'entretien mécanique

### Agent 5 — Planning & Ressources
**Périmètre** : postes atelier, techniciens, créneaux, dépendances entre opérations
**Spec** : `modules/08_planning.md`
**Dépendances** : Agent 3 + Agent 4
**Critères de validation** :
- Vue Gantt ou Kanban du planning
- Affectation technicien + poste
- Gestion des conflits de ressources
- Pointage temps technicien

### Agent 6 — Pièces & Stock
**Périmètre** : extension stock Odoo, catégorisation OEM/aftermarket/occasion, commandes auto
**Spec** : `modules/09_parts_stock.md`
**Dépendances** : Agent 3 (lien OR)
**Critères de validation** :
- Réservation pièces sur OR
- Déclenchement commande fournisseur si rupture
- Suivi réception et affectation
- Gestion pièce consignée

### Agent 7 — Sous-traitance & Courtoisie
**Périmètre** : sous-traitants, bons de sous-traitance, flotte courtoisie, convention de prêt
**Spec** : `modules/10_subcontract.md` + `modules/11_courtesy.md`
**Dépendances** : Agent 3 (OR)
**Critères de validation** :
- Bon de sous-traitance lié à un OR
- Suivi statut sous-traitance
- Attribution véhicule courtoisie
- État des lieux départ/retour

### Agent 8 — Facturation multi-payeur
**Périmètre** : extension `account.move`, logique franchise, facturation assurance, acomptes
**Spec** : `modules/12_billing.md`
**Dépendances** : Agent 3 + Agent 2
**Critères de validation** :
- Facture client + facture assurance depuis un même OR
- Gestion franchise
- Acomptes
- Avoir / note de crédit
- TVA intracommunautaire (Luxembourg)

### Agent 9 — Communication, Qualité, Documentation
**Périmètre** : notifications, portail, photos, checklists QC
**Spec** : `modules/13_communication.md` + `modules/14_quality.md` + `modules/15_documentation.md`
**Dépendances** : Agent 3 (OR)
**Critères de validation** :
- Templates email/SMS par statut OR
- Upload photos lié à l'OR
- Checklist QC configurable
- Portail client lecture seule

### Agent 10 — Reporting & Dashboards
**Périmètre** : KPIs, vues pivot, graphiques, tableau de bord gérant
**Spec** : `modules/16_reporting.md`
**Dépendances** : tous les agents précédents
**Critères de validation** :
- Dashboard CA par activité
- Taux productivité atelier
- Suivi créances assurance
- Export données

### Agent 11 — CarVertical (Phase 2)
**Périmètre** : API CarVertical, wizard lookup par VIN, préremplissage
**Spec** : `integrations/carvertical.md`
**Dépendances** : Agent 1
**Critères de validation** :
- Appel API par VIN
- Préremplissage champs véhicule
- Gestion erreurs / VIN non trouvé
- Cache des résultats

---

## Ordre d'exécution recommandé

```
Phase 1 (fondation) :  Agent 1 → Agent 2 → Agent 3
Phase 2 (métiers) :    Agent 4 → Agent 5 → Agent 6
Phase 3 (support) :    Agent 7 → Agent 8 → Agent 9
Phase 4 (pilotage) :   Agent 10
Phase 5 (extension) :  Agent 11
```

Chaque agent doit :
1. Lire son fichier spec dans `/modules/` ou `/integrations/`
2. Consulter `README.md` pour les conventions
3. Implémenter les modèles Python
4. Créer les vues XML
5. Mettre à jour `security/ir.model.access.csv`
6. Tester l'installation du module
7. Valider les critères listés dans cette fiche

---

## Commandes utiles pour l'agent

```bash
# Installer/mettre à jour le module
odoo -d garage_test -u garage_pro --stop-after-init

# Lancer Odoo en mode dev
odoo -d garage_test --dev=all

# Lancer les tests
odoo -d garage_test --test-enable --test-tags garage_pro --stop-after-init

# Vérifier la syntaxe XML
xmllint --noout garage_pro/views/*.xml

# Vérifier les imports Python
python -c "import ast; ast.parse(open('models/vehicle.py').read())"
```

---

## Règles de codage

1. **Python** : PEP 8, docstrings en français, type hints
2. **XML** : indentation 4 espaces, IDs uniques préfixés `garage_`
3. **Modèles** : toujours hériter de `mail.thread` et `mail.activity.mixin` pour le tracking
4. **Champs** : `string=` en français, `help=` en français, `tracking=True` sur les champs importants
5. **Compute** : toujours avec `@api.depends`, jamais de SQL direct dans un compute
6. **Onchange** : préférer `@api.onchange` pour l'UX, mais la logique métier dans `write()`/`create()`
7. **Workflows** : utiliser `Selection` field avec méthodes `action_xxx()` pour les transitions
8. **Sécurité** : `ir.model.access.csv` + `ir.rule` pour le multi-company si nécessaire
9. **Tests** : au minimum un test par workflow principal (`TransactionCase`)
10. **Performance** : `sudo()` uniquement quand nécessaire, `search()` avec `limit=` quand possible
