"""Wizard de demande de supplément sur sinistre."""

from odoo import fields, models
from odoo.exceptions import UserError


class GarageInsuranceSupplementWizard(models.TransientModel):
    """Wizard pour créer un supplément sur un sinistre existant."""

    _name = 'garage.insurance.supplement.wizard'
    _description = 'Wizard supplément sinistre'

    claim_id = fields.Many2one(
        'garage.insurance.claim',
        string="Sinistre",
        required=True,
        readonly=True,
    )
    name = fields.Char(
        string="Description du supplément",
        required=True,
    )
    amount = fields.Monetary(
        string="Montant demandé",
        currency_field='currency_id',
        required=True,
    )
    reason = fields.Html(
        string="Justification détaillée",
        help="Expliquez pourquoi des travaux supplémentaires sont nécessaires",
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    def action_confirm(self):
        """Crée le supplément et passe le sinistre en 'supplement_pending'."""
        self.ensure_one()
        if self.amount <= 0:
            raise UserError("Le montant du supplément doit être positif.")

        supplement = self.env['garage.insurance.supplement'].create({
            'claim_id': self.claim_id.id,
            'name': self.name,
            'amount': self.amount,
            'reason': self.reason,
        })
        # Passer le supplément en "envoyé"
        supplement.action_send()
        # Mettre le sinistre en attente de supplément
        self.claim_id.write({'state': 'supplement_pending'})

        return {'type': 'ir.actions.act_window_close'}
