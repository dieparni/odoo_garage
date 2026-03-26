"""Experts automobiles liés aux compagnies d'assurance."""

from odoo import fields, models


class GarageInsuranceExpert(models.Model):
    """Expert automobile mandaté par une compagnie d'assurance."""

    _name = 'garage.insurance.expert'
    _description = 'Expert automobile'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string="Nom", required=True)
    company_id = fields.Many2one(
        'garage.insurance.company',
        string="Compagnie d'assurance",
    )
    partner_id = fields.Many2one('res.partner', string="Contact")
    phone = fields.Char(string="Téléphone")
    email = fields.Char(string="Email")
    expertise_type = fields.Selection([
        ('on_site', 'Sur place (se déplace)'),
        ('remote', 'Expertise à distance (photo/vidéo)'),
        ('both', 'Les deux'),
    ], string="Type d'expertise", default='on_site')
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")
