"""Devis garage — objet commercial avant conversion en OR."""

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class GarageQuotation(models.Model):
    """Devis garage multi-ligne avec workflow et conversion en OR."""

    _name = 'garage.quotation'
    _description = 'Devis garage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Référence",
        default='Nouveau',
        readonly=True,
        copy=False,
    )

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
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Véhicule",
        required=True,
        tracking=True,
    )
    customer_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        tracking=True,
        domain="[('is_garage_customer', '=', True)]",
    )
    invoice_partner_id = fields.Many2one(
        'res.partner',
        string="Adresse de facturation",
        help="Si différent du client (ex: société de leasing, employeur)",
    )
    claim_id = fields.Many2one(
        'garage.insurance.claim',
        string="Sinistre",
        domain="[('vehicle_id', '=', vehicle_id), "
               "('state', 'not in', ['cancelled', 'paid'])]",
    )
    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        readonly=True,
        copy=False,
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
    line_ids = fields.One2many(
        'garage.quotation.line',
        'quotation_id',
        string="Lignes de devis",
    )

    # === MONTANTS ===
    amount_labor = fields.Monetary(
        string="Total main d'œuvre",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_parts = fields.Monetary(
        string="Total pièces",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_subcontract = fields.Monetary(
        string="Total sous-traitance",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_paint_material = fields.Monetary(
        string="Total matière peinture",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_untaxed = fields.Monetary(
        string="Total HT",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_tax = fields.Monetary(
        string="TVA",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_total = fields.Monetary(
        string="Total TTC",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )

    # === ASSURANCE (si sinistre) ===
    is_insurance_claim = fields.Boolean(
        compute='_compute_is_insurance',
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
    date_quotation = fields.Date(
        string="Date du devis",
        default=fields.Date.today,
    )
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
    customer_notes = fields.Html(
        string="Notes client (imprimées sur le devis)",
    )

    # === TECHNIQUE ===
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    user_id = fields.Many2one(
        'res.users',
        string="Responsable",
        default=lambda self: self.env.user,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('line_ids.amount_total', 'line_ids.line_type',
                 'global_discount_rate')
    def _compute_amounts(self):
        labor_types = ('labor_body', 'labor_paint', 'labor_mech')
        for rec in self:
            lines = rec.line_ids
            rec.amount_labor = sum(
                l.amount_total for l in lines if l.line_type in labor_types
            )
            rec.amount_parts = sum(
                l.amount_total for l in lines if l.line_type == 'parts'
            )
            rec.amount_subcontract = sum(
                l.amount_total for l in lines if l.line_type == 'subcontract'
            )
            rec.amount_paint_material = sum(
                l.amount_total for l in lines
                if l.line_type == 'paint_material'
            )
            subtotal = sum(l.amount_total for l in lines)
            discount = (
                subtotal * (rec.global_discount_rate / 100.0)
                if rec.global_discount_rate else 0
            )
            rec.global_discount_amount = discount
            rec.amount_untaxed = subtotal - discount
            # TVA 21% Belgique — à rendre configurable via ir.config_parameter
            rec.amount_tax = rec.amount_untaxed * 0.21
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    @api.depends('claim_id')
    def _compute_is_insurance(self):
        for rec in self:
            rec.is_insurance_claim = bool(rec.claim_id)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'garage.quotation'
                ) or 'Nouveau'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_send(self):
        """Brouillon → Envoyé."""
        self.write({
            'state': 'sent',
            'date_sent': fields.Datetime.now(),
        })

    def action_approve(self):
        """Envoyé → Accepté."""
        self.write({
            'state': 'approved',
            'date_approved': fields.Datetime.now(),
        })

    def action_refuse(self):
        """Envoyé → Refusé."""
        self.write({
            'state': 'refused',
            'date_refused': fields.Datetime.now(),
        })

    def action_convert_to_repair_order(self):
        """Accepté → Converti en OR. Crée l'OR avec toutes les lignes."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(
                "Le devis doit être accepté avant conversion."
            )
        if self.customer_id.is_blocked_garage:
            raise UserError(
                "Ce client est bloqué. Raison : %s"
                % self.customer_id.blocked_reason
            )

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle_id.id,
            'customer_id': self.customer_id.id,
            'invoice_partner_id': (
                self.invoice_partner_id.id or self.customer_id.id
            ),
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
                'uom_id': line.uom_id.id if line.uom_id else False,
                'unit_price': line.unit_price,
                'discount': line.discount,
                'allocated_time': line.allocated_time,
                'hourly_rate': line.hourly_rate,
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
        """Créer un avenant/supplément lié à ce devis."""
        self.ensure_one()
        supplement = self.copy({
            'name': 'Nouveau',
            'state': 'draft',
            'is_supplement': True,
            'parent_quotation_id': self.id,
            'line_ids': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'garage.quotation',
            'res_id': supplement.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        """Annuler le devis."""
        self.write({'state': 'cancelled'})
