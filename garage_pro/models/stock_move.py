"""Extension stock.move — lien vers les lignes d'OR garage."""

from odoo import fields, models


class StockMove(models.Model):
    """Extension stock.move pour traçabilité pièces garage."""

    _inherit = 'stock.move'

    garage_ro_line_id = fields.Many2one(
        'garage.repair.order.line',
        string="Ligne OR garage",
        index=True,
    )
    garage_paint_consumption_id = fields.Many2one(
        'garage.paint.consumption',
        string="Consommation peinture",
        index=True,
    )
