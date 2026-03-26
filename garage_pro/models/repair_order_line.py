"""Lignes d'ordre de réparation."""

from odoo import api, fields, models

from .constants import DAMAGE_ZONES


class GarageRepairOrderLine(models.Model):
    """Ligne d'OR — identique à la ligne de devis avec suivi d'exécution."""

    _name = 'garage.repair.order.line'
    _description = "Ligne d'ordre de réparation"
    _order = 'sequence, id'

    repair_order_id = fields.Many2one(
        'garage.repair.order',
        ondelete='cascade',
        required=True,
    )
    sequence = fields.Integer(default=10)

    name = fields.Char(string="Description", required=True)
    description = fields.Text(string="Description détaillée")

    line_type = fields.Selection([
        ('labor_body', "Main d'œuvre carrosserie"),
        ('labor_paint', "Main d'œuvre peinture"),
        ('labor_mech', "Main d'œuvre mécanique"),
        ('parts', 'Pièces détachées'),
        ('paint_material', 'Matière peinture'),
        ('subcontract', 'Sous-traitance'),
        ('consumable', 'Consommables'),
        ('misc', 'Divers'),
    ], string="Type de ligne", required=True)

    # === PRODUIT ===
    product_id = fields.Many2one(
        'product.product',
        string="Produit/Pièce",
    )
    product_category = fields.Selection([
        ('oem', 'Pièce OEM (constructeur)'),
        ('aftermarket', 'Pièce aftermarket'),
        ('used', "Pièce d'occasion"),
        ('exchange', 'Échange standard'),
    ], string="Catégorie pièce")

    # === QUANTITÉ & PRIX ===
    quantity = fields.Float(string="Quantité", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unité")
    unit_price = fields.Monetary(
        string="Prix unitaire",
        currency_field='currency_id',
    )
    discount = fields.Float(string="Remise (%)")
    amount_total = fields.Monetary(
        string="Total ligne",
        compute='_compute_total',
        store=True,
        currency_field='currency_id',
    )

    # === MAIN D'ŒUVRE ===
    allocated_time = fields.Float(
        string="Temps alloué (heures)",
    )
    hourly_rate = fields.Monetary(
        string="Taux horaire",
        currency_field='currency_id',
    )

    # === TECHNICIEN ===
    technician_id = fields.Many2one(
        'hr.employee',
        string="Technicien",
        domain="[('is_garage_technician', '=', True)]",
    )

    # === EXÉCUTION ===
    actual_time = fields.Float(
        string="Temps réel passé (heures)",
        help="Temps réellement passé par le technicien",
    )
    is_done = fields.Boolean(string="Terminé", default=False)
    done_date = fields.Datetime(string="Date fin")

    # === ZONE CARROSSERIE ===
    damage_zone = fields.Selection(
        DAMAGE_ZONES,
        string="Zone endommagée",
    )

    damage_level = fields.Selection([
        ('light', 'Léger (retouche/débosselage)'),
        ('medium', 'Moyen (redressage)'),
        ('heavy', 'Grave (remplacement partiel)'),
        ('replace', 'Remplacement complet'),
    ], string="Niveau de dommage")

    # === STOCK ===
    stock_move_ids = fields.One2many(
        'stock.move',
        'garage_ro_line_id',
        string="Mouvements stock",
    )
    parts_received = fields.Boolean(
        string="Pièces reçues",
        compute='_compute_parts_received',
        store=True,
    )

    # === COÛT ===
    cost_price = fields.Monetary(
        string="Coût unitaire",
        currency_field='currency_id',
        help="Coût d'achat ou coût horaire technicien",
    )
    cost_total = fields.Monetary(
        string="Coût total",
        compute='_compute_cost_total',
        store=True,
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(related='repair_order_id.currency_id')

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('quantity', 'unit_price', 'discount', 'allocated_time',
                 'hourly_rate', 'line_type')
    def _compute_total(self):
        labor_types = ('labor_body', 'labor_paint', 'labor_mech')
        for line in self:
            if (line.line_type in labor_types
                    and line.allocated_time and line.hourly_rate):
                subtotal = line.allocated_time * line.hourly_rate
            else:
                subtotal = line.quantity * line.unit_price
            line.amount_total = subtotal * (1 - (line.discount / 100.0))

    @api.depends('stock_move_ids.state')
    def _compute_parts_received(self):
        for line in self:
            moves = line.stock_move_ids
            if moves:
                line.parts_received = all(m.state == 'done' for m in moves)
            else:
                # Pas de mouvement stock = pas en attente de pièces
                line.parts_received = True

    @api.depends('quantity', 'cost_price', 'allocated_time', 'line_type')
    def _compute_cost_total(self):
        labor_types = ('labor_body', 'labor_paint', 'labor_mech')
        for line in self:
            if line.line_type in labor_types and line.allocated_time:
                line.cost_total = line.allocated_time * line.cost_price
            else:
                line.cost_total = line.quantity * line.cost_price
