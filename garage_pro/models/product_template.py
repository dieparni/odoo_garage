"""Extension product.template — champs pièces garage."""

from odoo import fields, models


class ProductTemplate(models.Model):
    """Ajout des champs garage sur les produits."""

    _inherit = 'product.template'

    is_garage_part = fields.Boolean(string="Pièce garage")
    garage_part_category = fields.Selection([
        ('oem', 'OEM (constructeur)'),
        ('aftermarket', 'Aftermarket (équipementier)'),
        ('used', 'Occasion'),
        ('exchange', 'Échange standard'),
        ('consumable', 'Consommable atelier'),
        ('paint', 'Produit peinture'),
    ], string="Catégorie garage")
    oem_reference = fields.Char(string="Référence OEM constructeur")
    tecdoc_reference = fields.Char(string="Référence TecDoc")
    compatible_vehicle_models = fields.Char(
        string="Véhicules compatibles",
        help="Marques/modèles compatibles (texte libre ou via TecDoc)",
    )
    is_consignment = fields.Boolean(
        string="Pièce consignée",
        help="Échange standard avec consigne (turbo, injecteur, démarreur…)",
    )
    consignment_amount = fields.Monetary(
        string="Montant consigne",
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
