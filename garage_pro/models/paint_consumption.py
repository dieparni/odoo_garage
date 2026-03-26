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
    stock_move_id = fields.Many2one(
        'stock.move',
        string="Mouvement stock",
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends('quantity', 'unit_cost')
    def _compute_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.unit_cost

    def _create_stock_move(self):
        """Crée un mouvement de sortie stock pour la consommation peinture."""
        for rec in self:
            if not rec.product_id or rec.quantity <= 0 or rec.stock_move_id:
                continue
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', rec.paint_operation_id.company_id.id
                  if hasattr(rec.paint_operation_id, 'company_id')
                  else self.env.company.id)],
                limit=1,
            )
            if not warehouse:
                continue
            location_src = warehouse.lot_stock_id
            location_dest = self.env.ref(
                'stock.location_production', raise_if_not_found=False
            ) or warehouse.lot_stock_id
            move_vals = {
                'name': "Conso peinture — %s" % (
                    rec.paint_operation_id.display_name or ''),
                'product_id': rec.product_id.id,
                'product_uom': rec.uom_id.id or rec.product_id.uom_id.id,
                'product_uom_qty': rec.quantity,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'garage_paint_consumption_id': rec.id,
                'company_id': warehouse.company_id.id,
            }
            move = self.env['stock.move'].create(move_vals)
            move._action_confirm()
            move._action_assign()
            move.quantity = rec.quantity
            move.picked = True
            move._action_done()
            rec.stock_move_id = move.id

    @api.model_create_multi
    def create(self, vals_list):
        """Crée les enregistrements puis les mouvements stock associés."""
        records = super().create(vals_list)
        records._create_stock_move()
        return records
