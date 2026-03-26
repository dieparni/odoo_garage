"""Système de peinture (fabricant)."""

from odoo import fields, models


class GaragePaintSystem(models.Model):
    """Fabricant de peinture utilisé par l'atelier (Standox, Sikkens, PPG...)."""

    _name = 'garage.paint.system'
    _description = 'Système de peinture (fabricant)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string="Nom", required=True, tracking=True)
    code = fields.Char(string="Code")
    supplier_id = fields.Many2one('res.partner', string="Fournisseur")
    active = fields.Boolean(default=True)
