"""Extension des paramètres système pour la configuration Garage Pro."""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Ajoute les paramètres Garage dans Configuration > Garage."""

    _inherit = 'res.config.settings'

    # === TVA ===
    garage_default_vat_rate = fields.Float(
        string="Taux TVA par défaut (%)",
        config_parameter='garage_pro.default_vat_rate',
        default=21.0,
        help="Taux de TVA appliqué sur les devis et OR (ex: 21 pour la Belgique)",
    )

    # === CarVertical ===
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
