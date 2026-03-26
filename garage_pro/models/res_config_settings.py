"""Extension des paramètres système pour la configuration CarVertical."""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Ajoute les paramètres CarVertical dans Configuration > Garage."""

    _inherit = 'res.config.settings'

    carvertical_api_key = fields.Char(
        string="Clé API CarVertical",
        config_parameter='garage_pro.carvertical_api_key',
    )
    carvertical_auto_lookup = fields.Boolean(
        string="Recherche auto à la création véhicule",
        config_parameter='garage_pro.carvertical_auto_lookup',
        help="Si activé, une recherche CarVertical est lancée automatiquement quand un VIN est saisi",
    )
    carvertical_cache_days = fields.Integer(
        string="Durée cache (jours)",
        config_parameter='garage_pro.carvertical_cache_days',
        default=30,
        help="Nombre de jours pendant lesquels un résultat CarVertical est considéré comme frais",
    )
