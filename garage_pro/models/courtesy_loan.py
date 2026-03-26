"""Prêt de véhicule de courtoisie."""

from odoo import api, fields, models


class GarageCourtesyLoan(models.Model):
    """Prêt de véhicule de courtoisie avec état des lieux."""

    _name = 'garage.courtesy.loan'
    _description = 'Prêt de véhicule de courtoisie'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    courtesy_vehicle_id = fields.Many2one(
        'garage.courtesy.vehicle',
        string="Véhicule de courtoisie",
        required=True,
        domain="[('state', '=', 'available')]",
    )
    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="OR lié",
    )
    customer_id = fields.Many2one(
        'res.partner',
        string="Client emprunteur",
        required=True,
    )

    state = fields.Selection([
        ('reserved', 'Réservé'),
        ('active', 'En cours'),
        ('returned', 'Restitué'),
        ('damaged', 'Restitué avec dommage'),
    ], default='reserved', tracking=True, string="Statut")

    # === DÉPART ===
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
        'ir.attachment',
        'courtesy_start_photo_rel',
        string="Photos départ",
    )
    agreement_signed = fields.Boolean(string="Convention signée")
    agreement_file = fields.Binary(string="Convention signée (fichier)")

    # === RETOUR ===
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
        'ir.attachment',
        'courtesy_end_photo_rel',
        string="Photos retour",
    )
    has_damage = fields.Boolean(string="Dommage constaté au retour")
    damage_description = fields.Text(string="Description dommage")

    # === DURÉE ET FACTURATION ===
    loan_days = fields.Integer(
        string="Jours de prêt",
        compute='_compute_days',
        store=True,
    )
    billable_days = fields.Integer(
        string="Jours facturables",
        compute='_compute_billable_days',
    )
    billable_amount = fields.Monetary(
        string="Montant facturable",
        compute='_compute_billable_amount',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('loan_start', 'loan_end')
    def _compute_days(self):
        for rec in self:
            if rec.loan_start and rec.loan_end:
                delta = rec.loan_end - rec.loan_start
                rec.loan_days = max(delta.days, 1)
            elif rec.loan_start:
                delta = fields.Datetime.now() - rec.loan_start
                rec.loan_days = max(delta.days, 1)
            else:
                rec.loan_days = 0

    def _compute_billable_days(self):
        for rec in self:
            max_free = rec.courtesy_vehicle_id.max_free_days or 0
            rec.billable_days = max(rec.loan_days - max_free, 0)

    def _compute_billable_amount(self):
        for rec in self:
            rate = rec.courtesy_vehicle_id.daily_charge_rate or 0.0
            rec.billable_amount = rec.billable_days * rate

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_activate(self):
        """Réservé → En cours. Active le prêt."""
        self.write({
            'state': 'active',
            'loan_start': fields.Datetime.now(),
        })
        for rec in self:
            rec.courtesy_vehicle_id.write({
                'state': 'loaned',
                'current_loan_id': rec.id,
            })

    def action_return(self):
        """En cours → Restitué (ou avec dommage)."""
        for rec in self:
            state = 'damaged' if rec.has_damage else 'returned'
            rec.write({
                'state': state,
                'loan_end': fields.Datetime.now(),
            })
            rec.courtesy_vehicle_id.write({
                'state': 'available',
                'current_loan_id': False,
            })

    def action_cancel(self):
        """Annuler la réservation."""
        self.write({'state': 'reserved'})
        for rec in self:
            if rec.courtesy_vehicle_id.current_loan_id == rec:
                rec.courtesy_vehicle_id.write({
                    'state': 'available',
                    'current_loan_id': False,
                })
