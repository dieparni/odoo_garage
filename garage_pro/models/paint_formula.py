"""Formule teinte peinture — composition mesurée par spectrophotomètre."""

from odoo import fields, models


class GaragePaintFormula(models.Model):
    """Formule de teinte peinture pour un véhicule/code couleur."""

    _name = 'garage.paint.formula'
    _description = 'Formule teinte peinture'
    _order = 'paint_code, variant_name'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule")
    paint_system_id = fields.Many2one(
        'garage.paint.system',
        string="Système",
        required=True,
    )
    paint_code = fields.Char(string="Code constructeur", required=True)
    formula_reference = fields.Char(string="Référence formule système")
    formula_detail = fields.Text(
        string="Détail formule",
        help="Composition de la formule (bases, quantités). "
             "Copié depuis le spectrophotomètre.",
    )
    variant_name = fields.Char(
        string="Variante",
        help="Certaines teintes ont des variantes (1K, 2K, effet nacré…)",
    )
    spectro_date = fields.Date(string="Date spectrophotomètre")
    spectro_result = fields.Binary(string="Fichier spectro")
    notes = fields.Text(string="Notes (ajustements, remarques)")
    active = fields.Boolean(default=True)
