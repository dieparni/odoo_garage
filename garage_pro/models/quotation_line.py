"""Lignes de devis garage."""

from odoo import api, fields, models


class GarageQuotationLine(models.Model):
    """Ligne de devis — MO, pièces, sous-traitance, matière peinture."""

    _name = 'garage.quotation.line'
    _description = 'Ligne de devis garage'
    _order = 'sequence, id'

    quotation_id = fields.Many2one(
        'garage.quotation',
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

    # === PRODUIT (optionnel, pour les pièces) ===
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
        help="Temps barème alloué pour cette opération",
    )
    hourly_rate = fields.Monetary(
        string="Taux horaire",
        currency_field='currency_id',
    )

    # === RÉFÉRENCE BARÈME ===
    bareme_code = fields.Char(
        string="Code opération barème",
        help="Référence Audatex/DAT/GT Motive",
    )
    bareme_source = fields.Selection([
        ('audatex', 'Audatex'),
        ('dat', 'DAT'),
        ('gt_motive', 'GT Motive'),
        ('manual', 'Manuel'),
    ], string="Source barème", default='manual')

    # === ZONE CARROSSERIE ===
    damage_zone = fields.Selection([
        ('front_bumper', 'Pare-chocs avant'),
        ('rear_bumper', 'Pare-chocs arrière'),
        ('hood', 'Capot'),
        ('trunk', 'Coffre'),
        ('roof', 'Toit'),
        ('fender_fl', 'Aile avant gauche'),
        ('fender_fr', 'Aile avant droite'),
        ('fender_rl', 'Aile arrière gauche'),
        ('fender_rr', 'Aile arrière droite'),
        ('door_fl', 'Porte avant gauche'),
        ('door_fr', 'Porte avant droite'),
        ('door_rl', 'Porte arrière gauche'),
        ('door_rr', 'Porte arrière droite'),
        ('sill_l', 'Bas de caisse gauche'),
        ('sill_r', 'Bas de caisse droit'),
        ('windshield', 'Pare-brise'),
        ('rear_window', 'Lunette arrière'),
        ('side_window_l', 'Vitre latérale gauche'),
        ('side_window_r', 'Vitre latérale droite'),
        ('mirror_l', 'Rétroviseur gauche'),
        ('mirror_r', 'Rétroviseur droit'),
        ('other', 'Autre'),
    ], string="Zone endommagée")

    damage_level = fields.Selection([
        ('light', 'Léger (retouche/débosselage)'),
        ('medium', 'Moyen (redressage)'),
        ('heavy', 'Grave (remplacement partiel)'),
        ('replace', 'Remplacement complet'),
    ], string="Niveau de dommage")

    currency_id = fields.Many2one(related='quotation_id.currency_id')

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

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------

    @api.onchange('line_type')
    def _onchange_line_type(self):
        """Pré-remplir le taux horaire selon le type de MO."""
        labor_types = ('labor_body', 'labor_paint', 'labor_mech')
        if self.line_type in labor_types:
            claim = self.quotation_id.claim_id
            if claim and claim.insurance_company_id:
                ins = claim.insurance_company_id
                rates = {
                    'labor_body': ins.hourly_rate_bodywork,
                    'labor_paint': ins.hourly_rate_paint,
                    'labor_mech': ins.hourly_rate_mechanic,
                }
                self.hourly_rate = rates.get(self.line_type, 0)
            else:
                params = self.env['ir.config_parameter'].sudo()
                defaults = {
                    'labor_body': float(params.get_param(
                        'garage_pro.default_hourly_rate_body', 55)),
                    'labor_paint': float(params.get_param(
                        'garage_pro.default_hourly_rate_paint', 55)),
                    'labor_mech': float(params.get_param(
                        'garage_pro.default_hourly_rate_mech', 60)),
                }
                self.hourly_rate = defaults.get(self.line_type, 55)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.unit_price = self.product_id.lst_price
            self.uom_id = self.product_id.uom_id
