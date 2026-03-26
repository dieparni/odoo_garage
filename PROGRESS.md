# Garage Pro — Progression

## Dernier agent : 4 — 2026-03-26
## Statut global : Phase 2 en cours (Agent 4 terminé)

### ✅ Terminé
- Specs rédigées et déposées
- Structure CLAUDE.md et agents créée
- Agent 1 : Fondation & Véhicules (2026-03-26)
  - Extension fleet.vehicle (carrosserie, peinture, mécanique, CT, garantie, propriété)
  - Extension res.partner (type client, facturation, préférences, flotte, contentieux)
  - garage.paint.system, séquences, groupes sécurité, vues, 18 tests
- Agent 2 : Assurances & Sinistres (2026-03-26)
  - garage.insurance.company (barèmes, contacts, conditions)
  - garage.insurance.expert, garage.insurance.claim (workflow 13 états)
  - garage.insurance.supplement (workflow 4 états)
  - Vues compagnie + sinistre, menus Assurances, 16 tests
- Agent 3 : Devis & Ordres de Réparation (2026-03-26)
  - `models/quotation.py` — garage.quotation (workflow 6 états, conversion en OR)
  - `models/quotation_line.py` — garage.quotation.line (MO, pièces, sous-traitance, barème)
  - `models/repair_order.py` — garage.repair.order (workflow 12 états)
  - `models/repair_order_line.py` — garage.repair.order.line (exécution, temps réel)
  - Lien claim ↔ quotation ↔ repair_order bidirectionnel
  - Smart buttons OR + Sinistres sur véhicule et client
  - `views/quotation_views.xml` — form + tree + search + action
  - `views/repair_order_views.xml` — form + tree + search + action
  - Menus: Réception > Devis, Atelier > OR
  - `tests/test_quotation.py` — 18 tests (workflow, compute, conversion, supplément)
  - Installation OK, 0 erreurs, 52 tests passent
- Agent 4 : Métiers — Carrosserie, Peinture, Mécanique (2026-03-26)
  - `models/constants.py` — DAMAGE_ZONES, DAMAGE_LEVELS partagés
  - `models/bodywork_operation.py` — garage.bodywork.operation (workflow 4 états, auto-création peinture)
  - `models/paint_operation.py` — garage.paint.operation (workflow 7 états : waiting→prep→booth→drying→polish→done, rework)
  - `models/paint_formula.py` — garage.paint.formula (code constructeur, spectro, variantes)
  - `models/paint_consumption.py` — garage.paint.consumption (produits, coûts compute)
  - `models/mechanic_operation.py` — garage.mechanic.operation (workflow 4 états, OBD, pneus, entretien)
  - `models/maintenance_plan.py` — garage.maintenance.plan + item (intervalles km/mois, compute next/overdue)
  - One2many + counts sur repair_order (bodywork/paint/mechanic_operation_ids)
  - `views/trade_views.xml` — form+tree+search pour chaque métier + onglets inline dans OR form
  - Menus Atelier : Carrosserie, Peinture, Mécanique, Plans d'entretien
  - Menu Config : Formules peinture
  - Sécurité : 20 règles ACL (technician/chief/manager) pour 7 nouveaux modèles
  - `hr` ajouté aux depends (technician_id sur les 3 opérations)
  - `tests/test_trades.py` — 23 tests (workflows, auto-paint, consumption, maintenance)
  - Installation OK, 0 erreurs, 75 tests passent

### 🔧 En cours
- Rien

### 📋 À faire
- Agent 5 : Planning & Ressources — spec `08_09_10_11_planning_stock_sub_courtesy.md`
- Agent 6 : Pièces & Stock — idem
- Agent 7 : Sous-traitance & Courtoisie — idem
- Agent 8 : Facturation multi-payeur — spec `12_to_16_billing_comms_quality_reporting.md`
- Agent 9 : Communication, Qualité, Documentation — idem
- Agent 10 : Reporting & Dashboards — idem
- Agent 11 : CarVertical (Phase 2) — spec `carvertical.md`

### ⚠️ Problèmes connus
- `fleet.vehicle` utilise `vin_sn` (pas `vin`)
- TVA fixée à 21% en dur — à rendre configurable via ir.config_parameter
- portal.mixin non inclus sur quotation/OR (nécessite module portal, à ajouter avec Agent 9)
- Création `product.product` en tests échoue si `purchase` installé (contrainte NOT NULL sur `purchase_line_warn`) — contourné en utilisant un produit existant

### 📝 Champs différés (dépendent de modèles futurs)
- `vehicle.paint_formula_ids` → garage.paint.formula — ✅ modèle créé, One2many à ajouter sur vehicle
- `vehicle.carvertical_*` → 4 champs CarVertical (Agent 11)
- `repair_order.technician_ids`, `workshop_chief_id` → hr.employee (Agent 5)
- `repair_order.planning_slot_ids` → garage.planning.slot (Agent 5)
- `repair_order.subcontract_order_ids` → garage.subcontract.order (Agent 7)
- `repair_order.courtesy_loan_id`, `has_courtesy_vehicle` → garage.courtesy.loan (Agent 7)
- `repair_order.quality_check_id`, `qc_validated*` → garage.quality.checklist (Agent 9)
- `repair_order.documentation_ids`, `photo_count` → garage.documentation (Agent 9)
- `repair_order.invoice_ids`, `invoice_count`, `invoice_status`, `margin*` → account.move (Agent 8)
- `ro_line.stock_move_ids`, `parts_received` → stock.move (Agent 6)
- `claim.document_ids` → garage.documentation (Agent 9)
- `customer.total_invoiced_garage`, `outstanding_garage_balance`, `last_visit_date` → Agents 3+8
- `paint_consumption` → stock.move pour décrémentation stock (Agent 6)

### 📝 Notes pour le prochain agent
- Le module s'installe et se met à jour sans erreur
- 75 tests passent (0 fail, 0 error)
- Phase 1 complète + Agent 4 (métiers) terminé
- `hr` est maintenant dans les depends (pour technician_id sur les opérations)
- Agent 5 doit lire la spec `08_09_10_11_planning_stock_sub_courtesy.md` pour le planning
- Les actions QC (action_request_qc, action_validate_qc) sont simplifiées — à enrichir avec Agent 9
- La facturation (action_create_invoice) est différée à Agent 8
- Les consommations peinture ne décrémentent pas encore le stock (Agent 6)
