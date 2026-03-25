# Module 04 — Devis & Ordres de Réparation

## Principe

Le devis est l'objet commercial, l'OR est l'objet opérationnel. Un devis validé se convertit en OR. L'OR est le cœur du système : tout y converge (pièces, temps, sous-traitance, planning, facturation).

---

## Modèle : `garage.quotation`

```python
class GarageQuotation(models.Model):
    _name = 'garage.quotation'
    _description = 'Devis garage'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'

    name = fields.Char(string="Référence", default='Nouveau', readonly=True, copy=False)

    # === STATUT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('approved', 'Accepté'),
        ('refused', 'Refusé'),
        ('converted', 'Converti en OR'),
        ('cancelled', 'Annulé'),
    ], default='draft', tracking=True, string="Statut")

    # === LIENS PRINCIPAUX ===
    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule", required=True, tracking=True)
    customer_id = fields.Many2one(
        'res.partner', string="Client", required=True, tracking=True,
        domain="[('is_garage_customer', '=', True)]",
    )
    invoice_partner_id = fields.Many2one(
        'res.partner', string="Adresse de facturation",
        help="Si différent du client (ex: société de leasing, employeur)",
    )
    claim_id = fields.Many2one(
        'garage.insurance.claim', string="Sinistre",
        domain="[('vehicle_id', '=', vehicle_id), ('state', 'not in', ['cancelled', 'paid'])]",
    )
    repair_order_id = fields.Many2one(
        'garage.repair.order', string="Ordre de réparation",
        readonly=True, copy=False,
    )

    # === INFORMATIONS VÉHICULE AU MOMENT DU DEVIS ===
    odometer_at_entry = fields.Integer(
        string="Kilométrage à l'entrée",
        help="Km relevé au moment de la réception du véhicule",
    )
    vehicle_reception_date = fields.Datetime(
        string="Date de réception véhicule",
        default=fields.Datetime.now,
    )
    vehicle_plate = fields.Char(
        related='vehicle_id.license_plate',
        string="Immatriculation",
        store=True,
    )
    vehicle_vin = fields.Char(
        related='vehicle_id.vin_sn',
        string="VIN",
    )

    # === LIGNES ===
    line_ids = fields.One2many('garage.quotation.line', 'quotation_id', string="Lignes de devis")

    # === MONTANTS ===
    amount_labor = fields.Monetary(
        string="Total main d'œuvre",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    amount_parts = fields.Monetary(
        string="Total pièces",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    amount_subcontract = fields.Monetary(
        string="Total sous-traitance",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    amount_paint_material = fields.Monetary(
        string="Total matière peinture",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    amount_untaxed = fields.Monetary(
        string="Total HT",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    amount_tax = fields.Monetary(
        string="TVA",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    amount_total = fields.Monetary(
        string="Total TTC",
        compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )

    # === ASSURANCE (si sinistre) ===
    is_insurance_claim = fields.Boolean(
        compute='_compute_is_insurance',
        store=True,
    )
    insurance_amount = fields.Monetary(
        string="Part assurance",
        compute='_compute_insurance_split',
        currency_field='currency_id',
        store=True,
    )
    franchise_amount = fields.Monetary(
        string="Part franchise client",
        compute='_compute_insurance_split',
        currency_field='currency_id',
        store=True,
    )

    # === REMISE ===
    global_discount_rate = fields.Float(string="Remise globale (%)")
    global_discount_amount = fields.Monetary(
        string="Montant remise",
        compute='_compute_amounts',
        currency_field='currency_id',
        store=True,
    )

    # === DATES ===
    date_quotation = fields.Date(string="Date du devis", default=fields.Date.today)
    date_validity = fields.Date(
        string="Date de validité",
        default=lambda self: fields.Date.today() + timedelta(days=30),
    )
    date_sent = fields.Datetime(string="Date d'envoi")
    date_approved = fields.Datetime(string="Date d'acceptation")
    date_refused = fields.Datetime(string="Date de refus")

    # === ESTIMATION TRAVAUX ===
    estimated_days = fields.Float(
        string="Durée estimée (jours ouvrés)",
        help="Estimation du temps de réparation",
    )
    estimated_delivery_date = fields.Date(
        string="Date de restitution estimée",
    )

    # === SUPPLÉMENTS ===
    is_supplement = fields.Boolean(
        string="Est un supplément / avenant",
        default=False,
    )
    parent_quotation_id = fields.Many2one(
        'garage.quotation',
        string="Devis parent",
        help="Si supplément, réfère au devis original",
    )
    supplement_ids = fields.One2many(
        'garage.quotation',
        'parent_quotation_id',
        string="Suppléments / Avenants",
    )

    # === NOTES ===
    internal_notes = fields.Html(string="Notes internes")
    customer_notes = fields.Html(string="Notes client (imprimées sur le devis)")

    # === TECHNIQUE ===
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    user_id = fields.Many2one('res.users', string="Responsable", default=lambda self: self.env.user)
```

### Calcul des montants

```python
@api.depends('line_ids.amount_total', 'line_ids.line_type', 'global_discount_rate')
def _compute_amounts(self):
    for rec in self:
        lines = rec.line_ids
        rec.amount_labor = sum(l.amount_total for l in lines if l.line_type in ('labor_body', 'labor_paint', 'labor_mech'))
        rec.amount_parts = sum(l.amount_total for l in lines if l.line_type == 'parts')
        rec.amount_subcontract = sum(l.amount_total for l in lines if l.line_type == 'subcontract')
        rec.amount_paint_material = sum(l.amount_total for l in lines if l.line_type == 'paint_material')

        subtotal = sum(l.amount_total for l in lines)
        discount = subtotal * (rec.global_discount_rate / 100.0) if rec.global_discount_rate else 0
        rec.global_discount_amount = discount
        rec.amount_untaxed = subtotal - discount
        rec.amount_tax = rec.amount_untaxed * 0.21  # Belgique 21% — à rendre configurable
        rec.amount_total = rec.amount_untaxed + rec.amount_tax
```

### Actions workflow

```python
def action_send(self):
    """Brouillon → Envoyé. Envoie le devis par email au client (et à l'assurance si sinistre)."""
    self.ensure_one()
    template = self.env.ref('garage_pro.email_template_quotation_sent')
    self.write({'state': 'sent', 'date_sent': fields.Datetime.now()})
    template.send_mail(self.id, force_send=True)
    # Si sinistre, envoyer aussi à l'assurance
    if self.claim_id and self.claim_id.insurance_company_id.claims_email:
        template.send_mail(self.id, force_send=True,
            email_values={'email_to': self.claim_id.insurance_company_id.claims_email})

def action_approve(self):
    """Envoyé → Accepté"""
    self.write({'state': 'approved', 'date_approved': fields.Datetime.now()})

def action_refuse(self):
    """Envoyé → Refusé"""
    self.write({'state': 'refused', 'date_refused': fields.Datetime.now()})

def action_convert_to_repair_order(self):
    """Accepté → Converti en OR. Crée l'OR avec toutes les lignes."""
    self.ensure_one()
    if self.state != 'approved':
        raise UserError("Le devis doit être accepté avant conversion.")

    # Vérifier si le client est bloqué
    if self.customer_id.is_blocked_garage:
        raise UserError("Ce client est bloqué. Raison : %s" % self.customer_id.blocked_reason)

    ro = self.env['garage.repair.order'].create({
        'vehicle_id': self.vehicle_id.id,
        'customer_id': self.customer_id.id,
        'invoice_partner_id': self.invoice_partner_id.id or self.customer_id.id,
        'claim_id': self.claim_id.id if self.claim_id else False,
        'quotation_id': self.id,
        'odometer_at_entry': self.odometer_at_entry,
        'estimated_days': self.estimated_days,
        'estimated_delivery_date': self.estimated_delivery_date,
    })

    # Copier les lignes
    for line in self.line_ids:
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': line.name,
            'line_type': line.line_type,
            'product_id': line.product_id.id if line.product_id else False,
            'description': line.description,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id,
            'unit_price': line.unit_price,
            'discount': line.discount,
            'allocated_time': line.allocated_time,
        })

    self.write({'state': 'converted', 'repair_order_id': ro.id})

    # Si sinistre, lier l'OR au sinistre
    if self.claim_id:
        self.claim_id.write({'repair_order_id': ro.id})

    return {
        'type': 'ir.actions.act_window',
        'res_model': 'garage.repair.order',
        'res_id': ro.id,
        'view_mode': 'form',
    }

def action_create_supplement(self):
    """Créer un avenant/supplément lié à ce devis"""
    self.ensure_one()
    supplement = self.copy({
        'name': 'Nouveau',
        'state': 'draft',
        'is_supplement': True,
        'parent_quotation_id': self.id,
        'line_ids': False,  # Lignes vides
    })
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'garage.quotation',
        'res_id': supplement.id,
        'view_mode': 'form',
    }

def action_cancel(self):
    self.write({'state': 'cancelled'})
```

---

## Modèle : `garage.quotation.line`

```python
class GarageQuotationLine(models.Model):
    _name = 'garage.quotation.line'
    _description = 'Ligne de devis garage'
    _order = 'sequence, id'

    quotation_id = fields.Many2one('garage.quotation', ondelete='cascade', required=True)
    sequence = fields.Integer(default=10)

    name = fields.Char(string="Description", required=True)
    description = fields.Text(string="Description détaillée")

    line_type = fields.Selection([
        ('labor_body', 'Main d\'œuvre carrosserie'),
        ('labor_paint', 'Main d\'œuvre peinture'),
        ('labor_mech', 'Main d\'œuvre mécanique'),
        ('parts', 'Pièces détachées'),
        ('paint_material', 'Matière peinture'),
        ('subcontract', 'Sous-traitance'),
        ('consumable', 'Consommables'),
        ('misc', 'Divers'),
    ], string="Type de ligne", required=True)

    # === PRODUIT (optionnel, pour les pièces) ===
    product_id = fields.Many2one(
        'product.product',
        string="Produit/Pièce",
        domain="[('type', 'in', ['product', 'consu'])]",
    )
    product_category = fields.Selection([
        ('oem', 'Pièce OEM (constructeur)'),
        ('aftermarket', 'Pièce aftermarket'),
        ('used', 'Pièce d\'occasion'),
        ('exchange', 'Échange standard'),
    ], string="Catégorie pièce")

    # === QUANTITÉ & PRIX ===
    quantity = fields.Float(string="Quantité", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unité")
    unit_price = fields.Monetary(string="Prix unitaire", currency_field='currency_id')
    discount = fields.Float(string="Remise (%)")
    amount_total = fields.Monetary(
        string="Total ligne",
        compute='_compute_total',
        store=True,
        currency_field='currency_id',
    )

    # === MAIN D'ŒUVRE ===
    allocated_time = fields.Float(
        string="Temps alloué (heures)",
        help="Temps barème alloué pour cette opération (pour lignes MO)",
    )
    hourly_rate = fields.Monetary(
        string="Taux horaire",
        currency_field='currency_id',
    )

    # === RÉFÉRENCE BARÈME ===
    bareme_code = fields.Char(
        string="Code opération barème",
        help="Référence Audatex/DAT/GT Motive",
    )
    bareme_source = fields.Selection([
        ('audatex', 'Audatex'),
        ('dat', 'DAT'),
        ('gt_motive', 'GT Motive'),
        ('manual', 'Manuel'),
    ], string="Source barème", default='manual')

    # === ZONE CARROSSERIE (si applicable) ===
    damage_zone = fields.Selection([
        ('front_bumper', 'Pare-chocs avant'),
        ('rear_bumper', 'Pare-chocs arrière'),
        ('hood', 'Capot'),
        ('trunk', 'Coffre'),
        ('roof', 'Toit'),
        ('fender_fl', 'Aile avant gauche'),
        ('fender_fr', 'Aile avant droite'),
        ('fender_rl', 'Aile arrière gauche'),
        ('fender_rr', 'Aile arrière droite'),
        ('door_fl', 'Porte avant gauche'),
        ('door_fr', 'Porte avant droite'),
        ('door_rl', 'Porte arrière gauche'),
        ('door_rr', 'Porte arrière droite'),
        ('sill_l', 'Bas de caisse gauche'),
        ('sill_r', 'Bas de caisse droit'),
        ('windshield', 'Pare-brise'),
        ('rear_window', 'Lunette arrière'),
        ('side_window_l', 'Vitre latérale gauche'),
        ('side_window_r', 'Vitre latérale droite'),
        ('mirror_l', 'Rétroviseur gauche'),
        ('mirror_r', 'Rétroviseur droit'),
        ('other', 'Autre'),
    ], string="Zone endommagée")

    damage_level = fields.Selection([
        ('light', 'Léger (retouche/débosselage)'),
        ('medium', 'Moyen (redressage)'),
        ('heavy', 'Grave (remplacement partiel)'),
        ('replace', 'Remplacement complet'),
    ], string="Niveau de dommage")

    currency_id = fields.Many2one(related='quotation_id.currency_id')

    @api.depends('quantity', 'unit_price', 'discount', 'allocated_time', 'hourly_rate', 'line_type')
    def _compute_total(self):
        for line in self:
            if line.line_type in ('labor_body', 'labor_paint', 'labor_mech') and line.allocated_time and line.hourly_rate:
                subtotal = line.allocated_time * line.hourly_rate
            else:
                subtotal = line.quantity * line.unit_price
            line.amount_total = subtotal * (1 - (line.discount / 100.0))

    @api.onchange('line_type')
    def _onchange_line_type(self):
        """Pré-remplir le taux horaire selon le type de MO et la config assurance si applicable"""
        if self.line_type in ('labor_body', 'labor_paint', 'labor_mech'):
            claim = self.quotation_id.claim_id
            if claim and claim.insurance_company_id:
                ins = claim.insurance_company_id
                rates = {
                    'labor_body': ins.hourly_rate_bodywork,
                    'labor_paint': ins.hourly_rate_paint,
                    'labor_mech': ins.hourly_rate_mechanic,
                }
                self.hourly_rate = rates.get(self.line_type, 0)
            else:
                # Taux horaire par défaut (config système)
                params = self.env['ir.config_parameter'].sudo()
                defaults = {
                    'labor_body': float(params.get_param('garage_pro.default_hourly_rate_body', 55)),
                    'labor_paint': float(params.get_param('garage_pro.default_hourly_rate_paint', 55)),
                    'labor_mech': float(params.get_param('garage_pro.default_hourly_rate_mech', 60)),
                }
                self.hourly_rate = defaults.get(self.line_type, 55)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.unit_price = self.product_id.lst_price
            self.uom_id = self.product_id.uom_id
```

---

## Modèle : `garage.repair.order`

```python
class GarageRepairOrder(models.Model):
    _name = 'garage.repair.order'
    _description = 'Ordre de réparation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'

    name = fields.Char(string="Référence OR", default='Nouveau', readonly=True, copy=False)

    # === STATUT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('parts_waiting', 'Attente pièces'),
        ('in_progress', 'En cours'),
        ('paint_booth', 'En cabine'),
        ('reassembly', 'Remontage'),
        ('qc_pending', 'Contrôle qualité'),
        ('qc_done', 'QC validé'),
        ('ready', 'Prêt à livrer'),
        ('delivered', 'Livré'),
        ('invoiced', 'Facturé'),
        ('cancelled', 'Annulé'),
    ], default='draft', tracking=True, string="Statut",
        group_expand='_group_expand_states',
    )

    # === LIENS ===
    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule", required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string="Client", required=True, tracking=True)
    invoice_partner_id = fields.Many2one('res.partner', string="Facturer à")
    claim_id = fields.Many2one('garage.insurance.claim', string="Sinistre")
    quotation_id = fields.Many2one('garage.quotation', string="Devis d'origine")
    quotation_ids = fields.One2many('garage.quotation', 'repair_order_id', string="Devis liés")

    # === LIGNES ===
    line_ids = fields.One2many('garage.repair.order.line', 'repair_order_id', string="Lignes")

    # === PLANNING ===
    planned_start_date = fields.Datetime(string="Début planifié")
    planned_end_date = fields.Datetime(string="Fin planifiée")
    actual_start_date = fields.Datetime(string="Début réel")
    actual_end_date = fields.Datetime(string="Fin réelle")
    estimated_days = fields.Float(string="Durée estimée (jours)")
    estimated_delivery_date = fields.Date(string="Date restitution estimée")
    planning_slot_ids = fields.One2many('garage.planning.slot', 'repair_order_id', string="Créneaux planning")

    # === TECHNICIENS AFFECTÉS ===
    technician_ids = fields.Many2many(
        'hr.employee',
        string="Techniciens affectés",
        domain="[('department_id.name', 'ilike', 'atelier')]",
    )
    workshop_chief_id = fields.Many2one('hr.employee', string="Chef d'atelier")

    # === VÉHICULE ===
    odometer_at_entry = fields.Integer(string="Km à l'entrée")
    odometer_at_exit = fields.Integer(string="Km à la sortie")
    vehicle_location = fields.Selection([
        ('outside', 'Parking extérieur'),
        ('workshop', 'Dans l\'atelier'),
        ('paint_booth', 'En cabine peinture'),
        ('subcontractor', 'Chez un sous-traitant'),
        ('delivered', 'Restitué'),
    ], string="Localisation véhicule", default='outside', tracking=True)

    # === COURTOISIE ===
    courtesy_loan_id = fields.Many2one('garage.courtesy.loan', string="Prêt véhicule courtoisie")
    has_courtesy_vehicle = fields.Boolean(
        compute='_compute_has_courtesy',
        string="Véhicule de courtoisie",
    )

    # === TEMPS ===
    total_allocated_hours = fields.Float(
        string="Heures allouées (total)",
        compute='_compute_hours',
        store=True,
    )
    total_worked_hours = fields.Float(
        string="Heures travaillées (total)",
        compute='_compute_hours',
        store=True,
    )
    productivity_rate = fields.Float(
        string="Taux de productivité (%)",
        compute='_compute_hours',
        store=True,
    )

    # === SOUS-TRAITANCE ===
    subcontract_order_ids = fields.One2many(
        'garage.subcontract.order', 'repair_order_id', string="Bons sous-traitance",
    )

    # === QUALITÉ ===
    quality_check_id = fields.Many2one('garage.quality.checklist', string="Checklist QC")
    qc_validated = fields.Boolean(string="QC validé", tracking=True)
    qc_validated_by = fields.Many2one('res.users', string="Validé par")
    qc_validated_date = fields.Datetime(string="Date validation QC")

    # === DOCUMENTATION ===
    documentation_ids = fields.One2many('garage.documentation', 'repair_order_id', string="Documents/Photos")
    photo_count = fields.Integer(compute='_compute_photo_count')

    # === FACTURATION ===
    invoice_ids = fields.Many2many('account.move', string="Factures")
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    invoice_status = fields.Selection([
        ('no', 'Rien à facturer'),
        ('to_invoice', 'À facturer'),
        ('partial', 'Partiellement facturé'),
        ('invoiced', 'Facturé'),
    ], compute='_compute_invoice_status', store=True)

    # === MONTANTS ===
    amount_untaxed = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_tax = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_total = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    margin = fields.Monetary(string="Marge", compute='_compute_margin', currency_field='currency_id')
    margin_rate = fields.Float(string="Taux marge (%)", compute='_compute_margin')

    # === NOTES ===
    internal_notes = fields.Html(string="Notes internes")
    delivery_notes = fields.Html(string="Notes de restitution")

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    user_id = fields.Many2one('res.users', string="Responsable", default=lambda self: self.env.user)

    # === PRIORITÉ ===
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgent'),
        ('2', 'Très urgent'),
    ], default='0', string="Priorité")
```

### Actions workflow OR

```python
def action_confirm(self):
    """Brouillon → Confirmé. Vérifie la disponibilité des pièces."""
    self.write({'state': 'confirmed'})
    # Vérifier pièces en stock
    missing = self.line_ids.filtered(
        lambda l: l.line_type == 'parts' and l.product_id and l.product_id.qty_available < l.quantity
    )
    if missing:
        self.write({'state': 'parts_waiting'})
        # Créer commandes fournisseur automatiques (ou notifier)
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary="Pièces manquantes pour OR %s" % self.name,
            note="Pièces à commander : %s" % ', '.join(missing.mapped('name')),
        )

def action_start(self):
    """Confirmé/Attente pièces → En cours"""
    self.write({
        'state': 'in_progress',
        'actual_start_date': fields.Datetime.now(),
    })
    # Notifier le client
    self._send_status_notification('in_progress')

def action_enter_paint_booth(self):
    self.write({'state': 'paint_booth', 'vehicle_location': 'paint_booth'})

def action_reassembly(self):
    self.write({'state': 'reassembly', 'vehicle_location': 'workshop'})

def action_request_qc(self):
    """Demander le contrôle qualité — crée une checklist si nécessaire"""
    self.write({'state': 'qc_pending'})
    if not self.quality_check_id:
        # Créer checklist auto selon le type d'opérations
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(self)
        self.quality_check_id = checklist.id

def action_validate_qc(self):
    """Chef d'atelier valide le QC"""
    if self.quality_check_id and not self.quality_check_id.is_fully_checked:
        raise UserError("Tous les points de la checklist doivent être vérifiés.")
    self.write({
        'state': 'qc_done',
        'qc_validated': True,
        'qc_validated_by': self.env.user.id,
        'qc_validated_date': fields.Datetime.now(),
    })

def action_ready(self):
    """QC validé → Prêt à livrer. Notifier le client."""
    self.write({'state': 'ready'})
    self._send_status_notification('ready')

def action_deliver(self):
    """Prêt → Livré. Restitution du véhicule."""
    self.write({
        'state': 'delivered',
        'actual_end_date': fields.Datetime.now(),
        'vehicle_location': 'delivered',
    })
    # Mettre à jour le km si saisi
    if self.odometer_at_exit and self.vehicle_id:
        self.env['fleet.vehicle.odometer'].create({
            'vehicle_id': self.vehicle_id.id,
            'value': self.odometer_at_exit,
            'date': fields.Date.today(),
        })
    # Restituer le véhicule de courtoisie si applicable
    if self.courtesy_loan_id and self.courtesy_loan_id.state == 'active':
        self.courtesy_loan_id.action_return()
    self._send_status_notification('delivered')

def action_create_invoice(self):
    """Crée les factures (client et/ou assurance)"""
    self.ensure_one()
    invoices = self.env['account.move']

    if self.claim_id and self.claim_id.insurance_company_id:
        # Facturation split : assurance + franchise client
        inv_insurance = self._create_insurance_invoice()
        inv_franchise = self._create_franchise_invoice()
        invoices = inv_insurance | inv_franchise
    else:
        # Facturation client simple
        inv_client = self._create_client_invoice()
        invoices = inv_client

    self.write({
        'state': 'invoiced',
        'invoice_ids': [(4, inv.id) for inv in invoices],
    })
    return self._action_view_invoices()

def _create_client_invoice(self):
    """Crée une facture client standard depuis l'OR"""
    invoice_vals = {
        'move_type': 'out_invoice',
        'partner_id': self.invoice_partner_id.id or self.customer_id.id,
        'invoice_date': fields.Date.today(),
        'invoice_origin': self.name,
        'garage_repair_order_id': self.id,
        'invoice_line_ids': [(0, 0, line._prepare_invoice_line()) for line in self.line_ids],
    }
    return self.env['account.move'].create(invoice_vals)

def _create_insurance_invoice(self):
    """Crée la facture assurance (total - franchise)"""
    insurance_partner = self.claim_id.insurance_company_id.partner_id
    total = self.amount_total
    franchise = self.claim_id.franchise_computed
    insurance_amount = total - franchise

    invoice_vals = {
        'move_type': 'out_invoice',
        'partner_id': insurance_partner.id,
        'invoice_date': fields.Date.today(),
        'invoice_origin': "%s (Sinistre %s)" % (self.name, self.claim_id.name),
        'garage_repair_order_id': self.id,
        'garage_claim_id': self.claim_id.id,
        'invoice_line_ids': [(0, 0, {
            'name': "Réparation %s - Sinistre %s" % (self.vehicle_id.license_plate, self.claim_id.insurance_claim_number),
            'quantity': 1,
            'price_unit': insurance_amount,
        })],
    }
    return self.env['account.move'].create(invoice_vals)

def _create_franchise_invoice(self):
    """Crée la facture franchise client"""
    franchise = self.claim_id.franchise_computed
    if franchise <= 0:
        return self.env['account.move']

    invoice_vals = {
        'move_type': 'out_invoice',
        'partner_id': self.customer_id.id,
        'invoice_date': fields.Date.today(),
        'invoice_origin': "%s (Franchise)" % self.name,
        'garage_repair_order_id': self.id,
        'invoice_line_ids': [(0, 0, {
            'name': "Franchise sinistre %s" % self.claim_id.insurance_claim_number,
            'quantity': 1,
            'price_unit': franchise,
        })],
    }
    return self.env['account.move'].create(invoice_vals)

def _send_status_notification(self, status):
    """Envoie une notification au client selon son canal préféré"""
    template_map = {
        'in_progress': 'garage_pro.email_template_or_in_progress',
        'ready': 'garage_pro.email_template_or_ready',
        'delivered': 'garage_pro.email_template_or_delivered',
    }
    template_ref = template_map.get(status)
    if template_ref:
        template = self.env.ref(template_ref, raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
```

---

## Modèle : `garage.repair.order.line`

Identique à `garage.quotation.line` avec en plus :

```python
# === EXÉCUTION ===
actual_time = fields.Float(
    string="Temps réel passé (heures)",
    help="Temps réellement passé par le technicien",
)
technician_id = fields.Many2one('hr.employee', string="Technicien")
is_done = fields.Boolean(string="Terminé", default=False)
done_date = fields.Datetime(string="Date fin")

# === PIÈCES ===
stock_move_ids = fields.One2many('stock.move', 'garage_ro_line_id', string="Mouvements stock")
parts_received = fields.Boolean(
    string="Pièces reçues",
    compute='_compute_parts_received',
    store=True,
)

def _prepare_invoice_line(self):
    """Prépare les valeurs pour une ligne de facture account.move.line"""
    return {
        'name': self.name,
        'quantity': self.quantity if self.line_type != 'labor_body' else 1,
        'price_unit': self.amount_total if self.line_type in ('labor_body', 'labor_paint', 'labor_mech') else self.unit_price,
        'product_id': self.product_id.id if self.product_id else False,
        'product_uom_id': self.uom_id.id if self.uom_id else False,
        'discount': self.discount,
    }
```

---

## Séquences

```xml
<record id="garage_seq_quotation" model="ir.sequence">
    <field name="name">Devis garage</field>
    <field name="code">garage.quotation</field>
    <field name="prefix">DEV/%(year)s/</field>
    <field name="padding">4</field>
</record>

<record id="garage_seq_repair_order" model="ir.sequence">
    <field name="name">Ordre de réparation</field>
    <field name="code">garage.repair.order</field>
    <field name="prefix">OR/%(year)s/</field>
    <field name="padding">4</field>
</record>
```

---

## Extension `account.move` (pour le lien retour)

```python
class AccountMove(models.Model):
    _inherit = 'account.move'

    garage_repair_order_id = fields.Many2one('garage.repair.order', string="OR garage")
    garage_claim_id = fields.Many2one('garage.insurance.claim', string="Sinistre")
    is_garage_invoice = fields.Boolean(
        string="Facture garage",
        compute='_compute_is_garage',
        store=True,
    )
```

## Extension `stock.move` (pour le lien pièces)

```python
class StockMove(models.Model):
    _inherit = 'stock.move'

    garage_ro_line_id = fields.Many2one('garage.repair.order.line', string="Ligne OR garage")
```
