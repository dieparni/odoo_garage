# Module 01 — Véhicules (`garage.vehicle`)

## Principe

Extension du modèle `fleet.vehicle` d'Odoo avec les champs spécifiques au métier garage (carrosserie, peinture, mécanique). Le véhicule est l'objet central du système : chaque devis, OR, sinistre, photo, facture y est rattaché.

---

## Modèle : `garage.vehicle`

**Héritage** : `_inherit = 'fleet.vehicle'` (extension du modèle existant)

### Champs hérités de fleet.vehicle (déjà existants, ne pas recréer)
- `name` — Nom affiché (marque + modèle)
- `license_plate` — Immatriculation
- `model_id` — Modèle véhicule (M2O → `fleet.vehicle.model`)
- `model_year` — Année modèle
- `odometer` — Compteur kilométrique
- `fuel_type` — Type carburant
- `driver_id` — Conducteur (M2O → `res.partner`)
- `manager_id` — Gestionnaire (M2O → `res.partner`)
- `company_id` — Société
- `state_id` — Statut
- `tag_ids` — Tags

### Champs ajoutés (spécifiques garage)

```python
# === IDENTIFICATION ===
vin = fields.Char(
    string="Numéro VIN",
    size=17,
    help="Vehicle Identification Number — 17 caractères alphanumériques",
    tracking=True,
    copy=False,
)
# Note : fleet.vehicle a déjà un champ 'vin_sn'. Vérifier s'il est utilisable.
# Si oui, NE PAS créer un nouveau champ, utiliser vin_sn.

first_registration_date = fields.Date(
    string="Date 1ère immatriculation",
    tracking=True,
)
registration_country_id = fields.Many2one(
    'res.country',
    string="Pays d'immatriculation",
)

# === CARROSSERIE / PEINTURE ===
paint_code = fields.Char(
    string="Code peinture constructeur",
    help="Code couleur fabricant (ex: LY9T, 475, etc.)",
    tracking=True,
)
paint_color_name = fields.Char(
    string="Nom de la teinte",
    help="Nom commercial de la couleur (ex: Noir Mythic, Blanc Glacier)",
)
paint_system_id = fields.Many2one(
    'garage.paint.system',
    string="Système peinture",
    help="Fabricant peinture utilisé (Standox, Sikkens, PPG...)",
)
paint_formula_ids = fields.One2many(
    'garage.paint.formula',
    'vehicle_id',
    string="Formules teinte enregistrées",
)
body_type = fields.Selection([
    ('sedan', 'Berline'),
    ('break', 'Break'),
    ('suv', 'SUV / Crossover'),
    ('coupe', 'Coupé'),
    ('cabriolet', 'Cabriolet'),
    ('monospace', 'Monospace'),
    ('utilitaire', 'Utilitaire'),
    ('pickup', 'Pick-up'),
    ('citadine', 'Citadine'),
    ('other', 'Autre'),
], string="Type de carrosserie")

# === MÉCANIQUE ===
engine_code = fields.Char(string="Code moteur")
engine_displacement = fields.Integer(string="Cylindrée (cm³)")
power_kw = fields.Integer(string="Puissance (kW)")
power_cv = fields.Integer(
    string="Puissance (CV)",
    compute='_compute_power_cv',
    store=True,
)
transmission_type = fields.Selection([
    ('manual', 'Manuelle'),
    ('automatic', 'Automatique'),
    ('semi_auto', 'Semi-automatique'),
    ('cvt', 'CVT'),
], string="Boîte de vitesses")
drive_type = fields.Selection([
    ('fwd', 'Traction (FWD)'),
    ('rwd', 'Propulsion (RWD)'),
    ('awd', 'Intégrale (AWD)'),
    ('4wd', '4x4 (4WD)'),
], string="Transmission")

# === ÉLECTRIQUE / HYBRIDE ===
is_electric = fields.Boolean(
    string="Véhicule électrique/hybride",
    compute='_compute_is_electric',
    store=True,
)
battery_capacity_kwh = fields.Float(string="Capacité batterie (kWh)")
charge_connector_type = fields.Selection([
    ('type1', 'Type 1 (J1772)'),
    ('type2', 'Type 2 (Mennekes)'),
    ('ccs', 'CCS Combo'),
    ('chademo', 'CHAdeMO'),
    ('tesla', 'Tesla'),
], string="Type de connecteur")

# === CONTRÔLE TECHNIQUE ===
ct_last_date = fields.Date(string="Dernier contrôle technique")
ct_next_date = fields.Date(
    string="Prochain contrôle technique",
    compute='_compute_ct_next',
    store=True,
)
ct_result = fields.Selection([
    ('pass', 'Favorable'),
    ('pass_remarks', 'Favorable avec remarques'),
    ('fail', 'Défavorable'),
    ('dangerous', 'Dangereux'),
], string="Résultat dernier CT")

# === GARANTIE ===
warranty_end_date = fields.Date(string="Fin de garantie constructeur")
is_under_warranty = fields.Boolean(
    string="Sous garantie",
    compute='_compute_warranty',
    store=True,
)

# === PROPRIÉTÉ ===
ownership_type = fields.Selection([
    ('private', 'Propriété privée'),
    ('leasing', 'Leasing'),
    ('lld', 'Location longue durée'),
    ('fleet', 'Flotte entreprise'),
    ('rental', 'Location courte durée'),
], string="Type de propriété", default='private')
leasing_company_id = fields.Many2one(
    'res.partner',
    string="Société de leasing",
    domain="[('is_leasing_company', '=', True)]",
)
owner_id = fields.Many2one(
    'res.partner',
    string="Propriétaire réel",
    help="Différent du conducteur si leasing ou flotte",
    tracking=True,
)

# === HISTORIQUE ===
repair_order_ids = fields.One2many(
    'garage.repair.order',
    'vehicle_id',
    string="Ordres de réparation",
)
repair_order_count = fields.Integer(
    compute='_compute_repair_order_count',
    string="Nombre d'OR",
)
claim_ids = fields.One2many(
    'garage.insurance.claim',
    'vehicle_id',
    string="Sinistres",
)
claim_count = fields.Integer(
    compute='_compute_claim_count',
    string="Nombre de sinistres",
)
total_spent = fields.Monetary(
    string="Total dépensé",
    compute='_compute_total_spent',
    currency_field='currency_id',
)

# === CARVERTICAL (Phase 2) ===
carvertical_last_check = fields.Datetime(string="Dernière vérification CarVertical")
carvertical_report_url = fields.Char(string="URL rapport CarVertical")
carvertical_mileage_ok = fields.Boolean(string="Kilométrage vérifié OK")
carvertical_damage_history = fields.Text(string="Historique dommages CarVertical")

# === NOTES ===
internal_notes = fields.Html(string="Notes internes")
```

### Méthodes

```python
@api.depends('power_kw')
def _compute_power_cv(self):
    for rec in self:
        rec.power_cv = round(rec.power_kw * 1.36) if rec.power_kw else 0

@api.depends('fuel_type')
def _compute_is_electric(self):
    for rec in self:
        rec.is_electric = rec.fuel_type in ('electric', 'hybrid', 'plug_in_hybrid')

@api.depends('ct_last_date')
def _compute_ct_next(self):
    """En Belgique : CT tous les ans après 4 ans. Au Luxembourg : 2 ans puis tous les ans."""
    for rec in self:
        if rec.ct_last_date:
            rec.ct_next_date = rec.ct_last_date + relativedelta(years=1)
        else:
            rec.ct_next_date = False

@api.depends('warranty_end_date')
def _compute_warranty(self):
    today = fields.Date.today()
    for rec in self:
        rec.is_under_warranty = bool(rec.warranty_end_date and rec.warranty_end_date >= today)

@api.constrains('vin')
def _check_vin(self):
    """Validation format VIN : 17 caractères alphanumériques, pas de I, O, Q"""
    for rec in self:
        if rec.vin:
            if len(rec.vin) != 17:
                raise ValidationError("Le VIN doit contenir exactement 17 caractères.")
            if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', rec.vin.upper()):
                raise ValidationError("Le VIN contient des caractères invalides (I, O, Q interdits).")

def action_lookup_carvertical(self):
    """Ouvre le wizard CarVertical pour préremplir les champs"""
    return {
        'type': 'ir.actions.act_window',
        'name': 'Recherche CarVertical',
        'res_model': 'garage.carvertical.lookup.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {'default_vehicle_id': self.id, 'default_vin': self.vin},
    }
```

### Vues

**Form** : onglets "Identification", "Carrosserie/Peinture", "Mécanique", "Historique", "Documents", "Notes"
- Bouton smart "X Ordres de réparation" → action ouvrant la liste filtrée
- Bouton smart "X Sinistres" → idem
- Bouton "Recherche CarVertical" (conditionnel : si VIN renseigné)
- Statusbar si on gère un statut véhicule (en atelier / restitué / abandonné)

**Tree** : immatriculation, marque/modèle, VIN, client, statut, dernier passage

**Search** : filtres par marque, type carrosserie, propriété, sous garantie, électrique

**Kanban** : carte avec immatriculation, photo véhicule, nom client, dernier OR

---

## Modèle auxiliaire : `garage.paint.system`

```python
class GaragePaintSystem(models.Model):
    _name = 'garage.paint.system'
    _description = 'Système de peinture (fabricant)'

    name = fields.Char(string="Nom", required=True)  # Standox, Sikkens, PPG, Spies Hecker...
    code = fields.Char(string="Code")
    supplier_id = fields.Many2one('res.partner', string="Fournisseur")
    active = fields.Boolean(default=True)
```

---

## Données de démonstration

Créer au minimum :
- 5 véhicules (berline, SUV, utilitaire, électrique, leasing)
- 3 systèmes peinture (Standox, Sikkens, PPG)
- Séquences initialisées

---

## Points d'attention

1. **`fleet.vehicle` a déjà `vin_sn`** : vérifier dans la version Odoo cible. Si le champ existe et correspond, l'utiliser au lieu de créer `vin`. Sinon, le créer.
2. **Unicité VIN** : ajouter `_sql_constraints = [('vin_unique', 'UNIQUE(vin)', 'Ce VIN existe déjà.')]`
3. **Photos** : utiliser le champ `image_128` / `image_1920` hérité de fleet.vehicle pour la photo principale. Les photos de dommages sont dans le module documentation.
4. **Odoo fleet gère déjà les odomètres** : via `fleet.vehicle.odometer`. Réutiliser ce mécanisme.
5. **Multi-société** : si le garage a plusieurs sites, respecter `company_id` hérité.
