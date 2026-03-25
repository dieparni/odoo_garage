# Module 08 — Planning atelier

## Modèle : `garage.workshop.post`

Chaque poste physique de l'atelier est une ressource planifiable.

```python
class GarageWorkshopPost(models.Model):
    _name = 'garage.workshop.post'
    _description = 'Poste de travail atelier'

    name = fields.Char(string="Nom du poste", required=True)  # Ex: "Pont 1", "Cabine peinture", "Marbre"
    code = fields.Char(string="Code court")
    post_type = fields.Selection([
        ('body_lift', 'Pont carrosserie'),
        ('mech_lift', 'Pont mécanique'),
        ('frame_bench', 'Marbre de redressage'),
        ('paint_booth', 'Cabine de peinture'),
        ('paint_prep', 'Zone préparation peinture'),
        ('welding', 'Poste de soudure'),
        ('diag', 'Poste diagnostic'),
        ('wash', 'Zone lavage'),
        ('general', 'Zone polyvalente'),
    ], string="Type de poste", required=True)
    capacity = fields.Integer(
        string="Capacité simultanée",
        default=1,
        help="Nombre de véhicules simultanés (1 pour un pont, 2+ pour une zone ouverte)",
    )
    is_bottleneck = fields.Boolean(
        string="Goulot d'étranglement",
        help="Si coché, ce poste est priorisé dans la planification (ex: cabine peinture)",
    )
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Couleur (Kanban)")
    notes = fields.Text(string="Notes (équipement, limitations)")
```

## Modèle : `garage.technician.skill`

Extension `hr.employee` pour les compétences atelier.

```python
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_garage_technician = fields.Boolean(string="Technicien atelier")
    garage_skills = fields.Selection([
        ('body', 'Carrossier'),
        ('painter', 'Peintre'),
        ('mechanic', 'Mécanicien'),
        ('electrician', 'Électricien auto'),
        ('multi', 'Polyvalent'),
    ], string="Spécialité garage")
    has_ev_certification = fields.Boolean(
        string="Habilitation véhicules électriques",
        help="Habilité à travailler sur les véhicules haute tension",
    )
    ev_certification_date = fields.Date(string="Date habilitation VE")
    hourly_cost = fields.Monetary(
        string="Coût horaire interne",
        currency_field='currency_id',
        help="Coût interne (pour calcul de marge, pas le taux facturé)",
    )
    daily_capacity_hours = fields.Float(
        string="Capacité journalière (h)",
        default=8.0,
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

## Modèle : `garage.planning.slot`

Créneau de planning liant un OR, un poste, un technicien, et un horaire.

```python
class GaragePlanningSlot(models.Model):
    _name = 'garage.planning.slot'
    _description = 'Créneau planning atelier'
    _inherit = ['mail.thread']
    _order = 'start_datetime'

    repair_order_id = fields.Many2one('garage.repair.order', string="Ordre de réparation", required=True)
    post_id = fields.Many2one('garage.workshop.post', string="Poste de travail", required=True)
    technician_id = fields.Many2one('hr.employee', string="Technicien",
        domain="[('is_garage_technician', '=', True)]")
    operation_type = fields.Selection([
        ('body', 'Carrosserie'),
        ('paint_prep', 'Préparation peinture'),
        ('paint_booth', 'Cabine peinture'),
        ('mechanic', 'Mécanique'),
        ('reassembly', 'Remontage'),
        ('qc', 'Contrôle qualité'),
        ('wash', 'Nettoyage'),
    ], string="Type d'opération")

    start_datetime = fields.Datetime(string="Début", required=True)
    end_datetime = fields.Datetime(string="Fin", required=True)
    duration_hours = fields.Float(
        string="Durée (h)",
        compute='_compute_duration',
        store=True,
    )

    state = fields.Selection([
        ('planned', 'Planifié'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
        ('cancelled', 'Annulé'),
    ], default='planned', tracking=True)

    # Pour le Gantt
    vehicle_plate = fields.Char(related='repair_order_id.vehicle_id.license_plate', store=True)
    customer_name = fields.Char(related='repair_order_id.customer_id.name', store=True)
    color = fields.Integer(related='post_id.color')

    notes = fields.Text(string="Notes")

    @api.constrains('post_id', 'start_datetime', 'end_datetime')
    def _check_no_overlap(self):
        """Vérifie qu'il n'y a pas de chevauchement sur le même poste"""
        for rec in self:
            if rec.post_id.capacity == 1:
                overlapping = self.search([
                    ('post_id', '=', rec.post_id.id),
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancelled'),
                    ('start_datetime', '<', rec.end_datetime),
                    ('end_datetime', '>', rec.start_datetime),
                ])
                if overlapping:
                    raise ValidationError(
                        "Le poste %s est déjà occupé sur ce créneau par l'OR %s."
                        % (rec.post_id.name, overlapping[0].repair_order_id.name)
                    )
```

### Vues planning
- **Vue Gantt** : `garage.planning.slot` groupé par `post_id`, avec `start_datetime` / `end_datetime`
- **Vue Kanban** : groupé par `state` pour le suivi quotidien du chef d'atelier
- **Vue Calendrier** : pour les peintres (planning cabine)
- Dashboard : taux d'occupation par poste (heures planifiées / heures disponibles)

---

# Module 09 — Pièces & Stock

Extension du stock Odoo natif. Pas de nouveau modèle de stock — on étend `product.template` et `product.product`.

## Extension `product.template`

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_garage_part = fields.Boolean(string="Pièce garage")
    garage_part_category = fields.Selection([
        ('oem', 'OEM (constructeur)'),
        ('aftermarket', 'Aftermarket (équipementier)'),
        ('used', 'Occasion'),
        ('exchange', 'Échange standard'),
        ('consumable', 'Consommable atelier'),
        ('paint', 'Produit peinture'),
    ], string="Catégorie garage")
    oem_reference = fields.Char(string="Référence OEM constructeur")
    tecdoc_reference = fields.Char(string="Référence TecDoc")
    compatible_vehicle_models = fields.Char(
        string="Véhicules compatibles",
        help="Marques/modèles compatibles (texte libre ou via TecDoc)",
    )
    is_consignment = fields.Boolean(
        string="Pièce consignée",
        help="Échange standard avec consigne (turbo, injecteur, démarreur...)",
    )
    consignment_amount = fields.Monetary(
        string="Montant consigne",
        currency_field='currency_id',
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

### Workflow pièces dans l'OR

1. La ligne OR de type `parts` référence un `product.product`
2. Quand l'OR passe en `confirmed`, on vérifie `product.qty_available`
3. Si stock insuffisant → création automatique d'un `purchase.order` (ou draft à valider)
4. Le `stock.move` créé par la réception est lié à la ligne OR via `garage_ro_line_id`
5. Quand la pièce est posée → le `stock.move` est validé (consommation)

### Catégories de produits à créer (data)

```xml
<record id="garage_product_categ_parts" model="product.category">
    <field name="name">Pièces garage</field>
</record>
<record id="garage_product_categ_oem" model="product.category">
    <field name="name">Pièces OEM</field>
    <field name="parent_id" ref="garage_product_categ_parts"/>
</record>
<record id="garage_product_categ_aftermarket" model="product.category">
    <field name="name">Pièces aftermarket</field>
    <field name="parent_id" ref="garage_product_categ_parts"/>
</record>
<record id="garage_product_categ_paint" model="product.category">
    <field name="name">Produits peinture</field>
</record>
<record id="garage_product_categ_consumable" model="product.category">
    <field name="name">Consommables atelier</field>
</record>
```

---

# Module 10 — Sous-traitance

## Modèle : `garage.subcontract.order`

```python
class GarageSubcontractOrder(models.Model):
    _name = 'garage.subcontract.order'
    _description = 'Bon de sous-traitance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string="Référence", default='Nouveau', readonly=True, copy=False)
    repair_order_id = fields.Many2one('garage.repair.order', string="OR", required=True)
    subcontractor_id = fields.Many2one(
        'res.partner', string="Sous-traitant", required=True,
        domain="[('is_subcontractor', '=', True)]",
    )

    service_type = fields.Selection([
        ('pdr', 'Débosselage sans peinture (PDR)'),
        ('glass', 'Vitrage'),
        ('upholstery', 'Sellerie / Garnissage'),
        ('electronics', 'Électronique embarquée'),
        ('adas_calibration', 'Calibration ADAS (caméras)'),
        ('aircon', 'Climatisation spécialisée'),
        ('geometry', 'Géométrie spécialisée'),
        ('towing', 'Remorquage / dépannage'),
        ('painting', 'Peinture externe'),
        ('other', 'Autre'),
    ], string="Type de service", required=True)

    description = fields.Html(string="Description des travaux")
    estimated_cost = fields.Monetary(string="Coût estimé", currency_field='currency_id')
    actual_cost = fields.Monetary(string="Coût réel", currency_field='currency_id')

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
        ('invoiced', 'Facturé'),
        ('cancelled', 'Annulé'),
    ], default='draft', tracking=True)

    send_date = fields.Date(string="Date d'envoi")
    expected_return_date = fields.Date(string="Retour prévu")
    actual_return_date = fields.Date(string="Retour réel")
    is_late = fields.Boolean(compute='_compute_is_late')

    # Véhicule ou pièce envoyée ?
    send_type = fields.Selection([
        ('vehicle', 'Véhicule envoyé chez le sous-traitant'),
        ('part', 'Pièce envoyée'),
        ('on_site', 'Intervention sur place'),
    ], string="Mode", default='on_site')

    quality_ok = fields.Boolean(string="Qualité validée")
    quality_notes = fields.Text(string="Notes qualité")
    purchase_order_id = fields.Many2one('purchase.order', string="Bon de commande achat")

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

---

# Module 11 — Véhicules de courtoisie

## Modèle : `garage.courtesy.vehicle`

```python
class GarageCourtesyVehicle(models.Model):
    _name = 'garage.courtesy.vehicle'
    _description = 'Véhicule de courtoisie'
    _inherit = ['mail.thread']

    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule", required=True)
    name = fields.Char(related='vehicle_id.license_plate', store=True)

    state = fields.Selection([
        ('available', 'Disponible'),
        ('loaned', 'En prêt'),
        ('maintenance', 'En maintenance'),
        ('unavailable', 'Indisponible'),
    ], default='available', tracking=True)

    insurance_expiry = fields.Date(string="Échéance assurance")
    ct_expiry = fields.Date(string="Échéance CT")
    current_loan_id = fields.Many2one('garage.courtesy.loan', string="Prêt en cours")
    loan_ids = fields.One2many('garage.courtesy.loan', 'courtesy_vehicle_id', string="Historique prêts")
    daily_cost = fields.Monetary(
        string="Coût journalier interne",
        currency_field='currency_id',
        help="Pour le calcul de rentabilité de l'OR",
    )
    daily_charge_rate = fields.Monetary(
        string="Tarif facturable / jour",
        currency_field='currency_id',
        help="Montant facturé au client si dépassement de durée",
    )
    max_free_days = fields.Integer(
        string="Jours gratuits max",
        default=0,
        help="Nombre de jours de prêt gratuit avant facturation",
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

## Modèle : `garage.courtesy.loan`

```python
class GarageCourtesyLoan(models.Model):
    _name = 'garage.courtesy.loan'
    _description = 'Prêt de véhicule de courtoisie'
    _inherit = ['mail.thread']

    courtesy_vehicle_id = fields.Many2one('garage.courtesy.vehicle', required=True)
    repair_order_id = fields.Many2one('garage.repair.order', string="OR lié")
    customer_id = fields.Many2one('res.partner', string="Client emprunteur", required=True)

    state = fields.Selection([
        ('reserved', 'Réservé'),
        ('active', 'En cours'),
        ('returned', 'Restitué'),
        ('damaged', 'Restitué avec dommage'),
    ], default='reserved', tracking=True)

    # Départ
    loan_start = fields.Datetime(string="Date de prêt")
    km_start = fields.Integer(string="Km départ")
    fuel_level_start = fields.Selection([
        ('full', 'Plein'),
        ('3_4', '3/4'),
        ('1_2', '1/2'),
        ('1_4', '1/4'),
        ('empty', 'Vide'),
    ], string="Niveau carburant départ")
    condition_start = fields.Html(string="État des lieux départ")
    condition_start_photos = fields.Many2many(
        'ir.attachment', 'courtesy_start_photo_rel',
        string="Photos départ",
    )
    agreement_signed = fields.Boolean(string="Convention signée")
    agreement_file = fields.Binary(string="Convention signée (fichier)")

    # Retour
    loan_end = fields.Datetime(string="Date de retour")
    km_end = fields.Integer(string="Km retour")
    fuel_level_end = fields.Selection([
        ('full', 'Plein'),
        ('3_4', '3/4'),
        ('1_2', '1/2'),
        ('1_4', '1/4'),
        ('empty', 'Vide'),
    ], string="Niveau carburant retour")
    condition_end = fields.Html(string="État des lieux retour")
    condition_end_photos = fields.Many2many(
        'ir.attachment', 'courtesy_end_photo_rel',
        string="Photos retour",
    )
    has_damage = fields.Boolean(string="Dommage constaté au retour")
    damage_description = fields.Text(string="Description dommage")

    # Durée et facturation
    loan_days = fields.Integer(compute='_compute_days', store=True)
    billable_days = fields.Integer(compute='_compute_billable_days')
    billable_amount = fields.Monetary(compute='_compute_billable_amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def action_activate(self):
        self.write({'state': 'active', 'loan_start': fields.Datetime.now()})
        self.courtesy_vehicle_id.write({'state': 'loaned', 'current_loan_id': self.id})

    def action_return(self):
        state = 'damaged' if self.has_damage else 'returned'
        self.write({'state': state, 'loan_end': fields.Datetime.now()})
        self.courtesy_vehicle_id.write({'state': 'available', 'current_loan_id': False})
```
