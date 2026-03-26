"""Suppléments de sinistre assurance."""

from odoo import fields, models


class GarageInsuranceSupplement(models.Model):
    """Demande de supplément sur un sinistre (travaux additionnels)."""

    _name = 'garage.insurance.supplement'
    _description = 'Supplément sinistre'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    claim_id = fields.Many2one(
        'garage.insurance.claim',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(string="Description", required=True)
    amount = fields.Monetary(
        string="Montant supplément",
        currency_field='currency_id',
    )
    reason = fields.Html(string="Justification détaillée")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', "Envoyé à l'expert"),
        ('approved', 'Approuvé'),
        ('rejected', 'Refusé'),
    ], default='draft', tracking=True)
    approved_amount = fields.Monetary(
        string="Montant approuvé",
        currency_field='currency_id',
    )
    expert_response_date = fields.Date(string="Date réponse expert")
    document_ids = fields.Many2many(
        'ir.attachment',
        string="Pièces jointes (photos)",
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    def action_send(self):
        """Brouillon → Envoyé."""
        self.write({'state': 'sent'})

    def action_approve(self):
        """Envoyé → Approuvé."""
        self.write({
            'state': 'approved',
            'expert_response_date': fields.Date.today(),
        })

    def action_reject(self):
        """Envoyé → Refusé."""
        self.write({
            'state': 'rejected',
            'expert_response_date': fields.Date.today(),
        })
