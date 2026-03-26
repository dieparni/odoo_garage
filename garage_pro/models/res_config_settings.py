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

    # === Taux horaires ===
    garage_default_hourly_rate_body = fields.Float(
        string="Taux horaire carrosserie (€/h)",
        config_parameter='garage_pro.default_hourly_rate_body',
        default=55.0,
    )
    garage_default_hourly_rate_paint = fields.Float(
        string="Taux horaire peinture (€/h)",
        config_parameter='garage_pro.default_hourly_rate_paint',
        default=55.0,
    )
    garage_default_hourly_rate_mech = fields.Float(
        string="Taux horaire mécanique (€/h)",
        config_parameter='garage_pro.default_hourly_rate_mech',
        default=60.0,
    )

    # === Devis ===
    garage_quotation_validity_days = fields.Integer(
        string="Validité devis (jours)",
        config_parameter='garage_pro.quotation_validity_days',
        default=30,
        help="Nombre de jours de validité par défaut pour les devis",
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
