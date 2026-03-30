"""Cache des résultats CarVertical pour éviter les appels API redondants."""

from odoo import api, fields, models


class CarVerticalCache(models.Model):
    """Stocke les réponses brutes CarVertical par VIN avec expiration configurable."""

    _name = 'garage.carvertical.cache'
    _description = 'Cache résultats CarVertical'
    _order = 'lookup_date desc'

    vin = fields.Char(string="VIN", required=True, index=True)
    lookup_date = fields.Datetime(
        string="Date recherche",
        default=fields.Datetime.now,
    )
    raw_response = fields.Text(string="Réponse brute (JSON)")
    is_expired = fields.Boolean(
        string="Expiré",
        compute='_compute_expired',
    )

    _vin_unique = models.Constraint(
        'UNIQUE(vin)',
        'Un seul cache par VIN.',
    )

    @api.depends('lookup_date')
    def _compute_expired(self):
        """Vérifie si le cache a dépassé la durée configurée."""
        cache_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'garage_pro.carvertical_cache_days', '30'))
        for rec in self:
            if rec.lookup_date:
                delta = fields.Datetime.now() - rec.lookup_date
                rec.is_expired = delta.days > cache_days
            else:
                rec.is_expired = True
