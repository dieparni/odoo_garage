"""Consommation de produits peinture par opération."""

from odoo import api, fields, models


class GaragePaintConsumption(models.Model):
    """Ligne de consommation produit peinture."""

    _name = 'garage.paint.consumption'
    _description = 'Consommation produit peinture'

    paint_operation_id = fields.Many2one(
        'garage.paint.operation',
        ondelete='cascade',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string="Produit",
        required=True,
        domain="[('categ_id.name', 'ilike', 'peinture')]",
    )
    product_type = fields.Selection([
        ('base', 'Base colorée'),
        ('clear', 'Vernis'),
        ('hardener', 'Durcisseur'),
        ('thinner', 'Diluant'),
        ('primer', 'Apprêt'),
        ('filler', 'Mastic'),
        ('other', 'Autre'),
    ], string="Type produit")

    quantity = fields.Float(string="Quantité consommée")
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unité",
        default=lambda self: self.env.ref('uom.product_uom_litre', False),
    )
    unit_cost = fields.Monetary(
        string="Coût unitaire",
        currency_field='currency_id',
    )
    total_cost = fields.Monetary(
        string="Coût total",
        compute='_compute_cost',
        store=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends('quantity', 'unit_cost')
    def _compute_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.unit_cost
