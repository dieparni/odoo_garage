# Garage Pro — Progression

## Dernier agent : 1 — 2026-03-26
## Statut global : Phase 1 en cours (Agent 1 terminé)

### ✅ Terminé
- Specs rédigées et déposées
- Structure CLAUDE.md et agents créée
- Agent 1 : Fondation & Véhicules (2026-03-26)
  - `__manifest__.py` — depends: base, contacts, fleet, mail, account
  - `security/garage_pro_groups.xml` — 5 groupes (réceptionniste, technicien, chef atelier, comptable, gérant)
  - `security/ir.model.access.csv` — droits fleet.vehicle + garage.paint.system par groupe
  - `data/garage_sequences.xml` — séquence VEH/%(year)s/XXXXX
  - `models/vehicle.py` — extension fleet.vehicle (carrosserie, peinture, mécanique, CT, garantie, propriété)
  - `models/customer.py` — extension res.partner (type client, facturation, préférences, flotte, contentieux)
  - `models/paint_system.py` — garage.paint.system (mail.thread + mail.activity.mixin)
  - `views/vehicle_views.xml` — form (5 onglets), tree, search (filtres + groupby)
  - `views/customer_views.xml` — form (3 onglets garage), tree, search, action filtrée
  - `views/menus.xml` — menu racine Garage + Réception (Véhicules, Clients)
  - `tests/test_vehicle.py` — 10 tests (VIN, compute, contraintes, séquence)
  - `tests/test_customer.py` — 8 tests (types, blocage, véhicules, action)
  - Installation OK, 0 erreurs, 18 tests passent

### 🔧 En cours
- Rien

### 📋 À faire
- Agent 2 : Assurances & Sinistres
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
- Les fuel_type Odoo 17 sont : diesel, gasoline, full_hybrid, plug_in_hybrid_diesel, plug_in_hybrid_gasoline, cng, lpg, hydrogen, electric (pas `hybrid` ni `plug_in_hybrid` comme dans la spec)
- Warning mineur "Two fields (drive_type, transmission) same label" — résolu en renommant drive_type en "Type de transmission"

### 📝 Champs différés (dépendent de modèles futurs)
- `vehicle.paint_formula_ids` → One2many vers garage.paint.formula (Agent 4)
- `vehicle.repair_order_ids`, `repair_order_count`, `total_spent` → garage.repair.order (Agent 3)
- `vehicle.claim_ids`, `claim_count` → garage.insurance.claim (Agent 2)
- `vehicle.carvertical_*` → 4 champs CarVertical (Agent 11)
- `customer.repair_order_ids`, `repair_order_count` → garage.repair.order (Agent 3)
- `customer.total_invoiced_garage`, `outstanding_garage_balance`, `last_visit_date` → dépendent de account.move/garage.repair.order (Agents 3+8)

### 📝 Notes pour le prochain agent
- Le module s'installe et se met à jour sans erreur
- 18 tests passent (0 fail, 0 error)
- Agent 2 doit lire `03_insurance.md`
- Les modèles garage.insurance.company et garage.insurance.claim doivent utiliser `_name` (pas `_inherit`)
- Penser à ajouter les claim_ids/claim_count sur vehicle et customer après création des modèles assurance
- Mettre à jour `ir.model.access.csv` et `__manifest__.py` avec les nouveaux fichiers
- Ajouter les depends supplémentaires au manifest au fur et à mesure (stock, purchase, calendar, portal, web, hr)
