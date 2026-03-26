# Garage Pro — Progression

## Dernier agent : 3 — 2026-03-26
## Statut global : Phase 1 terminée (Agents 1-3)

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

### 🔧 En cours
- Rien

### 📋 À faire
- Agent 4 : Métiers (Carrosserie, Peinture, Mécanique) — spec `05_06_07_trades.md`
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

### 📝 Champs différés (dépendent de modèles futurs)
- `vehicle.paint_formula_ids` → garage.paint.formula (Agent 4)
- `vehicle.carvertical_*` → 4 champs CarVertical (Agent 11)
- `repair_order.technician_ids`, `workshop_chief_id` → hr.employee (Agent 5, nécessite `hr` dans depends)
- `repair_order.planning_slot_ids` → garage.planning.slot (Agent 5)
- `repair_order.subcontract_order_ids` → garage.subcontract.order (Agent 7)
- `repair_order.courtesy_loan_id`, `has_courtesy_vehicle` → garage.courtesy.loan (Agent 7)
- `repair_order.quality_check_id`, `qc_validated*` → garage.quality.checklist (Agent 9)
- `repair_order.documentation_ids`, `photo_count` → garage.documentation (Agent 9)
- `repair_order.invoice_ids`, `invoice_count`, `invoice_status`, `margin*` → account.move (Agent 8)
- `ro_line.stock_move_ids`, `parts_received` → stock.move (Agent 6)
- `claim.document_ids` → garage.documentation (Agent 9)
- `customer.total_invoiced_garage`, `outstanding_garage_balance`, `last_visit_date` → Agents 3+8

### 📝 Notes pour le prochain agent
- Le module s'installe et se met à jour sans erreur
- 52 tests passent (0 fail, 0 error)
- Phase 1 complète : véhicules + clients + assurances + devis + OR
- Agent 4 doit lire `05_06_07_trades.md` pour les opérations métier
- Penser à ajouter `hr` aux depends quand les techniciens seront implémentés
- Les actions QC (action_request_qc, action_validate_qc) sont simplifiées — à enrichir avec Agent 9
- La facturation (action_create_invoice) est différée à Agent 8
