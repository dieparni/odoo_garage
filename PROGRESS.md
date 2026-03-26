# Garage Pro — Progression

## Dernier agent : 2 — 2026-03-26
## Statut global : Phase 1 en cours (Agents 1-2 terminés)

### ✅ Terminé
- Specs rédigées et déposées
- Structure CLAUDE.md et agents créée
- Agent 1 : Fondation & Véhicules (2026-03-26)
  - `__manifest__.py` — depends: base, contacts, fleet, mail, account
  - `security/garage_pro_groups.xml` — 5 groupes (réceptionniste, technicien, chef atelier, comptable, gérant)
  - `security/ir.model.access.csv` — droits par groupe
  - `data/garage_sequences.xml` — séquences VEH + SIN
  - `models/vehicle.py` — extension fleet.vehicle (carrosserie, peinture, mécanique, CT, garantie, propriété, sinistres)
  - `models/customer.py` — extension res.partner (type client, facturation, préférences, flotte, contentieux)
  - `models/paint_system.py` — garage.paint.system (mail.thread + mail.activity.mixin)
  - `views/vehicle_views.xml` — form (5 onglets + smart button sinistres), tree, search
  - `views/customer_views.xml` — form (3 onglets garage), tree, search, action filtrée
  - `tests/test_vehicle.py` — 10 tests, `tests/test_customer.py` — 8 tests
- Agent 2 : Assurances & Sinistres (2026-03-26)
  - `models/insurance_company.py` — garage.insurance.company (barèmes, contacts, conditions)
  - `models/insurance_expert.py` — garage.insurance.expert
  - `models/insurance_claim.py` — garage.insurance.claim (workflow complet 13 états)
  - `models/insurance_supplement.py` — garage.insurance.supplement (workflow 4 états)
  - `views/insurance_views.xml` — form compagnie (3 onglets), tree, search, action
  - `views/claim_views.xml` — form sinistre (6 onglets + statusbar + boutons workflow), tree, search, action
  - `views/menus.xml` — menus Assurances (Sinistres, Compagnies)
  - `tests/test_insurance.py` — 16 tests (workflow, compute, suppléments, experts)
  - Installation OK, 0 erreurs, 34 tests passent

### 🔧 En cours
- Rien

### 📋 À faire
- Agent 3 : Devis & Ordres de Réparation
- Agent 4 : Métiers (Carrosserie, Peinture, Mécanique)
- Agent 5 : Planning & Ressources
- Agent 6 : Pièces & Stock
- Agent 7 : Sous-traitance & Courtoisie
- Agent 8 : Facturation multi-payeur
- Agent 9 : Communication, Qualité, Documentation
- Agent 10 : Reporting & Dashboards
- Agent 11 : CarVertical (Phase 2)

### ⚠️ Problèmes connus
- `fleet.vehicle` utilise `vin_sn` (pas `vin`) — adapté dans le code
- Les fuel_type Odoo 17 : diesel, gasoline, full_hybrid, plug_in_hybrid_diesel, plug_in_hybrid_gasoline, cng, lpg, hydrogen, electric
- Le sinistre ne référence pas encore quotation_id/repair_order_id (dépend Agent 3)
- document_ids sur claim (One2many vers garage.documentation) différé à Agent 9

### 📝 Champs différés (dépendent de modèles futurs)
- `vehicle.paint_formula_ids` → garage.paint.formula (Agent 4)
- `vehicle.repair_order_ids`, `repair_order_count`, `total_spent` → garage.repair.order (Agent 3)
- `vehicle.carvertical_*` → 4 champs CarVertical (Agent 11)
- `customer.repair_order_ids`, `repair_order_count` → garage.repair.order (Agent 3)
- `customer.total_invoiced_garage`, `outstanding_garage_balance`, `last_visit_date` → Agents 3+8
- `claim.quotation_id` → garage.quotation (Agent 3)
- `claim.repair_order_id` → garage.repair.order (Agent 3)
- `claim.document_ids` → garage.documentation (Agent 9)
- `insurance_company.total_outstanding` → dépend factures (Agent 8)

### 📝 Notes pour le prochain agent
- Le module s'installe et se met à jour sans erreur
- 34 tests passent (0 fail, 0 error)
- Agent 3 doit lire `04_quotation_repair.md`
- Les modèles quotation et repair_order doivent référencer claim_id (Many2one vers garage.insurance.claim)
- Penser à ajouter quotation_id et repair_order_id sur insurance_claim.py après création des modèles
- Mettre à jour `ir.model.access.csv` et `__manifest__.py` avec les nouveaux fichiers
- Le claim.action_start_work() devra vérifier repair_order_id une fois le modèle créé
