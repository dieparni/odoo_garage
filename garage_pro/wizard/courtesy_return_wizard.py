"""Wizard de restitution de véhicule de courtoisie."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class CourtesyReturnWizard(models.TransientModel):
    """Wizard pour documenter la restitution d'un véhicule de courtoisie."""

    _name = 'garage.courtesy.return.wizard'
    _description = 'Wizard restitution courtoisie'

    loan_id = fields.Many2one(
        'garage.courtesy.loan',
        string="Prêt",
        required=True,
        readonly=True,
    )
    courtesy_vehicle_id = fields.Many2one(
        related='loan_id.courtesy_vehicle_id',
        string="Véhicule",
    )
    customer_id = fields.Many2one(
        related='loan_id.customer_id',
        string="Client",
    )

    # === RETOUR ===
    km_end = fields.Integer(string="Km retour", required=True)
    fuel_level_end = fields.Selection([
        ('full', 'Plein'),
        ('3_4', '3/4'),
        ('1_2', '1/2'),
        ('1_4', '1/4'),
        ('empty', 'Vide'),
    ], string="Niveau carburant retour", required=True)
    condition_end = fields.Html(
        string="État des lieux retour",
        help="Décrire l'état général du véhicule au retour",
    )
    has_damage = fields.Boolean(string="Dommage constaté")
    damage_description = fields.Text(string="Description du dommage")

    @api.model
    def default_get(self, fields_list):
        """Pré-remplit le wizard avec le prêt actif."""
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and 'loan_id' in fields_list:
            loan = self.env['garage.courtesy.loan'].browse(active_id)
            if loan.state != 'active':
                raise UserError("Ce prêt n'est pas en cours.")
            res['loan_id'] = loan.id
        return res

    def action_confirm_return(self):
        """Confirmer la restitution du véhicule de courtoisie."""
        self.ensure_one()
        loan = self.loan_id
        if loan.state != 'active':
            raise UserError("Ce prêt n'est pas en cours.")

        loan.write({
            'km_end': self.km_end,
            'fuel_level_end': self.fuel_level_end,
            'condition_end': self.condition_end,
            'has_damage': self.has_damage,
            'damage_description': self.damage_description,
        })
        loan.action_return()
        return {'type': 'ir.actions.act_window_close'}
