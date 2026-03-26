"""Véhicule de courtoisie — flotte de prêt pour les clients."""

from odoo import fields, models


class GarageCourtesyVehicle(models.Model):
    """Véhicule de courtoisie disponible pour le prêt client."""

    _name = 'garage.courtesy.vehicle'
    _description = 'Véhicule de courtoisie'
    _inherit = ['mail.thread']
    _order = 'name'

    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Véhicule",
        required=True,
    )
    name = fields.Char(
        related='vehicle_id.license_plate',
        store=True,
        string="Immatriculation",
    )

    state = fields.Selection([
        ('available', 'Disponible'),
        ('loaned', 'En prêt'),
        ('maintenance', 'En maintenance'),
        ('unavailable', 'Indisponible'),
    ], default='available', tracking=True, string="Statut")

    insurance_expiry = fields.Date(string="Échéance assurance")
    ct_expiry = fields.Date(string="Échéance CT")
    current_loan_id = fields.Many2one(
        'garage.courtesy.loan',
        string="Prêt en cours",
    )
    loan_ids = fields.One2many(
        'garage.courtesy.loan',
        'courtesy_vehicle_id',
        string="Historique prêts",
    )
    loan_count = fields.Integer(
        compute='_compute_loan_count',
    )
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
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    notes = fields.Text(string="Notes")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def _compute_loan_count(self):
        for rec in self:
            rec.loan_count = len(rec.loan_ids)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_loans(self):
        """Ouvre l'historique des prêts pour ce véhicule."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prêts',
            'res_model': 'garage.courtesy.loan',
            'view_mode': 'tree,form',
            'domain': [('courtesy_vehicle_id', '=', self.id)],
        }
