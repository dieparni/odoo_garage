"""Extension hr.employee — compétences technicien atelier."""

from odoo import fields, models


class HrEmployee(models.Model):
    """Ajout des compétences garage sur les employés."""

    _inherit = 'hr.employee'

    is_garage_technician = fields.Boolean(string="Technicien atelier")
    garage_skill = fields.Selection([
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
        currency_field='garage_currency_id',
        help="Coût interne (pour calcul de marge, pas le taux facturé)",
    )
    daily_capacity_hours = fields.Float(
        string="Capacité journalière (h)",
        default=8.0,
    )
    garage_currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        string="Devise garage",
    )
    planning_slot_ids = fields.One2many(
        'garage.planning.slot',
        'technician_id',
        string="Créneaux planifiés",
    )
