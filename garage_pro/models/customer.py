"""Extension de res.partner avec les champs spécifiques garage."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Extension res.partner pour la gestion des clients garage."""

    _inherit = 'res.partner'

    # === IDENTIFICATION GARAGE ===
    is_garage_customer = fields.Boolean(
        string="Client garage",
        default=False,
        help="Cocher pour activer les fonctionnalités garage sur ce contact",
    )
    garage_customer_type = fields.Selection([
        ('private', 'Particulier'),
        ('professional', 'Professionnel'),
        ('fleet_manager', 'Gestionnaire de flotte'),
        ('leasing_company', 'Société de leasing'),
        ('insurance_company', "Compagnie d'assurance"),
        ('subcontractor', 'Sous-traitant'),
        ('dealer', 'Concessionnaire'),
    ], string="Type client garage")
    is_leasing_company = fields.Boolean(
        string="Société de leasing",
        compute='_compute_is_leasing',
        store=True,
    )
    is_insurance_company = fields.Boolean(
        string="Compagnie d'assurance",
        compute='_compute_is_insurance',
        store=True,
    )
    is_subcontractor = fields.Boolean(
        string="Sous-traitant",
        compute='_compute_is_subcontractor',
        store=True,
    )

    # === VÉHICULES ===
    garage_vehicle_ids = fields.One2many(
        'fleet.vehicle',
        'driver_id',
        string="Véhicules (conducteur)",
        domain=[('active', '=', True)],
    )
    owned_vehicle_ids = fields.One2many(
        'fleet.vehicle',
        'owner_id',
        string="Véhicules possédés",
    )
    vehicle_count = fields.Integer(
        compute='_compute_vehicle_count',
        string="Nombre de véhicules",
    )

    # === ORDRES DE RÉPARATION ===
    repair_order_ids = fields.One2many(
        'garage.repair.order',
        'customer_id',
        string="Ordres de réparation",
    )
    repair_order_count = fields.Integer(
        compute='_compute_ro_count',
    )

    # === FACTURATION GARAGE ===
    garage_payment_term_id = fields.Many2one(
        'account.payment.term',
        string="Conditions de paiement garage",
        help="Conditions spécifiques pour les travaux garage",
    )
    garage_credit_limit = fields.Monetary(
        string="Plafond crédit garage",
        currency_field='currency_id',
        help="Montant maximum d'encours autorisé pour ce client",
    )
    garage_discount_rate = fields.Float(
        string="Remise garage (%)",
        help="Remise commerciale automatiquement appliquée sur les devis garage",
    )
    garage_price_list = fields.Selection([
        ('standard', 'Tarif standard'),
        ('fleet', 'Tarif flotte'),
        ('vip', 'Tarif VIP'),
        ('insurance', 'Tarif agréé assurance'),
    ], string="Grille tarifaire", default='standard')

    # === PRÉFÉRENCES ===
    preferred_language = fields.Selection([
        ('fr', 'Français'),
        ('nl', 'Néerlandais'),
        ('en', 'Anglais'),
        ('de', 'Allemand'),
    ], string="Langue de communication", default='fr')
    preferred_contact_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone', 'Téléphone'),
        ('portal', 'Portail en ligne'),
    ], string="Moyen de contact préféré", default='email')
    receive_maintenance_alerts = fields.Boolean(
        string="Recevoir alertes entretien",
        default=True,
    )
    receive_ct_alerts = fields.Boolean(
        string="Recevoir alertes CT",
        default=True,
    )

    # === FLOTTE (si gestionnaire de flotte) ===
    fleet_contact_ids = fields.One2many(
        'res.partner',
        'fleet_manager_id',
        string="Conducteurs de la flotte",
    )
    fleet_manager_id = fields.Many2one(
        'res.partner',
        string="Gestionnaire de flotte",
        domain="[('garage_customer_type', '=', 'fleet_manager')]",
        help="Le gestionnaire qui autorise les travaux pour ce conducteur",
    )
    fleet_approval_required = fields.Boolean(
        string="Approbation flotte requise",
        help="Si coché, les devis au-dessus du seuil nécessitent validation du gestionnaire",
    )
    fleet_approval_threshold = fields.Monetary(
        string="Seuil approbation (€)",
        currency_field='currency_id',
        help="Montant au-dessus duquel le gestionnaire doit approuver",
    )

    # === FACTURATION GARAGE — COMPUTE ===
    total_invoiced_garage = fields.Monetary(
        string="Total facturé garage",
        compute='_compute_garage_invoice_stats',
        currency_field='currency_id',
    )
    outstanding_garage_balance = fields.Monetary(
        string="Encours garage",
        compute='_compute_garage_invoice_stats',
        currency_field='currency_id',
    )
    last_visit_date = fields.Date(
        string="Dernière visite",
        compute='_compute_last_visit_date',
    )
    garage_invoice_count = fields.Integer(
        string="Nombre factures garage",
        compute='_compute_garage_invoice_stats',
    )

    # === CONTENTIEUX ===
    is_blocked_garage = fields.Boolean(
        string="Bloqué (garage)",
        help="Si coché, aucun nouveau devis/OR ne peut être créé pour ce client",
        tracking=True,
    )
    blocked_reason = fields.Text(string="Raison du blocage")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('garage_customer_type')
    def _compute_is_leasing(self):
        for rec in self:
            rec.is_leasing_company = rec.garage_customer_type == 'leasing_company'

    @api.depends('garage_customer_type')
    def _compute_is_insurance(self):
        for rec in self:
            rec.is_insurance_company = rec.garage_customer_type == 'insurance_company'

    @api.depends('garage_customer_type')
    def _compute_is_subcontractor(self):
        for rec in self:
            rec.is_subcontractor = rec.garage_customer_type == 'subcontractor'

    def _compute_vehicle_count(self):
        for rec in self:
            rec.vehicle_count = self.env['fleet.vehicle'].search_count([
                '|',
                ('driver_id', '=', rec.id),
                ('owner_id', '=', rec.id),
            ])

    def _compute_ro_count(self):
        for rec in self:
            rec.repair_order_count = self.env['garage.repair.order'].search_count([
                ('customer_id', '=', rec.id),
            ])

    def _compute_garage_invoice_stats(self):
        AccountMove = self.env['account.move']
        for rec in self:
            invoices = AccountMove.search([
                ('partner_id', '=', rec.id),
                ('is_garage_invoice', '=', True),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ])
            rec.garage_invoice_count = len(invoices)
            rec.total_invoiced_garage = sum(invoices.mapped('amount_total'))
            rec.outstanding_garage_balance = sum(
                invoices.mapped('amount_residual')
            )

    def _compute_last_visit_date(self):
        RepairOrder = self.env['garage.repair.order']
        for rec in self:
            last_ro = RepairOrder.search([
                ('customer_id', '=', rec.id),
                ('state', '=', 'delivered'),
                ('actual_end_date', '!=', False),
            ], order='actual_end_date desc', limit=1)
            rec.last_visit_date = (
                last_ro.actual_end_date.date() if last_ro else False
            )

    # ------------------------------------------------------------------
    # Contraintes
    # ------------------------------------------------------------------

    @api.constrains('is_blocked_garage', 'blocked_reason')
    def _check_blocked_with_reason(self):
        for rec in self:
            if rec.is_blocked_garage and not rec.blocked_reason:
                raise ValidationError(
                    "Veuillez indiquer la raison du blocage."
                )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_repair_orders(self):
        """Ouvre la liste des OR liés à ce partenaire."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordres de réparation',
            'res_model': 'garage.repair.order',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
        }

    def action_view_vehicles(self):
        """Ouvre la liste des véhicules liés à ce partenaire."""
        self.ensure_one()
        vehicles = self.env['fleet.vehicle'].search([
            '|',
            ('driver_id', '=', self.id),
            ('owner_id', '=', self.id),
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Véhicules',
            'res_model': 'fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', vehicles.ids)],
        }
